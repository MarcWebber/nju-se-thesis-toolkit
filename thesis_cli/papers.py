"""Run upstream Docling locally and retain its original provenance."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from .external import fresh_directory, run_logged, tool_path
from .files import digest, write_json


def read_paper(source, output, executable=None, pages=None, ocr=True, pipeline="standard", timeout=600):
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError("需要本地论文或文档文件")
    if pages and not re.fullmatch(r"[1-9]\d*(?:-[1-9]\d*)?", pages):
        raise ValueError("页码使用 1 或 1-4")
    if pages and "-" in pages and int(pages.split("-")[0]) > int(pages.split("-")[1]):
        raise ValueError("页码范围顺序无效")
    if pipeline == "native" and ocr:
        raise ValueError("native 模式不做 OCR，请显式传 --no-ocr；扫描件使用 standard")
    executable = str(executable or tool_path("docling") or "")
    if not executable:
        raise RuntimeError("未找到 Docling；按 docs/integrations.md 配置独立环境或 --docling")
    output = fresh_directory(output)
    saved = output / ("source" + source.suffix.lower())
    shutil.copyfile(source, saved)
    converted = output / "converted"
    converted.mkdir()
    command = [executable, "convert", str(saved), "--to", "json", "--to", "md", "--output", str(converted),
               "--pipeline", pipeline, "--image-export-mode", "referenced", "--document-timeout", str(timeout),
               "--ocr" if ocr else "--no-ocr"]
    if ocr:
        command += ["--ocr-engine", "rapidocr", "--ocr-lang", "ch"]
    if pipeline == "native":
        command += ["--no-tables"]
    if pages:
        command += ["--page-range", pages]
    env = os.environ.copy()
    env.setdefault("HF_HOME", str((Path.cwd() / ".tools/docling-cache/huggingface").resolve()))
    log = output / "docling.log"
    result = {"ok": False, "source": str(source), "source_sha256": digest(saved), "command": command,
              "pipeline": pipeline, "ocr": ocr, "page_range": pages, "log": str(log)}
    try:
        version = subprocess.run([executable, "convert", "--version"], capture_output=True, text=True, timeout=60)
        if version.returncode:
            raise RuntimeError("Docling 版本查询失败")
        result["docling_version"] = version.stdout.strip()
        run_logged(command, log, timeout, env)
        document, markdown = converted / (saved.stem + ".json"), converted / (saved.stem + ".md")
        if not document.is_file() or not markdown.is_file():
            raise RuntimeError("Docling 未生成完整 JSON 与 Markdown；请查看日志")
        data = json.loads(document.read_text(encoding="utf-8"))
        evidence = []
        for kind in ("texts", "tables", "pictures"):
            for item in data.get(kind, []):
                for prov in item.get("prov", []):
                    evidence.append({"item": item.get("self_ref"), "kind": kind, "label": item.get("label"),
                                     "text": item.get("text"), "page_no": prov.get("page_no"),
                                     "bbox": prov.get("bbox"), "charspan": prov.get("charspan")})
        if source.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"} and not evidence:
            raise RuntimeError("解析结果没有原页定位信息，不能作为已验收的论文证据")
        result.update(ok=True, document=str(document), markdown=str(markdown), evidence_items=len(evidence),
                      pages=sorted({e["page_no"] for e in evidence if e["page_no"] is not None}),
                      quality_review_required=True,
                      limitations=["OCR、表格与阅读顺序仍需回到原页核对；坐标保持 Docling 原始坐标系"])
        write_json(output, "evidence.json", {"source_sha256": result["source_sha256"], "items": evidence})
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result["error"] = str(exc)
    write_json(output, "paper.json", result)
    return result
