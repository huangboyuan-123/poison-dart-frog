"""
SQLAgent CLI 入口模块。

用法:
    sqlagent                          # 交互式模式
    sqlagent query "你的问题"          # 单次查询
    sqlagent --help                   # 显示帮助
"""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from . import __version__
from .agent import SQLAgent
from .config import config

console = Console()


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="sqlagent",
        description="🤖 AI SQL Agent — 用自然语言查询数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  sqlagent                                  # 启动交互式对话
  sqlagent query "所有用户的注册时间"        # 单次查询
  sqlagent query --db sqlite:///mydb.db "..."  # 指定数据库
  sqlagent schema                           # 查看数据库结构
  sqlagent test                             # 测试连接
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"sqlagent v{__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # query 子命令
    query_parser = subparsers.add_parser("query", help="执行自然语言查询")
    query_parser.add_argument("question", help="自然语言问题")
    query_parser.add_argument(
        "--db", dest="database_url", default=None, help="数据库连接 URL"
    )
    query_parser.add_argument(
        "--model", default=None, help="LLM 模型名称"
    )
    query_parser.add_argument(
        "--stream", action="store_true", help="流式输出"
    )

    # schema 子命令
    subparsers.add_parser("schema", help="查看数据库表结构")

    # test 子命令
    subparsers.add_parser("test", help="测试数据库和 LLM 连接")

    return parser


def cmd_query(args: argparse.Namespace) -> None:
    """处理 query 子命令。"""
    agent = SQLAgent(
        database_url=args.database_url,
        model=args.model,
    )

    with console.status("[bold green]正在处理查询..."):
        if args.stream:
            for event in agent.stream(args.question):
                console.log(event)
        else:
            result = agent.run(args.question)

    console.print()
    console.print(Panel(result, title="查询结果", border_style="green"))


def cmd_schema() -> None:
    """处理 schema 子命令。"""
    agent = SQLAgent()
    schema = agent.db.get_schema()

    console.print()
    console.print(Panel(schema, title="数据库结构", border_style="blue"))


def cmd_test() -> None:
    """处理 test 子命令。"""
    agent = SQLAgent()

    with console.status("[bold yellow]正在测试连接..."):
        results = agent.test_connection()

    console.print()
    for name, status in results.items():
        icon = "✅" if status else "❌"
        color = "green" if status else "red"
        console.print(f"  {icon} [{color}]{name}[/{color}]: {'正常' if status else '失败'}")


def interactive_mode() -> None:
    """交互式对话模式。"""
    console.print()
    console.print(
        Panel(
            f"[bold cyan]🤖 SQLAgent v{__version__}[/bold cyan]\n\n"
            "输入自然语言问题来查询数据库。\n"
            "输入 [yellow]:quit[/yellow] 或 [yellow]:q[/yellow] 退出\n"
            "输入 [yellow]:schema[/yellow] 查看数据库结构\n"
            "输入 [yellow]:clear[/yellow] 清除对话记忆",
            title="欢迎",
            border_style="cyan",
        )
    )

    agent = SQLAgent()

    while True:
        try:
            user_input = console.input("\n[bold green]你:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]再见！[/yellow]")
            break

        if not user_input:
            continue

        # 处理特殊命令
        if user_input.lower() in (":quit", ":q", "exit", "quit"):
            console.print("[yellow]再见！[/yellow]")
            break

        if user_input.lower() == ":schema":
            schema = agent.db.get_schema()
            console.print(Panel(schema, title="数据库结构", border_style="blue"))
            continue

        if user_input.lower() == ":clear":
            agent.clear_memory()
            console.print("[yellow]对话记忆已清除。[/yellow]")
            continue

        # 执行查询
        with console.status("[bold green]思考中..."):
            result = agent.run(user_input)

        console.print()
        console.print(Panel(Markdown(result), title="Agent", border_style="green"))


def main():
    """主入口函数。"""
    # 检测是否有管道输入（跳过参数解析）
    if not sys.stdin.isatty():
        question = sys.stdin.read().strip()
        if question:
            agent = SQLAgent()
            result = agent.run(question)
            console.print(result)
            return

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "query":
        cmd_query(args)
    elif args.command == "schema":
        cmd_schema()
    elif args.command == "test":
        cmd_test()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
