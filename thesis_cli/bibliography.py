"""Preserve Better BibTeX exports and stable citation keys."""

import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .external import fresh_directory
from .files import atomic_text, write_json
from .literature import normalize_doi


def read_bibliography(text):
    try:
        from pybtex.database import parse_string
    except ImportError as exc:
        raise RuntimeError("文献功能需要可选依赖：pip install 'nju-se-thesis[references]'") from exc
    try:
        data = parse_string(text, "bibtex")
    except Exception as exc:
        raise ValueError("BibTeX 解析失败：" + str(exc)) from exc
    if not data.entries:
        raise ValueError("文献库没有可用条目")
    return [{"citekey": key, "type": item.type, "title": item.fields.get("title"),
             "doi": item.fields.get("doi"), "year": item.fields.get("year") or item.fields.get("date", "")[:4],
             "url": item.fields.get("url"),
             "authors": [" ".join(person.prelast_names + person.last_names) for person in item.persons.get("author", [])]}
            for key, item in data.entries.items()]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sync_bibliography(source, output, existing=None, timeout=30):
    if timeout <= 0:
        raise ValueError("请求超时必须大于 0 秒")
    source = str(source)
    if source.startswith(("http://", "https://")):
        url = urlsplit(source)
        if url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"} or url.username or url.password or not url.path.startswith("/better-bibtex/"):
            raise ValueError("只接受本机 Better BibTeX 导出 URL，或本地 .bib 文件")
        try:
            with build_opener(_NoRedirect()).open(Request(source, headers={"User-Agent": "nju-se-thesis/0.5.0"}), timeout=timeout) as response:
                content = response.read(16 * 1024 * 1024 + 1)
        except OSError as exc:
            raise RuntimeError("无法读取 Better BibTeX；请打开 Zotero 并核对导出 URL：" + str(exc)) from exc
    else:
        source = str(Path(source).resolve())
        content = Path(source).read_bytes()
    if len(content) > 16 * 1024 * 1024:
        raise ValueError("文献库超过 16 MiB")
    text = content.decode("utf-8-sig")
    entries = read_bibliography(text)
    previous = read_bibliography(Path(existing).read_text(encoding="utf-8-sig")) if existing else []
    errors, doi_keys, mapping = [], {}, {}
    key_dois = {}
    for item in entries:
        key = item["citekey"]
        if not re.fullmatch(r"[A-Za-z0-9:._/-]+", key):
            errors.append({"citekey": key, "reason": "当前飞书转 TeX 入口不支持该引用键；保留原键，未自动改写"})
        if item.get("url"):
            mapping[item["url"]] = {"bibkey": key}
        if not item.get("doi"):
            continue
        try:
            doi = normalize_doi(item["doi"])
        except ValueError as exc:
            errors.append({"citekey": key, "reason": str(exc)})
            continue
        if doi in doi_keys and doi_keys[doi] != key:
            errors.append({"doi": doi, "reason": "同一 DOI 对应多个引用键", "keys": [doi_keys[doi], key]})
        doi_keys[doi] = key
        key_dois[key] = doi
        for value in (doi, "https://doi.org/" + doi, "http://doi.org/" + doi):
            mapping[value] = {"bibkey": key}
    for old in previous:
        if old.get("doi"):
            try:
                doi = normalize_doi(old["doi"])
            except ValueError:
                continue
            if doi in doi_keys and doi_keys[doi] != old["citekey"]:
                errors.append({"doi": doi, "reason": "已有引用键发生变化", "previous": old["citekey"], "incoming": doi_keys[doi]})
            if old["citekey"] in key_dois and key_dois[old["citekey"]] != doi:
                errors.append({"citekey": old["citekey"], "reason": "已有引用键对应的 DOI 发生变化", "previous": doi, "incoming": key_dois[old["citekey"]]})
    output = fresh_directory(output)
    atomic_text(output, "source.bib", text, overwrite=False)
    result = {"ok": not errors, "source": source, "sha256": hashlib.sha256(content).hexdigest(),
              "count": len(entries), "entries": entries, "errors": errors, "doi_to_citekey": doi_keys,
              "bibliography": str(output / "references.bib") if not errors else None}
    if not errors:
        # Preserve author formatting and fields: do not serialize through the parser.
        atomic_text(output, "references.bib", text, overwrite=False)
        write_json(output, "citation-assets.json", mapping, overwrite=False)
    write_json(output, "bibliography.json", result)
    return result
