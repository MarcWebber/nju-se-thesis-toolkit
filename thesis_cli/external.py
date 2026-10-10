"""Small shared helpers for optional command-line tools."""

import os
from pathlib import Path
import shutil
import signal
import subprocess


def fresh_directory(path):
    path = Path(path).absolute()
    if path.is_symlink() or (path.exists() and (not path.is_dir() or any(path.iterdir()))):
        raise ValueError("输出必须是新的空目录：" + str(path))
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def tool_path(name):
    override = os.environ.get("THESIS_" + name.upper())
    if override:
        return override
    for root in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent.parent]:
        candidate = root / ".tools" / name / "bin" / name
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def pdfjs_modules(override=None):
    if override or os.environ.get("THESIS_PDFJS_MODULES"):
        return Path(override or os.environ["THESIS_PDFJS_MODULES"]).resolve()
    for root in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent.parent]:
        candidate = root / ".tools/pdfjs/node_modules"
        if (candidate / "pdfjs-dist/package.json").is_file():
            return candidate
    return None


def run_logged(command, log, timeout, env=None):
    if timeout <= 0:
        raise ValueError("超时必须大于 0 秒")
    with Path(log).open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise RuntimeError("外部工具超时或中断；日志：" + str(log))
    if code:
        raise RuntimeError("外部工具退出码 " + str(code) + "；日志：" + str(log))
