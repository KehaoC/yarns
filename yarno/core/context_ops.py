import glob
from pathlib import Path

def list_human_markdowns() -> list[str]:
    """列出所有 human 目录下的 markdown 文件"""
    return glob.glob("context/human/**/*.md", recursive=True)

def ensure_ai_dirs():
    """确保 ai 空间目录存在"""
    Path("context/ai/reports").mkdir(parents=True, exist_ok=True)
    Path("context/ai/working").mkdir(parents=True, exist_ok=True)
