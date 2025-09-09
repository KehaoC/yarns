下面是一份可直接开工的 MVP 技术文档（两周版）。按文档中的目录结构与示例代码骨架实现，即可跑通文件总线 A2A、Yarno 定时编排、Markdown 双空间 Context、单一野生 Agent：collector_fs、最小授权与账簿。

说明：本文档以最小复杂度为原则，全部本地运行；UI 仅保留极简 CLI 与（可选）一个健康探针 API。可在 macOS/Ubuntu 上用 Python 3.11 实现。

⸻

0. 快速开始（TL;DR）

# 0) 进入任意工作目录
mkdir -p ~/dev/yarns && cd ~/dev/yarns

# 1) 初始化项目结构（见第 2 节），先创建空目录与配置文件
#    你也可以边读文档边创建

# 2) 创建虚拟环境 & 安装依赖
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn typer pydantic python-dotenv apscheduler watchdog

# 3) 写入 .env
echo 'OPENAI_API_KEY=sk-xxxxxx' > .env    # 如暂时没有 key，可留空，Yarno 会回退到规则引擎

# 4) 运行（先起 agent，再跑 Yarno）
python agents/collector_fs/run.py &   # 终端1：野生Agent监听文件总线
python yarno/main.py up               # 终端2：Yarno启动（一次循环 or 按计划任务）

当看到 context/ai/reports/daily-YYYYMMDD.md、ledger/ledger.jsonl 出现内容，闭环即跑通。

⸻

1. 目标与范围

本 MVP 验证点：
	•	无注意力调度：Yarno 能在没有用户显式 Prompt 情况下，从 context/human/ 中提取潜在需求，自动派单给野生 Agent 执行并回写结果。
	•	A2A 文件总线：以本地文件夹承载任务与结果，定义统一 JSON Schema。
	•	最小治理：一次性授权（scope + 预算），最小账簿记录（jsonl）。
	•	只做一个野生 Agent：collector_fs，负责把分散的 Markdown/笔记收拣与归档。

不在本次范围：高可用、横向扩展、复杂 UI、线上部署、真实支付通道、远程 Agent 市场。

⸻

2. 目录结构

yarns/
  .env
  README.md

  config/
    policy.yml          # 授权与预算策略
    scheduler.yml       # 定时策略（可选）

  context/
    human/              # 人的空间（你自由写/粘贴）
      profile.md
      goals.md
      notes/...
    ai/                 # AI 空间（系统生成）
      inbox/
      working/
      reports/
      decisions/

  market/
    agents.json         # Agent 市场（本地清单即可）

  bus/
    inbox/              # Yarno -> Agent 任务（file-bus）
    outbox/             # Agent -> Yarno 结果（file-bus）

  ledger/
    ledger.jsonl        # 账簿（jsonl）

  yarno/
    main.py             # CLI 入口（Typer）
    server.py           # （可选）健康/探针 API (FastAPI)
    core/
      schemas.py        # Pydantic 数据模型
      orchestrator.py   # 编排器（需求假设->派单->验收）
      context_ops.py    # 读写/摘要/查找引用
      market.py         # 发现可用 Agent
      a2a.py            # 文件总线协议
      payments.py       # 账簿写入/余额计算
      consent.py        # 授权/会话签名
      reporter.py       # 日报/周报生成
      utils.py          # 日志/IO/原子写等

  agents/
    collector_fs/
      agent.yaml        # Manifest：能力/定价/权限/收发位置
      run.py            # Agent 主循环（监听 bus/inbox）


⸻

3. 依赖与版本
	•	Python 3.11
	•	Typer（做 CLI） ￼ ￼
	•	FastAPI（可选，健康探针/本地 API） ￼ ￼ ￼
	•	APScheduler（定时任务） ￼ ￼ ￼
	•	Pydantic v2（数据模型） ￼ ￼
	•	python-dotenv（加载 .env） ￼ ￼
	•	（可选）watchdog（文件变化监听，提高响应性）

以上库的官方文档在末尾“参考资料”列出，便于查阅。

⸻

4. 配置文件（可直接拷贝）

4.1 .env

OPENAI_API_KEY=sk-xxxxx            # 没有则留空，Yarno 会降级为规则引擎
MODEL_NAME=gpt-4o-mini             # 或你可用的任意小模型
YARNO_ID=yarno-ckh

