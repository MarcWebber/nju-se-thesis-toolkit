"""Compile a TeX file in a copy of its project and inspect compiler logs."""

import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess


ENGINE_HEADER = re.compile(r"^This is (?:XeTeX|LuaHBTeX|LuaTeX|pdfTeX|TeX)\b", re.M)


def check_compile_log(log):
    """Return blocking findings with code, one-based line and original message."""
    text = log.read_text(encoding="utf-8", errors="replace") if isinstance(log, Path) else str(log)
    if not text.strip():
        return [{"code": "empty_log", "line": 1, "message": "编译日志为空"}]
    lines = text.splitlines()
    last_engine = max((number for number, line in enumerate(lines, 1) if ENGINE_HEADER.match(line)), default=1)
    findings = []
    for number, line in enumerate(lines, 1):
        nearby = " ".join(re.sub(r"^\s*\([A-Za-z][A-Za-z0-9_-]*\)\s*", "", part)
                          for part in lines[number - 1:number + 2])
        code = None
        if re.search(r"Undefined control sequence", line, re.I):
            code = "undefined_control_sequence"
        elif re.match(r"\s*!\s*\S", line) or re.search(r"(?:LaTeX|Package\s+\S+|Class\s+\S+|pdfTeX)\s+(?:Fatal\s+)?Error\b", line, re.I):
            code = "tex_error"
        elif re.search(r"(?:Emergency stop|Fatal error occurred|^\s*(?:ERROR|FATAL|FAILED)\s*[-:])", line, re.I):
            code = "compiler_error"
        elif not line.startswith("LaTeX Font Info:") and re.search(r"Missing character:|Font .*(?:not found|not available|not loadable|not installed|cannot be found|undefined)", line, re.I):
            code = "missing_font_or_glyph"
        elif re.search(r"(?:Citation|Reference)\b", line, re.I) and re.search(r"\bundefined\b", nearby, re.I):
            code = "unresolved_reference"
        elif re.search(r"There were undefined (?:references|citations)|(?:didn't find a database entry|couldn't open database file)", line, re.I):
            code = "unresolved_reference"
        elif re.search(r"Please\s+(?:\(re\)run|rerun|run)\s+(?:Biber|BibTeX|LaTeX)|Rerun to get cross-references right|Label\(s\) may have changed", nearby if "Please" in line else line, re.I):
            code = "rerun_required"
        if code and not (code in ("unresolved_reference", "rerun_required") and number < last_engine):
            findings.append({"code": code, "line": number, "message": line.strip()})
    return findings


def _copy_project(project, destination, output):
    def exclude_output(directory, names):
        excluded = []
        for name in names:
            path = Path(directory) / name
            if path == output or name in {".tools", ".venv", "node_modules", ".git", "__pycache__"}:
                excluded.append(name)
            elif path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError("工程只支持普通文件和目录：" + str(path))
        return excluded

    shutil.copytree(project, destination, ignore=exclude_output)


def _pdf_pages(path):
    from pypdf import PdfReader

    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("编译产物不是 PDF")
        stream.seek(max(0, path.stat().st_size - 1024))
        if b"%%EOF" not in stream.read():
            raise ValueError("编译产物 PDF 不完整")
        stream.seek(0)
        reader = PdfReader(stream, strict=True)
        if reader.is_encrypted or not reader.pages:
            raise ValueError("编译产物 PDF 加密或没有页面")
        for page in reader.pages:
            box = [float(value) for value in page.mediabox]
            if not all(math.isfinite(value) for value in box) or box[2] <= box[0] or box[3] <= box[1]:
                raise ValueError("PDF 页面尺寸无效")
            contents = page.get_contents()
            if contents is not None:
                list(contents.operations)
        return len(reader.pages)


