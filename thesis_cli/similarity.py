"""Compare supplied prose locally with RapidFuzz; no remote corpus or AI score."""

import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

from .files import digest, write_json


def read_passages(path, min_chars):
    path = Path(path).resolve()
    text = path.read_text(encoding="utf-8-sig")
    metadata = {"path": str(path), "sha256": digest(path)}
    if path.suffix.lower() == ".json":
        envelope = json.loads(text)
        if not isinstance(envelope, dict) or envelope.get("ok") is False:
            raise ValueError("飞书导出响应无效：" + str(path))
        data = envelope.get("data", envelope)
        document = data.get("document", data) if isinstance(data, dict) else None
        if not isinstance(document, dict) or not isinstance(document.get("content"), str):
            raise ValueError("需要包含 XML content 的飞书导出：" + str(path))
        metadata.update({key: document.get(key) for key in ("document_id", "revision_id")})
        text = document["content"]
    if path.suffix.lower() in {".json", ".xml"}:
        if re.search(r"<!DOCTYPE|<!ENTITY", text, re.I):
            raise ValueError("不支持 XML DTD 或实体声明")
        text = re.sub(r"^\s*<\?xml[^?]*\?>", "", text)
        try:
            root = ET.fromstring("<document>" + text + "</document>")
        except ET.ParseError as error:
            raise ValueError("无法解析飞书 XML：" + str(error)) from error
        tags = {"p", "li", "checkbox"}

        def inline(node):
            if node.tag == "br":
                return "\n"
            return (node.text or "") + "".join(
                (inline(child) if child.tag not in tags | {"ul", "ol"} else "")
                + (child.tail or "") for child in node)

        blocks = [(node.get("id"), inline(node)) for node in root.iter() if node.tag in tags]
    elif path.suffix.lower() in {".txt", ".md"}:
        blocks = [("line:%d" % number, line) for number, line in enumerate(text.splitlines(), 1)]
    else:
        raise ValueError("比对支持飞书 JSON/XML 和 UTF-8 TXT/MD，不接受 TeX 或 PDF")
    passages = []
    for block_id, block in blocks:
        for sentence in re.split(r"(?<=[。！？!?；;])|(?<=\.)\s+", block):
            normalized = re.sub(r"\s+", "", unicodedata.normalize("NFKC", sentence)).casefold()
            if len(normalized) >= min_chars:
                passages.append({"block_id": block_id, "text": sentence.strip(), "normalized": normalized})
    return metadata, passages


def compare_passages(source, references, output, threshold=85, min_chars=20):
    try:
        from rapidfuzz import __version__, fuzz, process
    except ImportError as error:
        raise RuntimeError("请安装重复检查依赖：pip install 'nju-se-thesis[similarity]'") from error
    if not 0 < threshold <= 100 or min_chars < 1:
        raise ValueError("threshold 需在 0 到 100 之间且大于 0，min-chars 需为正数")
    paths = [Path(source).resolve(), *(Path(path).resolve() for path in references)]
    if len(set(paths)) != len(paths):
        raise ValueError("稿件与参考文件不能重复")
    source_info, passages = read_passages(source, min_chars)
    corpus, reference_info = [], []
    for path in references:
        info, parts = read_passages(path, min_chars)
        reference_info.append(info)
        corpus.extend({**part, "path": str(path.resolve())} for part in parts)
    if not passages or not corpus:
        raise ValueError("稿件或参考资料没有达到 min-chars 的可比对文本")
    choices = [part["normalized"] for part in corpus]
    matches = []
    for part in passages:
        for _, score, index in process.extract(part["normalized"], choices, scorer=fuzz.ratio,
                                               score_cutoff=threshold, limit=3):
            reference = corpus[index]
            matches.append({"block_id": part["block_id"], "text": part["text"],
                            "reference": reference["path"], "reference_block_id": reference["block_id"],
                            "reference_text": reference["text"], "similarity": round(score, 2)})
    report = {"ok": not matches, "engine": "RapidFuzz " + __version__,
              "method": "fuzz.ratio; NFKC, casefold, ignore whitespace; top 3 per sentence",
              "scope": "仅比对提供的资料；分数是文本相似度，不是全文重复率或 AI 率",
              "source": source_info, "references": reference_info,
              "threshold": threshold, "min_chars": min_chars,
              "sentences": len(passages), "reference_sentences": len(corpus), "matches": matches}
    write_json(output.parent, output.name, report, overwrite=False)
    return report