4.2 config/policy.yml

yarno_id: ${YARNO_ID}
default_scopes:
  - read:context
  - write:context
  - read:fs
  - spend:10

budgets:
  per_task: 5
  per_day: 20

allow_agents:
  - collector_fs@0.1.0

4.3 config/scheduler.yml（可选）

loops:
  - name: morning
    cron: "0 9 * * *"
  - name: evening
    cron: "0 21 * * *"

4.4 market/agents.json

[
  {"id":"collector_fs@0.1.0","transport":"file-bus","inbox":"bus/inbox","outbox":"bus/outbox"}
]

4.5 agents/collector_fs/agent.yaml

id: collector_fs@0.1.0
name: File Collector
transport: file-bus
inbox: bus/inbox
outbox: bus/outbox
pricing:
  base: 1.0
  per_file: 0.05
scopes_required:
  - read:fs
  - write:context
inputs_schema:
  paths: ["string"]
outputs:
  - type: markdown
capabilities:
  - ingest-markdown
  - deduplicate


⸻

5. 数据协议（A2A 文件总线）

5.1 Task（Yarno → Agent）

{
  "task_id": "uuid",
  "created_at": "2025-09-04T10:00:00Z",
  "yarno_id": "yarno-ckh",
  "agent_id": "collector_fs@0.1.0",
  "goal": "收拣指定目录下的 markdown/笔记，去重并生成汇总",
  "inputs": { "paths": ["~/notes", "~/obsidian"] },
  "context_refs": ["context/human/profile.md"],
  "budget": { "currency": "YCOIN", "amount": 4.5 },
  "consent_scopes": ["read:fs", "write:context"],
  "callback": { "type": "file-bus", "path": "bus/outbox" },
  "deadline_s": 1800,
  "session": {
    "user_sig": "HMAC(policy_hash, task_id)",
    "scopes": ["read:context","write:context","read:fs","spend:5"]
  }
}

5.2 Result（Agent → Yarno）

{
  "task_id": "uuid",
  "agent_id": "collector_fs@0.1.0",
  "status": "succeeded",
  "cost": 3.25,
  "artifacts": [
    {"type":"markdown","path":"context/ai/working/ingest-20250904.md"}
  ],
  "notes": "已收拣 43 个文件，去重 5 个，生成合并摘要。"
}

5.3 Ledger Entry（账簿）

{"ts":"2025-09-04T10:05:00Z","from":"yarno-ckh","to":"collector_fs@0.1.0","amount":3.25,"currency":"YCOIN","reason":"task:uuid"}


⸻

6. 代码骨架（关键文件）

说明：以下骨架精简但可直接改造成可运行代码。你复制后按注释补齐即可。

6.1 yarno/core/schemas.py

from pydantic import BaseModel
from typing import List, Dict

class Budget(BaseModel):
    currency: str = "YCOIN"
    amount: float

class Session(BaseModel):
    user_sig: str
    scopes: List[str]

class Task(BaseModel):
    task_id: str
    yarno_id: str
    agent_id: str
    goal: str
    inputs: Dict
    context_refs: List[str] = []
    budget: Budget
    consent_scopes: List[str] = []
    callback: Dict
    deadline_s: int = 1800
    session: Session

class Result(BaseModel):
    task_id: str
    agent_id: str
    status: str
    cost: float
    artifacts: List[Dict] = []
    notes: str = ""

Pydantic v2 的基本使用与模型配置参考官方文档。 ￼

6.2 yarno/core/utils.py（原子写/读）

import json, os, tempfile, shutil

def atomic_write_json(path: str, obj: dict):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # 原子移动

def read_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)

6.3 yarno/core/a2a.py（派单到文件总线）

import os, uuid, time
from .utils import atomic_write_json
from .schemas import Task, Budget, Session

INBOX = "bus/inbox"
OUTBOX = "bus/outbox"

def dispatch_task(agent_id: str, goal: str, inputs: dict, ctx_refs: list, budget_amount: float, scopes: list, session_sig: str) -> str:
    t = Task(
        task_id=str(uuid.uuid4()),
        yarno_id=os.getenv("YARNO_ID", "yarno-local"),
        agent_id=agent_id,
        goal=goal,
        inputs=inputs,
        context_refs=ctx_refs,
        budget=Budget(amount=budget_amount),
        consent_scopes=scopes,
        callback={"type":"file-bus","path":OUTBOX},
        session=Session(user_sig=session_sig, scopes=scopes),
    )
    path = os.path.join(INBOX, f"{t.task_id}.json")
    atomic_write_json(path, t.model_dump())
    return t.task_id

