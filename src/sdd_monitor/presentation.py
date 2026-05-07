from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table
from rich import box

from sdd_monitor.models import MetricRecord

console = Console()


def render(records: list[MetricRecord], errors: dict[str, str] | None = None) -> None:
    errors = errors or {}

    if errors:
        for device_name, reason in errors.items():
            console.print(
                f"[bold red]✗ {device_name}[/bold red]: {reason}"
            )

    if not records:
        if not errors:
            console.print("[yellow]Sin métricas disponibles.[/yellow]")
        return

    table = Table(
        title=f"Métricas SNMP — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Dispositivo", style="cyan", no_wrap=True)
    table.add_column("OID", style="dim")
    table.add_column("Valor", style="green")
    table.add_column("Timestamp UTC", style="magenta", no_wrap=True)

    for record in records:
        table.add_row(
            record.device_name,
            record.oid,
            record.raw_value,
            record.timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
        )

    console.print(table)
