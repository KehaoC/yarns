# 规则引擎：生成一条假设 发布 tender 写日报

import os, time, uuid
from dotenv import load_dotenv
from .context_ops import list_human_markdowns, ensure_ai_dirs
from .exchange import publish_tender
from .reporter import write_daily_report

def generate_hypotheses(files: list[str]) -> list[str]:
    """
    MVP 规则引擎（无模型支持）
    """
    has_notes = any("notes" in f for f in files)
    if has_notes:
        return [{
            "goal": "整理 notes 下的 Markdown 为一份合并摘要",
            "capability": "ingest-markdown",
            "inputs": {
                "paths": ["context/human/notes"]
            },
            "budget": 4.5
        }]
    else:
        return [{
            "goal": "对 profile 进行深层的心理学分析",
            "capability": "ingest-markdown",
            "inputs": {
                "paths": ["context/human"]
            },
            "budget": 3.0
        }]

def one_loop():
    """
    只做生成假设，发布标书，写日报
    """
    load_dotenv()
    ensure_ai_dirs()

    files = list_human_markdowns()
    hyps = generate_hypotheses(files)

    logs = ['# Yarno Daily Run (Day1)', ""]
    for h in hyps:
        tender = {
            "tender_id": str(uuid.uuid4()),
            "yarno_id": os.getenv("YARNO_ID", "yarno-local"),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "goal": h["goal"],
            "required_capabilities": [h["capability"]],
            "inputs": h["inputs"],
            "budget_hint": {
                "currencty": "YCOIN",
                "max_amount": h["budget"]
            },
            "auth": {"mode": "shared_secret"},
            "expires_at":None
        }
        tid = publish_tender(tender)
        logs.append(f"- 发布标书 tender_id={tid}：{h['goal']}")
        logs.append(f"  · 能力：{h['capability']}")
        logs.append(f"  · 输入：{h['inputs']}")
        logs.append(f"  · 预算上限：{h['budget']} YCOIN")

    write_daily_report(logs)