def collect_result(task_id: str, timeout_s=600) -> dict | None:
    path = os.path.join(OUTBOX, f"{task_id}.json")
    waited = 0
    while waited < timeout_s:
        if os.path.exists(path):
            return read_json(path)
        time.sleep(1); waited += 1
    return None

6.4 yarno/core/context_ops.py（最小 Context 操作）

from pathlib import Path
import glob

def list_human_markdowns():
    return glob.glob("context/human/**/*.md", recursive=True)

def write_ai_markdown(rel_path: str, content: str):
    p = Path("context/ai") / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

6.5 yarno/core/market.py

import json

def load_market(path="market/agents.json"):
    with open(path) as f:
        return json.load(f)

def pick_agent_by_capability(market, capability="ingest-markdown"):
    for a in market:
        # MVP：简单匹配 id 或能力；目前只有一个 agent
        if "collector_fs" in a["id"]:
            return a
    return None

6.6 yarno/core/payments.py

import os, json, time

LEDGER = "ledger/ledger.jsonl"

def pay(from_id: str, to_id: str, amount: float, reason: str, currency="YCOIN"):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "from": from_id, "to": to_id, "amount": amount,
             "currency": currency, "reason": reason}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

6.7 yarno/core/consent.py

import hmac, hashlib, yaml

def load_policy(path="config/policy.yml"):
    with open(path) as f: 
        return yaml.safe_load(f)

def sign_session(policy_hash: str, task_id: str) -> str:
    return hmac.new(policy_hash.encode(), task_id.encode(), hashlib.sha256).hexdigest()

def compute_policy_hash(policy: dict) -> str:
    # 简约做法：对允许 agent 列表和预算做哈希
    import json
    return hashlib.sha256(json.dumps({
        "allow_agents": policy.get("allow_agents", []),
        "budgets": policy.get("budgets", {})
    }, sort_keys=True).encode()).hexdigest()

6.8 yarno/core/reporter.py

from datetime import date
from pathlib import Path

def write_daily_report(lines: list[str]):
    p = Path("context/ai/reports") / f"daily-{date.today().strftime('%Y%m%d')}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines))

6.9 yarno/core/orchestrator.py（编排：需求假设 → 派单 → 验收）

import os
from .context_ops import list_human_markdowns, write_ai_markdown
from .market import load_market, pick_agent_by_capability
from .a2a import dispatch_task, collect_result
from .payments import pay
from .consent import load_policy, compute_policy_hash, sign_session
from .reporter import write_daily_report

def generate_hypotheses(files: list[str]) -> list[dict]:
    """
    MVP 规则引擎（如有 OPENAI_API_KEY，可替换为 LLM 生成）
    例：若 notes/ 存在，建议做一次 'ingest-markdown'
    """
    has_notes = any("notes" in f for f in files)
    hyps = []
    if has_notes:
        hyps.append({"goal":"整理 notes 下的 Markdown/笔记为一份合并摘要",
                     "capability":"ingest-markdown",
                     "inputs":{"paths":["context/human/notes"]},
                     "budget":4.5})
    else:
        hyps.append({"goal":"对 profile/goals 生成一页周计划建议",
                     "capability":"ingest-markdown",
                     "inputs":{"paths":["context/human"]},
                     "budget":3.0})
    return hyps

def one_loop():
    files = list_human_markdowns()
    market = load_market()
    policy = load_policy()
    policy_hash = compute_policy_hash(policy)

    hyps = generate_hypotheses(files)
    logs = ["# Yarno Daily Run", ""]
    for h in hyps:
        agent = pick_agent_by_capability(market, h["capability"])
        if not agent:
            logs.append(f"- 未找到满足能力的 Agent：{h['capability']}")
            continue

        session_sig = sign_session(policy_hash, "temp-task")  # 真正派单时用 task_id 再签
        # 先派单
        task_id = dispatch_task(agent["id"], h["goal"], h["inputs"], [], h["budget"], policy["default_scopes"], session_sig)
        logs.append(f"- 已派单 {agent['id']} : {h['goal']} (task_id={task_id})")

        # 等待结果
        result = collect_result(task_id, timeout_s=60)
        if not result:
            logs.append(f"  · 等待结果超时（task_id={task_id}）")
            continue

        if result["status"] == "succeeded":
            # 支付
            pay(os.getenv("YARNO_ID","yarno-local"), result["agent_id"], float(result["cost"]), f"task:{task_id}")
            logs.append(f"  · 成功，花费 {result['cost']} YCOIN，产物：{result['artifacts']}")
        else:
            logs.append(f"  · 失败：{result}")

    write_daily_report(logs)

