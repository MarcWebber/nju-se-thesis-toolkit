"""Import and adapt the NJUThesis sample without changing its format implementation.

This module recognizes literal commands in the upstream sample, not arbitrary TeX.
Unknown main-document structures are inspected but never rewritten automatically.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import unicodedata
import zipfile

from .files import digest, local, read_json, tex_text, write_json


MAX_FILES = 5000
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
CONTENT_FILE = "thesis-content.generated.tex"
INFO_FILE = "thesis-info.generated.tex"
CHAPTER_ID = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")


def _relative(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("工程路径必须为非空的相对路径")
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts) or ":" in name:
        raise ValueError("工程路径不能包含绝对路径、空段或上级目录：" + name)
    return name


def _files(directory):
    """Enumerate every regular source file, refusing links and special files."""
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("论文工程目录不存在或是符号链接：" + str(directory))
    paths = []
    for current, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError("论文工程不允许符号链接或特殊文件：" + str(path))
            if stat.S_ISREG(mode):
                paths.append(path)
    return sorted(paths)


def project_paths(root, config):
    manuscript = config.get("manuscript", {})
    if not isinstance(manuscript, dict) or manuscript.get("format") != "latex":
        raise ValueError("manuscript.format 必须为 latex")
    name = _relative(manuscript.get("root", "paper"))
    # Source and generated trees must never overlap.
    if name.split("/")[0] in ("build", "reports", ".thesis", "release", "requests"):
        raise ValueError("manuscript.root 不能与输出目录重叠")
    paper = local(root, name)
    main = local(paper, _relative(manuscript.get("main", "njuthesis-sample.tex")))
    if not paper.is_dir() or not main.is_file():
        raise ValueError("缺少原生论文工程或主 TeX 文件：" + str(main))
    if main.suffix.lower() != ".tex":
        raise ValueError("主文件必须是 .tex 文件")
    return paper, main


def import_project(root, archive, main="njuthesis-sample.tex"):
    """Validate an archive completely, then install its original bytes and backup."""
    root = Path(root).resolve()
    archive = Path(archive)
    main = _relative(main)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError("模板 ZIP 不存在或是符号链接")
    paper = local(root, "paper")
    backup = local(root, ".thesis/template")
    if paper.exists() and (not paper.is_dir() or any(paper.iterdir())):
        raise ValueError("paper 非空，不能覆盖已有论文工程")
    if backup.exists():
        raise ValueError("已有模板备份，不能覆盖 .thesis/template")
    if archive.stat().st_size > MAX_TOTAL_BYTES:
        raise ValueError("模板 ZIP 超过大小限制")
    archive_hash = digest(archive)
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        if not entries or len(entries) > MAX_FILES:
            raise ValueError("模板 ZIP 为空或文件数量超过限制")
        names, files, total = {}, [], 0
        for item in entries:
            if "\x00" in item.orig_filename:
                raise ValueError("模板 ZIP 路径包含空字符")
            name = _relative(item.filename[:-1] if item.is_dir() else item.filename)
            canonical = unicodedata.normalize("NFC", name).casefold()
            if canonical in names:
                raise ValueError("模板 ZIP 包含重名路径：" + name)
            names[canonical] = item.is_dir()
            mode = item.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or item.flag_bits & 1:
                raise ValueError("模板 ZIP 不允许链接、特殊文件或加密文件：" + name)
            if kind == stat.S_IFDIR and not item.is_dir():
                raise ValueError("模板 ZIP 的目录标识冲突：" + name)
            total += item.file_size
            if (item.file_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or
                    item.file_size > max(1, item.compress_size) * MAX_COMPRESSION_RATIO):
                raise ValueError("模板 ZIP 超过解压大小或压缩比例限制")
            if not item.is_dir():
                files.append((item, name))
        for name in names:
            for parent in PurePosixPath(name).parents:
                if str(parent) != "." and names.get(str(parent)) is False:
                    raise ValueError("模板 ZIP 的文件与目录路径冲突：" + name)
        original_names = {name for _, name in files}
        if main not in original_names or "njuthesis.cls" not in original_names:
            raise ValueError("模板 ZIP 缺少指定主文件或 njuthesis.cls")
        with tempfile.TemporaryDirectory(prefix=".template-import-", dir=str(root)) as staging:
            stage = Path(staging)
            staged_paper, staged_backup = stage / "paper", stage / "template"
            staged_paper.mkdir()
            staged_backup.mkdir()
            for item in entries:
                if item.is_dir():
                    (staged_paper / _relative(item.filename[:-1])).mkdir(parents=True, exist_ok=True)
            hashes = {}
            for item, name in files:
                target = staged_paper / name
                target.parent.mkdir(parents=True, exist_ok=True)
                content = source.read(item)  # ZipFile also verifies the CRC.
                if len(content) != item.file_size:
                    raise ValueError("模板 ZIP 文件大小不一致：" + name)
                target.write_bytes(content)
                hashes[name] = hashlib.sha256(content).hexdigest()
            shutil.copyfile(archive, staged_backup / "source.zip")
            if digest(staged_backup / "source.zip") != archive_hash:
                raise ValueError("导入期间源 ZIP 发生变化，请重试")
            manifest = {"schema_version": 1, "main": main, "archive_sha256": archive_hash,
                        "files": dict(sorted(hashes.items()))}
            (staged_backup / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            backup.parent.mkdir(parents=True, exist_ok=True)
            if backup.exists() or (paper.exists() and any(paper.iterdir())):
                raise ValueError("导入期间目标目录发生变化，请重试")
            os.rename(staged_backup, backup)
            try:
                os.replace(staged_paper, paper)
            except BaseException:
                # Move our newly-created backup back into temporary storage.
                os.rename(backup, staged_backup)
                raise
    bibliography = [name for name in sorted(original_names) if name.lower().endswith(".bib")]
    return {"format": "latex", "root": "paper", "main": main, "bibliography": bibliography}


def _mask_comments(text):
    """Blank comments while retaining offsets for edits to the original text."""
    result = list(text)
    index = 0
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "%":
            end = text.find("\n", index)
            if end == -1:
                end = len(text)
            result[index:end] = " " * (end - index)
            index = end
        else:
            index += 1
    return "".join(result)


def _group(text, start, opening="{", closing="}"):
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != opening:
        raise ValueError("无法识别模板中的静态 TeX 参数")
    depth, index = 1, start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == opening:
            depth += 1
        elif text[index] == closing:
            depth -= 1
            if depth == 0:
                return text[start + 1:index], start, index + 1
        index += 1
    raise ValueError("模板中的 TeX 参数括号不完整")


def _split_options(value):
    parts, start, depth = [], 0, 0
    for index, char in enumerate(value):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "," and depth == 0:
            if value[start:index].strip():
                parts.append(value[start:index].strip())
            start = index + 1
    if value[start:].strip():
        parts.append(value[start:].strip())
    return parts


def _class(text):
    masked = _mask_comments(text)
    matches = list(re.finditer(r"\\documentclass\b", masked))
    if len(matches) != 1:
        raise ValueError("必须有且只有一个可识别的 documentclass")
    match = matches[0]
    index = match.end()
    while index < len(masked) and masked[index].isspace():
        index += 1
    options = ""
    if masked[index:index + 1] == "[":
        options, _, index = _group(masked, index, "[", "]")
    classname, _, end = _group(masked, index)
    parsed = {}
    for item in _split_options(options):
        key, separator, value = item.partition("=")
        parsed[key.strip()] = value.strip().strip("{}") if separator else True
    return classname.strip(), parsed, match.start(), end


def _literal_path(value):
    if any(char in value for char in "\\#${}"):
        return None
    return _relative(value.strip())


def inspect_project(root, config):
    paper, main = project_paths(root, config)
    _files(paper)
    text = main.read_text(encoding="utf-8")
    classname, options, _, _ = _class(text)
    warnings, inputs, missing, active_bibs, unknown = [], set(), set(), set(), []
    queue, visited = [main], set()
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        visited.add(path)
        masked = _mask_comments(path.read_text(encoding="utf-8"))
        for match in re.finditer(r"\\(?:input|include)\b", masked):
            argument = re.match(r"\s*\{([^{}]*)\}", masked[match.end():])
            if argument is None:
                unknown.append(masked[match.start():match.end() + 80].split("\n")[0])
                continue
            value = _literal_path(argument.group(1))
            if value is None:
                unknown.append(match.group(0) + argument.group(0))
                continue
            target = local(paper, value)
            if not target.suffix:
                target = local(paper, value + ".tex")
            name = target.relative_to(paper).as_posix()
            inputs.add(name)
            if not target.is_file():
                missing.add(name)
            elif target.suffix.lower() in (".tex", ".def"):
                queue.append(target)
        for match in re.finditer(r"\\addbibresource\s*(?:\[[^\]]*\]\s*)?\{([^{}]*)\}", masked):
            value = _literal_path(match.group(1))
            if value is not None:
                active_bibs.add(value)
            else:
                unknown.append(match.group(0))
        for match in re.finditer(r"\\njusetup\s*\[\s*bib\s*\]\s*\{", masked):
            body, _, _ = _group(masked, match.end() - 1)
            for item in _split_options(body):
                key, _, value = item.partition("=")
                if key.strip() == "resource":
                    for raw in _split_options(value.strip().strip("{}")):
                        value = _literal_path(raw)
                        if value is not None:
                            active_bibs.add(value)
                        else:
                            unknown.append(raw)
    manuscript = config["manuscript"]
    configured = manuscript.get("bibliography", sorted(active_bibs))
    if not isinstance(configured, list) or not all(isinstance(value, str) for value in configured):
        raise ValueError("manuscript.bibliography 必须是相对路径数组")
    bibliography = sorted(active_bibs | {_relative(value) for value in configured})
    for name in bibliography:
        if not name.lower().endswith(".bib"):
            raise ValueError("文献文件必须为 .bib：" + name)
        if not local(paper, name).is_file():
            missing.add(name)
    template_version = "unknown"
    cls = local(paper, "njuthesis.cls")
    if cls.is_file():
        version = re.search(r"\\GetIdInfo\s+\$Id:\s+njuthesis\.dtx\s+(\d+\.\d+\.\d+)", _mask_comments(cls.read_text(encoding="utf-8")))
        if version:
            template_version = version.group(1)
    document_type = options.get("type", "bachelor") if classname == "njuthesis" else "unknown"
    degree = options.get("degree", "academic") if classname == "njuthesis" else "unknown"
    if document_type not in ("bachelor", "master", "doctor", "postdoc"):
        document_type = "unknown"
    if degree not in ("academic", "professional"):
        degree = "unknown"
    for key, allowed in (("type", ("bachelor", "master", "doctor", "postdoc")),
                         ("degree", ("academic", "professional"))):
        if key in manuscript and manuscript[key] not in allowed:
            raise ValueError("manuscript." + key + " 的值无效")
    if "type" not in options and classname == "njuthesis":
        warnings.append("主文件未设置 type，模板默认本科 bachelor")
    if "degree" not in options and classname == "njuthesis":
        warnings.append("主文件未设置 degree，模板默认学术型 academic")
    if template_version == "unknown":
        warnings.append("无法确定 NJUThesis 版本")
    if unknown:
        warnings.append("存在动态路径，静态检查无法确定其依赖")
    if set(configured) - active_bibs:
        warnings.append("部分登记文献文件尚未在 TeX 工程启用")
    if missing:
        warnings.append("缺少输入文件：" + "、".join(sorted(missing)))
    return {"format": "latex", "root": paper.relative_to(Path(root).resolve()).as_posix(),
            "main": main.relative_to(paper).as_posix(), "documentclass": classname,
            "template_version": template_version, "class_options": options,
            "document_type": document_type, "degree": degree,
            "effective_type": manuscript.get("type", document_type),
            "effective_degree": manuscript.get("degree", degree),
            "inputs": sorted(inputs), "bibliography": bibliography,
            "active_bibliography": sorted(active_bibs), "missing_inputs": sorted(missing),
            "unknown_inputs": unknown, "warnings": warnings}


def _bib_entries(text):
    """Locate whole BibTeX entries, skipping quoted/braced field contents."""
    index = 0
    while index < len(text):
        if text[index] == "%":
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline + 1
            continue
        match = re.match(r"@([A-Za-z]+)\s*([({])", text[index:])
        if not match:
            index += 1
            continue
        entry_type, opening = match.groups()
        start = index + match.end()
        index, depth, quoted = start, 0, False
        while index < len(text):
            char = text[index]
            if char == "\\":
                index += 2
                continue
            if char == '"' and depth == 0:
                quoted = not quoted
            elif not quoted:
                if char == "{":
                    depth += 1
                elif char == "}" and depth:
                    depth -= 1
                elif depth == 0 and char == ("}" if opening == "{" else ")"):
                    yield entry_type.lower(), text[start:index]
                    index += 1
                    break
            index += 1
        else:
            raise ValueError("BibTeX 条目的括号或引号不完整")




def _unique_environment(text, name):
    masked = _mask_comments(text)
    begin = list(re.finditer(r"\\begin\s*\{" + re.escape(name) + r"\}", masked))
    end = list(re.finditer(r"\\end\s*\{" + re.escape(name) + r"\}", masked))
    if len(begin) != 1 or len(end) != 1 or begin[0].end() >= end[0].start():
        raise ValueError("无法唯一定位模板区域：" + name)
    return begin[0].end(), end[0].start()


def _sample_body(text):
    masked = _mask_comments(text)
    start = list(re.finditer(r"\\mainmatter\b", masked))
    end = list(re.finditer(r"\\printbibliography\b", masked))
    if len(start) != 1 or len(end) != 1 or start[0].end() >= end[0].start():
        raise ValueError("无法唯一定位 NJUThesis 示例正文区域")
    body = masked[start[0].end():end[0].start()]
    sample = (r"\chapter{引言}\section{量子计算}"
              r"John Preskill 认为我们现在处于“含噪声的中型量子时代”。\cite{preskill2018}"
              "量子位的不稳定性和有限的量子比特数量限制了量子计算机的复杂度和纠错能力。")
    if re.sub(r"\s+", "", body) != re.sub(r"\s+", "", sample):
        raise ValueError("主文件不是标准 NJUThesis 示例正文；请人工确认内容插槽，未替换已有正文")
    return start[0].end(), end[0].start()


def effective_info(config):
    """Resolve plain-text project metadata and explicit native TeX fields."""
    if not isinstance(config, dict) or not isinstance(config.get("manuscript", {}), dict):
        raise ValueError("论文配置与 manuscript 必须是对象")
    info = config.get("manuscript", {}).get("info", {})
    if not isinstance(info, dict) or any(not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z-]*\*?", key) or not isinstance(value, str)
                                         for key, value in info.items()):
        raise ValueError("manuscript.info 需要原生 NJUThesis 信息键和 TeX 文本值")
    info = dict(info)
    for field, key in (("title", "title"), ("title_en", "title*"), ("author", "author"),
                       ("department", "department"), ("degree", "degree")):
        if field not in config:
            continue
        value = config[field]
        if not isinstance(value, str):
            raise ValueError(field + " 必须是字符串")
        if not value.strip() and info.get(key, "").strip():
            continue
        escaped = tex_text(value)
        if value.strip() and info.get(key, "").strip() and info[key] not in (value, escaped):
            raise ValueError(field + " 与 manuscript.info." + key + " 冲突，请统一信息")
        info[key] = escaped
    return info




def assemble_project(root, config):
    """Adapt only the known sample slots, staging all changes in a build copy."""
    root = Path(root).resolve()
    paper, main = project_paths(root, config)
    inspection = inspect_project(root, config)
    if inspection["documentclass"] != "njuthesis" or inspection["template_version"] != "1.5.1":
        raise ValueError("自动组稿仅支持已核对的 NJUThesis v1.5.1 示例工程")
    if inspection["missing_inputs"] or inspection["unknown_inputs"]:
        raise ValueError("模板有缺失输入或动态输入，需先人工确认依赖")
    sources = _files(paper)
    for name in (CONTENT_FILE, INFO_FILE):
        if local(paper, name).exists():
            raise ValueError("模板中已有组稿保留文件名，未覆盖：" + name)
    outline, front = read_json(root, "outline.json"), read_json(root, "frontmatter.json")
    if not isinstance(outline, dict) or not isinstance(outline.get("chapters"), list) or not outline["chapters"]:
        raise ValueError("outline.json 需要章节数组")
    if not isinstance(front, dict):
        raise ValueError("frontmatter.json 必须是对象")
    content, seen = [], set()
    for chapter in outline["chapters"]:
        if not isinstance(chapter, dict):
            raise ValueError("提纲章节必须是对象")
        key, title = chapter.get("id"), chapter.get("title")
        if not isinstance(key, str) or not CHAPTER_ID.fullmatch(key) or key in seen:
            raise ValueError("章节 ID 无效或重复")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("章节标题不能为空")
        seen.add(key)
        path = local(paper, "chapters/" + key + ".tex")
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise ValueError("缺少原生 TeX 章节：" + key)
        active = _mask_comments(path.read_text(encoding="utf-8"))
        if re.search(r"\\(?:chapter|documentclass|mainmatter|appendix)\b|\\(?:begin|end)\s*\{document\}", active):
            raise ValueError("章节片段不能包含 chapter 或主文档结构命令：" + key)
        content.append("\\chapter{" + tex_text(title) + "}\n\\input{chapters/" + key + ".tex}\n")
    text = main.read_text(encoding="utf-8")
    edits = []
    for key, environment in (("abstract_zh", "abstract"), ("abstract_en", "abstract*")):
        value = front.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("frontmatter.json 缺少 " + key)
        begin, end = _unique_environment(text, environment)
        edits.append((begin, end, "\n" + value.strip() + "\n"))
    acknowledgement = front.get("acknowledgements")
    if acknowledgement is not None:
        if not isinstance(acknowledgement, str) or not acknowledgement.strip():
            raise ValueError("acknowledgements 应为非空 TeX 文本，省略此字段可保留原致谢")
        begin, end = _unique_environment(text, "acknowledgement")
        edits.append((begin, end, "\n" + acknowledgement.strip() + "\n"))
    begin, end = _sample_body(text)
    edits.append((begin, end, "\n\n\\input{" + CONTENT_FILE + "}\n\n"))
    info = effective_info(config)
    for key, option in (("keywords_zh", "keywords"), ("keywords_en", "keywords*")):
        values = front.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError("frontmatter.json 需要非空关键词数组：" + key)
        info[option] = ",".join("{" + value + "}" for value in values)
    generated_info = "\\njusetup[info]{\n" + "\n".join("  " + key + " = {" + value + "}," for key, value in info.items()) + "\n}\n"
    masked = _mask_comments(text)
    documents = list(re.finditer(r"\\begin\s*\{document\}", masked))
    if len(documents) != 1:
        raise ValueError("无法唯一定位主文档起点")
    edits.append((documents[0].start(), documents[0].start(), "\\input{" + INFO_FILE + "}\n\n"))
    overrides = {key: config["manuscript"][key] for key in ("type", "degree") if key in config["manuscript"]}
    if overrides:
        classname, _, begin, end = _class(text)
        declaration = _mask_comments(text[begin:end])
        option_start = declaration.find("[")
        raw = _group(declaration, option_start, "[", "]")[0] if option_start >= 0 else ""
        options = [item for item in _split_options(raw) if item.partition("=")[0].strip() not in overrides]
        options.extend(key + " = " + value for key, value in overrides.items())
        rendered = ",\n    ".join(options)
        edits.append((begin, end, "\\documentclass[\n    " + rendered + "\n]{" + classname + "}"))
    for begin, end, replacement in sorted(edits, reverse=True):
        text = text[:begin] + replacement + text[end:]
    build = local(root, "build")
    target = local(root, "build/project")
    build.mkdir(parents=True, exist_ok=True)
    if target.exists():
        _files(target)
    source_hashes = {path.relative_to(paper).as_posix(): digest(path) for path in sources}
    with tempfile.TemporaryDirectory(prefix=".assembly-", dir=str(build)) as directory:
        staging = Path(directory) / "project"
        shutil.copytree(paper, staging)
        (staging / main.relative_to(paper)).write_text(text, encoding="utf-8")
        (staging / CONTENT_FILE).write_text("\n".join(content), encoding="utf-8")
        (staging / INFO_FILE).write_text(generated_info, encoding="utf-8")
        current_hashes = {path.relative_to(paper).as_posix(): digest(path) for path in _files(paper)}
        if current_hashes != source_hashes:
            raise ValueError("组稿期间源工程发生变化，请重试")
        previous = Path(directory) / "previous"
        if target.exists():
            os.rename(target, previous)
        try:
            os.rename(staging, target)
        except BaseException:
            if previous.exists():
                os.rename(previous, target)
            raise
    report = {"template": "njuthesis-sample-1.5.1", "project": "build/project",
              "main": main.relative_to(paper).as_posix(), "source_files": source_hashes,
              "chapters": [chapter["id"] for chapter in outline["chapters"]],
              "class_overrides": overrides, "info": info, "inspection": inspection,
              "preserved": ["source_project", "setup", "class_and_def", "bibliography", "assets", "appendix"],
              "warnings": ["保留了模板原附录，提交前需由作者审阅其内容"]}
    write_json(root, "reports/assembly.json", report)
    outputs = [path.relative_to(root).as_posix() for path in _files(target)] + ["reports/assembly.json"]
    return {"status": "done", "outputs": outputs, "checks": [{"name": "native_template", "ok": True,
            "detail": "在工程副本完成组稿，原始模板与格式文件保持不变"}],
            "message": "原生 NJUThesis 工程组稿完成，原附录已保留，需作者审阅",
            "project": "build/project", "main": main.relative_to(paper).as_posix()}
