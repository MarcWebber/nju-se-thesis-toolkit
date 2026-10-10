"""Export source lines and a traceable, inline TeX listing."""

import hashlib
import json
from pathlib import Path
import re
import subprocess

from .files import local, tex_text


def _git(repo, *args):
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(repo), *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Git 读取超时，请检查仓库后重试") from error
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def export_excerpt(repo, file, output, start=1, end=None, revision=None, caption="", label=""):
    """Export inclusive UTF-8 source lines without modifying the repository."""
    repo = Path(repo).resolve(strict=True)
    source = local(repo, file)
    if not repo.is_dir() or not Path(file).parts:
        raise ValueError("请指定源码目录和相对文件路径")
    if type(start) is not int or start < 1 or (end is not None and (type(end) is not int or end < start)):
        raise ValueError("行号必须是从 1 开始的闭区间")
    if label and not re.fullmatch(r"[A-Za-z0-9:._/-]+", label):
        raise ValueError("标签仅支持字母、数字和 :._/-")
    output = Path(output).absolute()
    if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError("输出目录必须不存在或为空")

    commit = None
    dirty = None
    try:
        git_root = Path(_git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    except (ValueError, FileNotFoundError):
        if revision is not None:
            raise ValueError("读取指定版本需要 Git 仓库和 git 命令")
    else:
        dirty = bool(_git(repo, "status", "--porcelain", "--untracked-files=normal"))
        try:
            commit = _git(repo, "rev-parse", "--verify", "--end-of-options", (revision or "HEAD") + "^{commit}").decode().strip()
        except ValueError:
            if revision is not None:
                raise
        if revision is not None:
            git_path = source.relative_to(git_root).as_posix()
            entry = _git(repo, "ls-tree", "--full-tree", commit, "--", git_path).split(b"\t", 1)[0]
            if not entry.startswith((b"100644 blob ", b"100755 blob ")):
                raise ValueError("指定版本中的路径不是普通源码文件")
            data = _git(repo, "cat-file", "blob", commit + ":" + git_path)

    if revision is None:
        if not source.is_file():
            raise ValueError("源码路径不是普通文件：" + str(file))
        data = source.read_bytes()
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("代码摘录仅支持 UTF-8 文本") from error
    lines = data.splitlines(keepends=True)
    end = len(lines) if end is None else end
    if start > len(lines) or end > len(lines):
        raise ValueError("摘录行号超出源文件范围")
    snippet = b"".join(lines[start - 1:end])
    code = snippet.decode("utf-8")
    if re.search(r"\\end\s*\{\s*lstlisting\s*\}", code) or "^^" in code:
        raise ValueError("代码包含可退出 lstlisting 的 TeX 序列")
    if any(ord(char) < 32 and char not in "\t\n\r" for char in code):
        raise ValueError("代码包含不支持的控制字符")

    caption = tex_text(caption).replace("\r", " ").replace("\n", " ")
    options = ["numbers=left", "firstnumber=" + str(start), "breaklines=true", "keepspaces=true",
               "columns=fullflexible", "escapechar={}", "escapeinside={}{}",
               "mathescape=false", "texcl=false"]
    if caption:
        options.append("caption={" + caption + "}")
    if label:
        options.append("label={" + label + "}")
    tex = "\\begin{lstlisting}[" + ",".join(options) + "]\n" + code
    if not tex.endswith(("\r", "\n")):
        tex += "\n"
    tex += "\\end{lstlisting}\n"
    # Avoid colliding with the TeX fragment when the source itself is a .tex file.
    snippet_name = "snippet" + (source.suffix if source.suffix not in ("", ".tex") else ".txt")
    manifest = {
        "repository": str(repo), "path": source.relative_to(repo).as_posix(),
        "start": start, "end": end, "revision": commit, "requested_revision": revision,
        "source_kind": "git" if revision is not None else "working-tree",
        "working_tree_dirty": dirty, "source_sha256": hashlib.sha256(data).hexdigest(),
        "excerpt_sha256": hashlib.sha256(snippet).hexdigest(),
        "excerpt": snippet_name, "tex": "snippet.tex", "encoding": "utf-8",
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, contents in ((snippet_name, snippet), ("snippet.tex", tex.encode("utf-8")),
                           ("source.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))):
        with (output / name).open("xb") as stream:
            stream.write(contents)
    return manifest
