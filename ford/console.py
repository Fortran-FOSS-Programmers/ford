from rich.console import Console
from rich.markup import escape

console = Console()


def warn(msg: str):
    console.print(f"[bold red]Warning:[/] {escape(msg)}")
