import typer
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from yarno.core.orchestrator import one_loop

def main(
    once: bool = typer.Option(False, help="仅执行一次"),
    cron: str = typer.Option(None, help="cron 表达式, 示例 '0 */6 * * *'")
):
    """
    启动 Yarno 编排（Day1：只发布标书与写日报）
    用法示例：
      python -m yarno.main --once
      python -m yarno.main --cron "0 */6 * * *"
    """
    load_dotenv()
    if once or not cron:
        one_loop()
        return
    sched = BlockingScheduler()
    sched.add_job(one_loop, "interval", hours=6)
    typer.echo("Yarno scheduler started.")
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    typer.run(main)