def build_tex(main, output, timeout=180, skip_preview=False, modules=None, cmap=None,
              bibliography_source=None, bibliography_target="references.bib"):
    """Build main.tex in a fresh directory; retain source copy and all logs.

    Shell escape and latexmk configuration scripts are disabled. This is not an
    operating-system sandbox: compile only trusted TeX sources.
    """
    main, output = Path(main).absolute(), Path(output).absolute()
    if main.is_symlink() or not main.is_file() or main.suffix != ".tex":
        raise ValueError("主文件必须是普通 .tex 文件：" + str(main))
    if re.search(r"[\x00-\x1f\x7f\x60$;&|<>\"']", main.name):
        raise ValueError("TeX 主文件名含不支持的控制字符或命令字符")
    if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError("输出必须是新的空目录：" + str(output))
    if timeout <= 0:
        raise ValueError("编译超时必须大于 0 秒")
    main, output = main.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    log = output / "compile.log"
    source, compiled = output / "source", output / "compiled"
    with log.open("w", encoding="utf-8") as stream:
        stream.write("主文件：" + str(main) + "\n禁用 shell escape 和 latexmk 配置脚本。\n")
        stream.flush()
        try:
            executables = {name: shutil.which(name) for name in ("latexmk", "xelatex")}
            missing = [name for name, path in executables.items() if not path]
            if missing:
                raise RuntimeError("缺少 TeX 工具：" + ", ".join(missing))
            _copy_project(main.parent, source, output)
            if bibliography_source:
                from .bibliography import sync_bibliography
                from .files import local
                target = local(source, bibliography_target)
                if target.suffix.lower() != ".bib":
                    raise ValueError("文献目标必须是工程内的 .bib 文件")
                synced = sync_bibliography(bibliography_source, output / "bibliography", existing=target if target.is_file() else None)
                if not synced["ok"]:
                    raise ValueError("文献同步存在引用键冲突；见 bibliography/bibliography.json")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(synced["bibliography"], target)
            compiled.mkdir()
            env = os.environ.copy()
            env.update({"openin_any": "p", "openout_any": "p", "TEXMFOUTPUT": str(compiled)})
            command = [executables["latexmk"], "-norc", "-xelatex", "-no-shell-escape",
                       "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
                       "-outdir=" + str(compiled), "./" + main.name]
            stream.write("Command: " + repr(command) + "\n")
            stream.flush()
            process = subprocess.Popen(command, cwd=source, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                returncode = process.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                if isinstance(exc, KeyboardInterrupt):
                    raise
                raise RuntimeError("TeX 编译超时") from exc
            if returncode:
                raise RuntimeError("TeX 编译失败，退出码 " + str(returncode))
            final_log = compiled / (main.stem + ".log")
            if not final_log.is_file():
                raise RuntimeError("未生成 TeX 原始 .log")
            text = final_log.read_text(encoding="utf-8", errors="replace")
            if not ENGINE_HEADER.search(text) or not re.search(r"Output written on .+?\.(?:pdf|xdv|dvi)\b", text, re.S):
                raise RuntimeError("TeX 原始日志没有完整的引擎和输出记录")
            findings = [dict(item, file=str(path)) for path in sorted(compiled.rglob("*"))
                        if path.suffix in (".log", ".blg") and path.is_file()
                        for item in check_compile_log(path)]
            # Final logs decide whether first-pass reference warnings are resolved.
            findings += [dict(item, file=str(log)) for item in check_compile_log(log)
                         if item["code"] not in ("unresolved_reference", "rerun_required")]
            if findings:
                raise RuntimeError("编译日志存在问题：" + findings[0]["message"])
            pdf = compiled / (main.stem + ".pdf")
            pages = _pdf_pages(pdf)
        except (Exception, KeyboardInterrupt) as exc:
            message = "编译已中断" if isinstance(exc, KeyboardInterrupt) else str(exc)
            stream.write("\nFAILED: " + message + "\n")
            if isinstance(exc, KeyboardInterrupt):
                raise
            raise RuntimeError(message + "；日志：" + str(log)) from exc
    from .checks import inspect_pdf
    from .files import write_json
    result = {"main": str(main), "pdf": str(pdf), "log": str(log), "pages": pages, "findings": []}
    if cmap:
        from .pdfpreview import repair_cmap
        initial = inspect_pdf(pdf)
        if any(f["external_cmap_risk"] for f in initial.get("fonts", [])):
            repaired = output / (main.stem + "-preview.pdf")
            result["repair"] = repair_cmap(pdf, repaired, cmap)
            result["original_pdf"], pdf = str(pdf), repaired
            result["pdf"] = str(pdf)
    result["pdf_check"] = inspect_pdf(pdf, None if skip_preview else output / "preview", modules, timeout=timeout)
    result["ok"] = result["pdf_check"]["ok"]
    result["preview_skipped"] = skip_preview
    write_json(output, "build.json", result)
    return result
