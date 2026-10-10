"""File paths, text escaping and source archives."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile


def local(root, name):
    root = Path(root).resolve()
    value = Path(name)
    if value.is_absolute() or ".." in value.parts:
        raise ValueError("路径必须位于论文目录内：" + str(name))
    target = root / value
    current = root
    for part in value.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("论文文件路径不能是符号链接：" + str(name))
    try:
        target.resolve().relative_to(root)
    except ValueError:
        raise ValueError("路径越过论文目录：" + str(name))
    return target


def read_json(root, name):
    return json.loads(local(root, name).read_text(encoding="utf-8"))


def atomic_text(root, name, content, overwrite=True):
    path = local(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".write-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            # Link is atomic and refuses an existing destination.
            os.link(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return str(path.relative_to(Path(root).resolve()))


def write_json(root, name, value, overwrite=True):
    return atomic_text(root, name, json.dumps(value, ensure_ascii=False, indent=2) + "\n", overwrite)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tex_text(value):
    """Escape plain text, never TeX source."""
    table = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "#": r"\#", "%": r"\%",
             "$": r"\$", "&": r"\&", "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(table.get(char, char) for char in value)


def pack_files(sources, output):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("归档输出已存在，未覆盖：" + str(output))
    output = output.resolve()
    entries = {}
    for source in sources:
        source = Path(source).absolute()
        if not source.exists() or source.is_symlink():
            raise ValueError("请选择实际文件或目录：" + str(source))
        source = source.resolve()
        if source == Path(source.anchor):
            raise ValueError("不能归档文件系统根目录")
        if source == output or source in output.parents:
            raise ValueError("归档输出不能放在输入目录内")
        paths = [source, *sorted(source.rglob("*"))] if source.is_dir() else [source]
        for path in paths:
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError("归档不接受符号链接或特殊文件：" + str(path))
            if path.is_file():
                name = path.relative_to(source.parent).as_posix()
                if name in entries or name == "manifest.json":
                    raise ValueError("归档路径重名：" + name)
                entries[name] = path
    if not entries:
        raise ValueError("没有可归档的文件")
    output.parent.mkdir(parents=True, exist_ok=True)
    hashes = {}
    # Hash the archived bytes rather than re-reading a potentially changing source.
    with tempfile.TemporaryDirectory(prefix=".pack-", dir=output.parent) as temporary:
        pending = Path(temporary) / "package.zip"
        with zipfile.ZipFile(pending, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, path in sorted(entries.items()):
                content = path.read_bytes()
                archive.writestr(name, content)
                hashes[name] = hashlib.sha256(content).hexdigest()
            archive.writestr("manifest.json", json.dumps({"files": hashes}, ensure_ascii=False, indent=2))
        os.link(pending, output)
    return {"output": str(output), "files": hashes}