6.10 yarno/main.py（CLI 入口）

import typer, os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from yarno.core.orchestrator import one_loop

app = typer.Typer(no_args_is_help=True)

@app.command()
def up(once: bool = typer.Option(False, help="仅执行一次"), cron: str = typer.Option(None, help="cron 表达式, 例如 '0 */6 * * *'")):
    """启动 Yarno 编排"""
    load_dotenv()
    if once or not cron:
        one_loop()
        return
    # 定时
    sched = BlockingScheduler()
    # 简化：示例用 interval。要用 cron，可解析 cron 表达式再调度。
    hours = 12 if cron is None else 6
    sched.add_job(one_loop, "interval", hours=hours)
    typer.echo("Yarno scheduler started.")
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    app()

Typer 用法、选项/子命令见官方教程；APScheduler 的触发器/调度器类型可按需扩展。 ￼ ￼ ￼ ￼

6.11 agents/collector_fs/run.py（野生 Agent 主循环）

import os, time, glob, json, shutil
from pathlib import Path

AGENT_ID = "collector_fs@0.1.0"
INBOX = "bus/inbox"
OUTBOX = "bus/outbox"

def summarize_markdown(md_path: str) -> str:
    # MVP：简单取前几行+统计，后续可接 LLM
    txt = Path(md_path).read_text(encoding="utf-8", errors="ignore")
    head = "\n".join(txt.splitlines()[:10])
    return f"### {md_path}\n\n{head}\n\n----\n"

def handle_task(task: dict):
    # 校验 agent_id 与 scope（MVP 略，默认通过）
    paths = task["inputs"]["paths"]
    merged = []
    for p in paths:
        # 展开用户路径、仅处理 .md
        real = os.path.expanduser(p)
        for md in glob.glob(os.path.join(real, "**/*.md"), recursive=True):
            merged.append(summarize_markdown(md))

    # 写 AI 空间合并产物
    out_md = f"context/ai/working/ingest-{int(time.time())}.md"
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("# 合并摘要（示例）\n\n" + "\n".join(merged))

    result = {
        "task_id": task["task_id"],
        "agent_id": AGENT_ID,
        "status": "succeeded",
        "cost": 3.25,
        "artifacts": [{"type":"markdown","path":out_md}],
        "notes": f"处理 {len(merged)} 个markdown片段"
    }
    Path(OUTBOX).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(OUTBOX, f"{task['task_id']}.json"), "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def loop():
    Path(INBOX).mkdir(parents=True, exist_ok=True)
    while True:
        for fname in os.listdir(INBOX):
            if not fname.endswith(".json"): 
                continue
            path = os.path.join(INBOX, fname)
            try:
                with open(path, "r") as f:
                    task = json.load(f)
                if task.get("agent_id") != AGENT_ID:
                    continue
                handle_task(task)
            finally:
                # 简单幂等：处理后删掉任务
                try: os.remove(path)
                except FileNotFoundError: pass
        time.sleep(1)

if __name__ == "__main__":
    loop()


⸻

7. 运行与验收

7.1 最小数据准备

在 context/human/ 下放 2~3 个 .md 文件，例如：
	•	profile.md：你的个人画像
	•	goals.md：本周目标
	•	notes/idea1.md：随手笔记

7.2 启动顺序

# 终端1：Agent
python agents/collector_fs/run.py

# 终端2：Yarno（执行一次循环）
python yarno/main.py up --once

