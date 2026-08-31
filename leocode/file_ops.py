"""File upload and attachment handling."""

import os
from pathlib import Path
from typing import Optional


class FileAttachment:
    def __init__(self, path: str, content: str, name: str, size: int):
        self.path = path
        self.content = content
        self.name = name
        self.size = size

    def __repr__(self):
        return f"FileAttachment({self.name}, {self.size}b)"


def load_file(path: str, max_size: int = 500_000) -> Optional[FileAttachment]:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return None
    if p.is_dir():
        return _load_directory(p)
    if p.stat().st_size > max_size:
        return FileAttachment(str(p), f"[File too large: {p.stat().st_size} bytes]", p.name, p.stat().st_size)
    try:
        content = p.read_text(errors="ignore")
        return FileAttachment(str(p), content, p.name, len(content))
    except Exception as e:
        return FileAttachment(str(p), f"[Error reading file: {e}]", p.name, 0)


def _load_directory(dir_path: Path) -> Optional[FileAttachment]:
    tree_parts = []
    exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java", ".c", ".cpp", ".h", ".md",
            ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".sh", ".css", ".html", ".vue", ".svelte"}
    included = 0
    total = 0
    for f in sorted(dir_path.rglob("*")):
        if f.is_file() and f.suffix.lower() in exts and f.stat().st_size < 100_000:
            total += 1
            rel = f.relative_to(dir_path)
            try:
                content = f.read_text(errors="ignore")
                tree_parts.append(f"--- {rel} ---\n{content[:5000]}\n")
                included += 1
            except Exception:
                continue
            if included >= 20:
                tree_parts.append(f"\n... and {total - included} more files")
                break
    if not tree_parts:
        return None
    return FileAttachment(
        str(dir_path),
        "\n".join(tree_parts),
        dir_path.name,
        len("\n".join(tree_parts)),
    )


def read_file_for_context(path: str) -> str:
    attachment = load_file(path)
    if not attachment:
        return f"Could not read: {path}"
    return attachment.content


def get_file_info(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Not found: {path}"
    if p.is_dir():
        files = list(p.rglob("*"))
        code_files = [f for f in files if f.is_file() and f.suffix.lower() in {".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp"}]
        return f"Directory: {p}\nTotal files: {len([f for f in files if f.is_file()])}\nCode files: {len(code_files)}\nSize: {sum(f.stat().st_size for f in files if f.is_file())} bytes"
    return f"File: {p}\nSize: {p.stat().st_size} bytes\nType: {p.suffix}"
