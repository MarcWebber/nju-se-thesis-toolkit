"""Read public OpenAlex and Crossref records; retain raw responses."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .external import fresh_directory
from .files import write_json


def normalize_doi(value):
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", str(value).strip(), flags=re.I).lower()
    if not re.fullmatch(r"10\.\d{4,9}/[^\s]+", value):
        raise ValueError("无效 DOI：" + value)
    return value


def fetch_json(url, timeout=30, headers=None):
    if timeout <= 0:
        raise ValueError("请求超时必须大于 0 秒")
    request = Request(url, headers={"User-Agent": "nju-se-thesis/0.5.0", "Accept": "application/json", **(headers or {})})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout) as response:
                content = response.read(16 * 1024 * 1024 + 1)
            if len(content) > 16 * 1024 * 1024:
                raise ValueError("接口响应超过 16 MiB")
            return json.loads(content)
        except HTTPError as exc:
            if exc.code in (429, 502, 503, 504) and attempt < 2:
                delay = exc.headers.get("Retry-After", "")
                time.sleep(min(float(delay) if delay.isdigit() else 2 ** attempt, 10))
                continue
            raise RuntimeError("公开元数据接口 HTTP " + str(exc.code)) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("元数据接口连接或响应失败：" + str(exc)) from exc


def search_literature(query, output, limit=10, year=None, cites=None, references=None, timeout=30):
    if not 1 <= limit <= 100:
        raise ValueError("limit 必须为 1–100")
    if not (query or cites or references):
        raise ValueError("请提供检索词、--cites 或 --references")
    if year and not re.fullmatch(r"\d{4}(?:-\d{4})?", year):
        raise ValueError("年份使用 YYYY 或 YYYY-YYYY")
    if references and (query or year):
        raise ValueError("参考文献展开不与关键词或年份筛选组合")
    output = fresh_directory(output)
    headers = {"Authorization": "Bearer " + os.environ["OPENALEX_API_KEY"]} if os.environ.get("OPENALEX_API_KEY") else {}
    requests = []

    def get(path, params=None):
        url = "https://api.openalex.org/" + path + ("?" + urlencode(params) if params else "")
        data = fetch_json(url, timeout, headers)
        raw = "raw-" + str(len(requests) + 1) + ".json"
        write_json(output, raw, data)
        requests.append({"url": url, "raw": raw, "retrieved_at": datetime.now(timezone.utc).isoformat()})
        return data

    seed = None
    if cites or references:
        value = cites or references
        if re.fullmatch(r"(?:https://openalex\.org/)?W\d+", value):
            seed = get("works/" + value.rsplit("/", 1)[-1])
        else:
            found = get("works", {"filter": "doi:https://doi.org/" + normalize_doi(value), "per_page": 1})["results"]
            if not found:
                raise ValueError("OpenAlex 没有找到这条 DOI")
            seed = found[0]
    if references:
        records = [get("works/" + value.rsplit("/", 1)[-1]) for value in seed.get("referenced_works", [])[:limit]]
        total = len(seed.get("referenced_works", []))
    else:
        params = {"per_page": limit}
        filters = []
        if query:
            params["search"] = query
        if year:
            filters.append("publication_year:" + year)
        if cites:
            filters.append("cites:" + seed["id"].rsplit("/", 1)[-1])
        if filters:
            params["filter"] = ",".join(filters)
        data = get("works", params)
        records, total = data["results"], data.get("meta", {}).get("count")
    candidates, seen = [], set()
    for work in records:
        doi = normalize_doi(work["doi"]) if work.get("doi") else None
        identity = doi or work["id"]
        if identity in seen:
            continue
        seen.add(identity)
        location = work.get("primary_location") or {}
        candidates.append({"id": work["id"], "doi": doi, "title": work.get("display_name"),
                           "year": work.get("publication_year"), "authors": [a["author"].get("display_name") for a in work.get("authorships", [])],
                           "source": (location.get("source") or {}).get("display_name"),
                           "url": location.get("landing_page_url"), "referenced_works": work.get("referenced_works", []),
                           "cited_by_count": work.get("cited_by_count"), "is_retracted": work.get("is_retracted"),
                           "evidence": "metadata_only"})
    result = {"ok": True, "query": query, "cites": cites, "references": references, "year": year,
              "seed_id": seed.get("id") if seed else None, "total": total, "count": len(candidates),
              "results": candidates, "requests": requests,
              "limitations": ["仅取得书目信息，尚未阅读全文；检索结果不证明对论断的支持"]}
    write_json(output, "literature.json", result)
    return result


def _plain(value):
    value = re.sub(r"\\[A-Za-z]+", "", value or "")
    return "".join(c for c in unicodedata.normalize("NFKD", value).casefold() if c.isalnum())


def check_references(source, output, timeout=30):
    from .bibliography import read_bibliography
    path = Path(source)
    if path.is_file():
        entries = read_bibliography(path.read_text(encoding="utf-8"))
    else:
        entries = [{"citekey": None, "doi": normalize_doi(source)}]
    output = fresh_directory(output)
    findings, requests = [], []
    cache = {}
    for entry in entries:
        finding = {"citekey": entry.get("citekey"), "doi": entry.get("doi"), "differences": []}
        if not entry.get("doi"):
            finding.update(status="unverified", reason="没有 DOI；未自动猜测")
            findings.append(finding)
            continue
        try:
            doi = normalize_doi(entry["doi"])
            url = "https://api.crossref.org/works/" + quote(doi, safe="")
            if doi not in cache:
                data = fetch_json(url, timeout)
                raw = "crossref-" + str(len(cache) + 1) + ".json"
                write_json(output, raw, data)
                cache[doi] = data["message"]
                requests.append({"url": url, "raw": raw, "retrieved_at": datetime.now(timezone.utc).isoformat()})
            record = cache[doi]
            title = " ".join(record.get("title", []))
            years = sorted({str(record[k]["date-parts"][0][0]) for k in ("published", "published-print", "published-online", "issued") if record.get(k, {}).get("date-parts")})
            authors = [a.get("family", "") for a in record.get("author", [])]
            if normalize_doi(record["DOI"]) != doi:
                finding["differences"].append("doi")
            if entry.get("title") and _plain(entry["title"]) != _plain(title):
                finding["differences"].append("title")
            if entry.get("year") and str(entry["year"]) not in years:
                finding["differences"].append("year")
            if entry.get("authors") and [_plain(a) for a in entry["authors"]] != [_plain(a) for a in authors]:
                finding["differences"].append("authors")
            finding.update(status="review" if finding["differences"] else "matched", metadata={
                "doi": record.get("DOI"), "title": title, "authors": authors, "years": years,
                "container_title": record.get("container-title"), "type": record.get("type"),
                "updates": record.get("update-to", []), "relations": record.get("relation", {})})
        except (ValueError, RuntimeError, KeyError) as exc:
            finding.update(status="unverified", reason=str(exc))
        findings.append(finding)
    result = {"ok": bool(findings) and all(x["status"] == "matched" for x in findings), "entries": findings, "requests": requests,
              "limitations": ["Crossref 仅核对书目；差异不自动改写作者记录", "更新关系的覆盖并不完整；无记录不代表没有撤稿或更正", "未检查原文是否支持稿件结论"]}
    write_json(output, "references-check.json", result)
    return result
