from datetime import date
from pathlib import Path

def write_daily_report(lines: list[str]):
    p = Path("context/ai/reports") / f"daily-{date.today().strftime('%Y-%m-%d')}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines), encoding="utf-8")