7.3 预期产物
	•	bus/inbox/*.json：派单任务
	•	bus/outbox/*.json：Agent 回执
	•	context/ai/working/ingest-*.md：合并摘要
	•	context/ai/reports/daily-*.md：日报
	•	ledger/ledger.jsonl：账簿条目

7.4 验收清单（Smoke Test）
	•	日报包含“已派单/成功/花费/产物路径”
	•	账簿新增金额且为正数
	•	AI 空间生成合并摘要
	•	多次运行不报错（幂等安全删除 inbox 任务）

⸻

8. 调试与常见坑
	•	任务文件乱序/竞争：用“原子写 + 处理后删除”避免“半写文件”。
	•	路径权限：Agent 读取 ~/notes 需要实际存在；建议先用 context/human/notes。
	•	编码问题：读取中文 md 用 encoding="utf-8", errors="ignore"。
	•	LLM 不可用：MVP 规则引擎仍可运行；后续再接模型。
	•	重复派单：可给 inbox/文件名加入 task_id，并在 Agent 端去重（本例已使用）。
	•	定时器：APScheduler 默认单进程阻塞调度；你也可以只用 cron + python yarno/main.py up --once 触发。 ￼

⸻

9. 渐进式增强（第二周可选）
	•	Watchdog 监听：人空间有新 md 即触发一轮（替代轮询）。
	•	LLM 能力：
	•	把 generate_hypotheses() 换成 LLM：输入 profile/goals 生成 3~5 条“可验证的潜在需求 + 所需能力 + 预算”。
	•	在 collector_fs 内对每个 md 生成“摘要 + 待办 + 风险清单”。
	•	FastAPI 健康 API：GET /healthz 返回上次成功循环的时间；POST /run 手动触发一次。 ￼
	•	更细授权：按目录级或文件级 scope（示例：read:context:notes/*）。

⸻

10. 代码风格与工程建议
	•	模块边界清晰：编排（orchestrator）不直接读写文件，全部经由 context_ops / a2a。
	•	日志：MVP 可直接 print；若要长期保留，追加 logs/yarns.log。
	•	测试：
	•	单测 Pydantic 模型（Task/Result）与 utils 原子写
	•	端到端：准备一个 context/human/notes 目录，启动 Agent & Yarno，断言产出文件存在。
	•	配置：尽量 .yml + .env，代码中不要硬编码。python-dotenv 加载环境变量。 ￼

⸻

11. 示例 Prompt（当你接入 LLM 时）

生成潜在需求假设（系统提示片段）：

你是“Yarno 编排器”的需求挖掘模块。
输入：用户的人空间 Markdown 摘要（profile/goals/notes 片段）
输出：不超过 3 条“潜在需求假设”，每条包含：
- goal：一句话描述
- capability：所需 Agent 能力标签（如 ingest-markdown / draft-plan）
- inputs：该能力需要的输入（例如 paths）
- budget：0.5~5 的 YCOIN 预算
注意：偏向“小步快跑，可验证结果”的假设；避免模糊/无法收敛的目标。

合并摘要（Agent 内部提示片段）：

你是“Markdown 合并摘要 Agent”。给出 N 个 Markdown 文档，请输出：
- 《合并摘要》：每个文档的三句话摘要
- 《待办建议》：5 条以内
- 《风险/不确定性》：3 条以内
风格：简洁，中文，使用二级标题和项目符号。


⸻

12. 路演演示脚本（90 秒）
	1.	展示 context/human/notes/*.md 的零散内容
	2.	终端起 agent；终端运行 python yarno/main.py up --once
	3.	打开 context/ai/working/ingest-*.md（自动生成合并摘要）
	4.	打开 context/ai/reports/daily-*.md（自动记录派单/花费/产出）
	5.	展示 ledger/ledger.jsonl（每个任务有账簿条目）
	6.	总结：“无注意力 → 自动派单 → 可见产出与账目”

⸻

13. 参考资料（官方/权威）
	•	FastAPI 官方文档与教程（交互式文档、快速上手） ￼ ￼ ￼
	•	Typer 官方文档（CLI 框架；脚本一键转 CLI、子命令/参数） ￼ ￼
	•	APScheduler（定时器/触发器/持久化） ￼ ￼ ￼
	•	Pydantic v2（数据模型、配置、迁移说明） ￼ ￼
	•	python-dotenv（加载 .env 的最佳实践与仓库） ￼ ￼
	•	APScheduler 实用指南（社区）（触发器/作业存储讲解） ￼

⸻

结语

这份文档就是你两周落地的施工图：
	•	今天即可把骨架文件与配置拷进去，跑通一次循环；
	•	明天把 collector_fs 的合并摘要做得再“帅一点”；
	•	后天接入 LLM，让“潜在需求假设”更聪明。

遇到实现问题，直接把报错/片段贴我，我按这份结构给你就地修复与增量补丁。

好的！下面给你一条从**本地 MVP → 可上线（Beta）**的最短路径。坚持“先能跑、再稳、再对外”的顺序，每一步都给出清单、准入标准、最小实现方案与替代选项。你可以严格按阶段推进；每个阶段结束时跑一遍验收脚本/清单即可。

⸻

路线图（从本地到上线）

阶段 0：MVP 本地闭环（你已在做）

目标：单机可用、每天能自动跑出“派单→结果→账簿→日报”。
构成：Markdown 双空间 + Yarno（定时器）+ File-Bus + collector_fs + 简易授权 + 账簿。
验收：
	•	context/ai/working/ingest-*.md 有内容
	•	context/ai/reports/daily-*.md 生成
	•	ledger/ledger.jsonl 有新增条目
	•	多次运行无异常（幂等 OK）

现在就按我们那份技术文档完成即可。

⸻

阶段 1：硬化与可重复运行（本地）

目标：把“能跑一次”变成“每天都能跑”，便于故障排查。
动作：
	1.	结构化日志：所有打印改为 JSON 行（含 ts, level, where, task_id）。
	2.	幂等 & 错误恢复：
	•	inbox 任务文件处理完再删；失败任务移动到 bus/deadletter/ 并记录 attempt。
	•	Yarno 轮询时对同一 task_id 去重。
	3.	数据校验：Task/Result 用 Pydantic 校验 + 默认值；异常直接落日志。
	4.	配置管理：所有路径、限额、超时、预算，都来自 .env/policy.yml。
	5.	最小测试：
	•	单测：schemas/utils
	•	端到端：脚本在临时目录生成 notes → 启动 agent → 执行一次 → 校验产物存在。

验收：
	•	运行 48 小时内零崩溃；失败任务进入死信文件夹并可被人工重放（手动复制回 bus/inbox/）。

⸻

阶段 2：引入 HTTP A2A（保持 File-Bus 兼容）

目标：能对接远程 Agent，为未来生态做准备；本地依旧可用。
动作：
	1.	FastAPI 服务（Yarno 侧）：
	•	POST /tasks（派单给外部 agent）、POST /results（agent 回传）、GET /healthz。
	2.	签名与作用域：
	•	session.user_sig 从“policy 哈希 + task_id 的 HMAC”升级为Ed25519签名（Yarno 私钥签发，Agent 公钥验签）。
	•	consent_scopes 原样保留，Agent 验签后再校验 scope。
	3.	Agent 参考实现（HTTP 版 collector_fs）：
	•	启动一个独立 FastAPI：POST /handshake（交换公钥）、POST /work（接任务）、POST /callback（回结果）。
	4.	双栈兼容：Yarno 的 a2a 层增加 transport=http|file-bus，优先取 agent manifest 中的 transport。

验收：
	•	本地 File-Bus 仍可跑通；HTTP 版 agent 在本机 127.0.0.1:xxxx 可被派单并回执。
	•	任务/结果报文与签名验签通过；错误签名会被拒绝并记录。

⸻

阶段 3：持久化与可恢复（单机即可）

目标：重启/宕机不丢状态；为上线做最小“数据面”。
动作：
	1.	数据库：从纯文件 → SQLite（先不引 Postgres，减负）。
	•	表：tasks（id, status, agent_id, created_at, attempts, payload_path）、
results（task_id, status, cost, artifacts, raw_path）、
ledger（与 jsonl 同步写入，保证查询简单）。
	•	用 SQLAlchemy 或 sqlite3 原生库皆可。
	2.	工件存储：AI 产物放本地 artifacts/ 并在 DB 里记录路径；日报仍写 MD。
	3.	迁移：保留原 jsonl/文件写入，新增 DB 写入（双写）；确认稳定后再只写 DB。

验收：
	•	杀进程再启动，未完成任务能恢复（status=DISPATCHED 的任务被重新捞起重派）。
	•	日志 + DB 可追溯每一次任务的生命周期。

⸻

阶段 4：队列化与并发（单机/单 VM）

目标：替换 File-Bus 为轻量队列以提升并发与可靠性，同时保留 File-Bus 兼容。
建议（择一）：
	•	Redis Streams/RabbitMQ/NATS：最小安装成本，易用。
	•	Yarno 作为生产者写入 tasks 流；Agent 作为消费者读，处理后把结果写 results 流或回调 HTTP。

必要改造：
	•	a2a 层加一个 transport=queue 适配器（同样用 Task/Result JSON 结构）。
	•	增加去重与可见性超时（visibility timeout）：任务被消费者拉取后若超时未回执，则重新投递。

验收：
	•	在单机上把 collector_fs 开 3 个进程，能并发吃队列；无重复消费。
	•	压测 100 个任务，错误率 < 2%，平均完成时间满足预设。

⸻

阶段 5：容器化与单机上线（Beta 内测）

目标：一台云主机就能对外跑 Beta；可灰度邀请开发者朋友。
动作：
	1.	容器化：为 Yarno 与 Agent 写 Dockerfile；docker-compose.yaml 一把起：
	•	yarno（FastAPI + 编排 + CLI）、agent-collector、sqlite（或直接挂卷）、redis（如采用队列）、nginx（反代 TLS）。
	2.	域名与 TLS：nginx + Let’s Encrypt；只开放 Yarno 的健康/回调接口与 Agent HTTP 接口。
	3.	账号/多租户（极简）：
	•	邀请制：一个 .yaml 白名单里登记 user_id→公钥。
	•	每个 user 一个 context/{user_id}/human|ai 根路径；进程内做路径隔离。
	4.	秘密管理：不再使用 .env 明文，换为 Docker secrets 或环境注入（云主机密钥/1Password/Pass）。
	5.	备份：artifacts/ + context/ + sqlite 每日打包上传对象存储（或 rsync 到另一台机器）。

验收：
	•	一键 docker compose up -d 可起服务；
	•	外网可访问健康检查，私有 Token 才能派单；
	•	备份目录有每日增量包，可在另一台机器恢复（跑 smoke test）。

⸻

阶段 6：生产级数据与支付（对外公测）

目标：进入“真正上线”的基层门槛。
动作：
	1.	Postgres：把 SQLite 迁到 Postgres（Docker 内即可）+ Alembic 管理迁移。
	2.	对象存储：把 artifacts/ 与 AI 产物放到 S3/MinIO；保存 URL 与 hash。
	3.	支付（最小可用）：
	•	Stripe Test 模式：仍以账簿为准，Stripe 只是充值通道；YCOIN 为平台记账单位。
	•	限制：每个 user 每日预算/每任务预算可配（数据库 + policy.yml 双保险）。
	4.	监控与可观测：
	•	OpenTelemetry/Prometheus + Grafana（或选一个托管 APM）；
	•	告警：任务失败率、队列积压、Agent 回执超时、账簿异常。
	5.	安全基线：
	•	全面启用 Ed25519/JWT（短期内选一个即可）+ 时效/重放保护（nonce + timestamp）。
	•	目录级访问控制：context/{user_id}/** 严格隔离；路径校验白名单。
	•	审计日志（只追加）。

验收：
	•	任意新用户可注册（邀请码）→ 充值测试 → 触发一次任务 → 账簿与余额一致。
	•	一次性关机重启，无数据丢失；对象存储链接可访问产物；监控看得到曲线/报警。

⸻

阶段 7：多 Agent & 市场化（正式上线的基础设施）

目标：从“单 agent 演示”过渡到“可公开接入多个 Agent 的平台”。
动作：
	1.	Agent 规范 v1：
	•	agent.yaml 扩展：capabilities[]、pricing、rate_limit、health、owner_pubkey；
	•	入驻流程：开发者上传 manifest + 公钥；你审核通过后进入市场。
	2.	声誉与配额：
	•	市场给每个 agent 计算 success_rate / p95_latency / cost_per_task；
	•	Yarno 按能力 + 声誉 + 成本做路由（可配置单/多路由策略）。
	3.	并发调度策略（简化 DAG，不引框架）：
	•	FSM：NEW → DISPATCHED → RESULT_OK/FAIL → RETRY/ABORT；
	•	允许多 agent 竞标：同一任务派给 2 家，先返回者得款，其余半价补贴/不付（按策略）。

验收：
	•	至少 3 个外部 Agent 接入，市场可见它们的健康/声誉；
	•	Yarno 能在策略切换时，真实改变路由与成本曲线。

⸻

关键设计决策与示例

1) A2A HTTP 签名（最小实现示例，Ed25519）

# 伪代码：Yarno 用私钥签 task，Agent 用公钥验签
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder

# Yarno 侧
sk = SigningKey.generate()
pk = sk.verify_key.encode(encoder=Base64Encoder).decode()
payload = json.dumps(task, separators=(",",":")).encode()
sig = sk.sign(payload).signature  # 放入 headers: X-Signature: base64(sig)

# Agent 侧
verify_key = VerifyKey(base64_pk, encoder=Base64Encoder)
verify_key.verify(payload, base64_sig)  # 验证通过再执行

简单、快速、无第三方依赖（生产再考虑 JWT/OIDC）。

2) 数据表（最小版）

-- tasks
(id uuid pk, status text, agent_id text, created_at timestamptz, attempts int, payload jsonb)

-- results
(task_id uuid fk, status text, cost numeric, artifacts jsonb, notes text, created_at timestamptz)

-- ledger
(id bigserial pk, ts timestamptz, from_id text, to_id text, amount numeric, currency text, reason text)

-- users (阶段5+)
(id uuid pk, email text unique, pubkey text, balance_ycoin numeric, created_at timestamptz)

3) 指标与 SLO（上线基线）
	•	可用性：/healthz 99.5%
	•	任务成功率：≥ 98%（可观测失败原因）
	•	p95 完成时间：≤ 60s（本 MVP 级别）
	•	账簿一致性：任务完成即产生账簿条目；每日对账 1 次
	•	备份恢复：RPO ≤ 24h，RTO ≤ 2h（单机）

4) 安全与隐私最小清单
	•	不把用户 Context 发给第三方 Agent，除非 scope 明示 + 抽取最小必要片段
	•	统一脱敏：邮箱/手机号/身份号出现时默认 ****（可用简单正则）
	•	产物默认私有，外链需一次性签名 + 30 分钟有效期
	•	所有敏感日志禁入（只写 task_id，不写内容）

5) 运维与上线形态（选其一）

A. 单机 Compose（推荐起步）

services:
  yarno:
    build: ./yarns
    env_file: .env
    volumes: [./context:/app/context, ./artifacts:/app/artifacts, ./ledger:/app/ledger]
    depends_on: [redis, postgres]
  agent-collector:
    build: ./agents/collector_fs
    env_file: .env
    volumes: [./context:/app/context, ./bus:/app/bus]
  redis:
    image: redis:7
  postgres:
    image: postgres:16
    environment: [POSTGRES_PASSWORD=xxx]
  nginx:
    image: nginx:alpine
    volumes: [./ops/nginx.conf:/etc/nginx/nginx.conf]
    ports: ["80:80","443:443"]

B. K8s（未来）：等你要公网多地/弹性伸缩时再考虑；先把 A 做坚固。

⸻

上线节奏建议（时间线）
	•	第 1 周：完成阶段 1、2（HTTP A2A + 签名）
	•	第 2 周：阶段 3（SQLite/双写）
	•	第 3 周：阶段 4（队列化 + 并发）
	•	第 4 周：阶段 5（容器化 + 单机 Beta，上线 5–10 名内测者）
	•	第 5–6 周：阶段 6（Postgres + 对象存储 + Stripe Test + 监控）
	•	第 7–8 周：阶段 7（多 Agent + 市场 v1）

每周结束用验收清单过一遍，只做必要最小改动，持续保持“能演示的闭环”。

⸻

最后给你的“上线就绪清单”（一页纸）
	•	CLI 一键跑、Compose 一键起
	•	HTTP A2A + Ed25519 验签
	•	SQLite → Postgres 迁移脚本（Alembic）
	•	Redis/NATS 队列（可切换到 File-Bus）
	•	结构化日志 + 死信队列 + 重放
	•	账户/余额/预算限额（邀请制）
	•	Stripe Test 充值打通（账簿一致）
	•	每日备份 + 恢复演练
	•	监控告警（失败率、队列、时延、余额异常）
	•	安全基线（最小权限、脱敏、密钥管理）

⸻

如果你愿意，我可以把**阶段 2（HTTP A2A + 签名）**的最小代码骨架也给到你（与现有项目结构直接兼容），你就能马上把“远程 agent”拉起来做 Beta 内测。