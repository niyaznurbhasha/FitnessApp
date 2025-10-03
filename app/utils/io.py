from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Any

def write_json_atomic(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmppath = tempfile.mkstemp(prefix=p.name, dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmppath, p)  # atomic on same filesystem
    except Exception:
        try:
            os.remove(tmppath)
        finally:
            raise
