from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table
from rich import box

from sdd_monitor.models import LivenessRecord, MetricRecord

console = Console()


def render(
    records: list[MetricRecord],
    errors: dict[str, str] | None = None,
    liveness: list[LivenessRecord] | None = None,
) -> None:
    errors = errors or {}
    liveness = liveness or []

    if errors:
        for device_name, reason in errors.items():
            console.print(
                f"[bold red]✗ {device_name}[/bold red]: {reason}"
            )

    if records:
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
    elif not errors:
        console.print("[yellow]Sin métricas disponibles.[/yellow]")

    if liveness:
        live = Table(
            title=f"Liveness AP — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
            box=box.ROUNDED,
            show_lines=True,
        )
        live.add_column("Dispositivo", style="cyan", no_wrap=True)
        live.add_column("Estado", style="bold")
        live.add_column("RTT (ms)", style="green")
        live.add_column("HTTPS 443", style="magenta")
        live.add_column("Timestamp UTC", style="dim", no_wrap=True)
        live.add_column("Error", style="red")

        for row in liveness:
            live.add_row(
                row.device_name,
                "UP" if row.is_up else "DOWN",
                f"{row.ping_rtt_ms:.2f}" if row.ping_rtt_ms is not None else "-",
                "UP" if row.https_up else "DOWN",
                row.timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                row.error or "-",
            )
        console.print(live)
    else:
        console.print("[dim]Sin datos de liveness AP.[/dim]")
