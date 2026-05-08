import html as _html
import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sdd_monitor.models import MetricRecord
from sdd_monitor.storage import Storage

logger = logging.getLogger(__name__)

N_HISTORY = 20

_ICONS: dict[str, str] = {
    "switch": "🔀",
    "router": "🌐",
    "server": "🖥️",
    "firewall": "🔒",
}
_DEFAULT_ICON = "📡"

_CSS = """
:root {
    --bg: #0f172a;
    --surface: #1e293b;
    --border: #334155;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #06b6d4;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    min-height: 100vh;
    padding: 1.5rem;
}
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1.25rem;
    border-bottom: 1px solid var(--border);
}
h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
.header-meta { color: var(--muted); font-size: 0.8rem; margin-top: 0.3rem; }
.refresh-badge {
    background: rgba(6,182,212,0.12);
    color: var(--accent);
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 9999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 500;
}
.devices-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
    gap: 1.5rem;
}
.device-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 1rem;
    padding: 1.5rem;
    transition: border-color 0.2s;
}
.device-card:hover { border-color: var(--accent); }
.device-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}
.device-icon { font-size: 1.75rem; line-height: 1; }
.device-name { font-size: 1.125rem; font-weight: 600; }
.metrics-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    margin-bottom: 1rem;
}
.metrics-table th {
    text-align: left;
    padding: 0.35rem 0.6rem;
    color: var(--muted);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    border-bottom: 1px solid var(--border);
}
.metrics-table td {
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid rgba(51,65,85,0.4);
    vertical-align: middle;
}
.metrics-table tr:last-child td { border-bottom: none; }
.val { color: var(--accent); font-family: 'Menlo','Monaco',monospace; font-weight: 500; }
.ts  { color: var(--muted); font-size: 0.78rem; }
.chart-block { margin-top: 1.25rem; }
.chart-label {
    color: var(--muted);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}
.chart-wrap { position: relative; height: 150px; }
"""


def _safe_id(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", s)


def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _is_uptime_label(label: str | None) -> bool:
    return bool(label and "uptime" in label.lower())


def _format_uptime(centiseconds: str) -> str:
    try:
        total_seconds = int(centiseconds) // 100
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    except (ValueError, TypeError):
        return centiseconds


def _build_html(
    now_str: str,
    poll_interval: int,
    device_cards: str,
    charts_js: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="{poll_interval}">
  <title>SDD Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>{_CSS}</style>
</head>
<body>
  <header>
    <div>
      <h1>SDD Monitor</h1>
      <p class="header-meta">Actualizado: {_html.escape(now_str)}</p>
    </div>
    <span class="refresh-badge">↻ {poll_interval}s</span>
  </header>
  <main class="devices-grid">
{device_cards}
  </main>
{charts_js}
</body>
</html>"""


def _build_device_card(
    device_name: str,
    device_type: str | None,
    records: list[MetricRecord],
    history_map: dict[tuple[str, str], list[MetricRecord]],
) -> tuple[str, list[dict]]:
    icon = _ICONS.get(device_type or "", _DEFAULT_ICON)
    rows = ""
    chart_blocks = ""
    charts_data: list[dict] = []

    for record in records:
        label = record.label or record.oid
        is_uptime = _is_uptime_label(record.label)
        display_value = _format_uptime(record.raw_value) if is_uptime else record.raw_value
        rows += (
            f"        <tr>"
            f"<td>{_html.escape(label)}</td>"
            f"<td class='val'>{_html.escape(display_value)}</td>"
            f"<td class='ts'>{record.timestamp_utc.strftime('%H:%M:%S')} UTC</td>"
            f"</tr>\n"
        )

        if not is_uptime and _is_numeric(record.raw_value):
            history = history_map.get((device_name, record.oid), [])
            if len(history) >= 2:
                chart_id = _safe_id(f"chart-{device_name}-{record.oid}")
                labels = [r.timestamp_utc.strftime("%H:%M") for r in history]
                data = [float(r.raw_value) for r in history]
                charts_data.append({"id": chart_id, "labels": labels, "data": data, "label": label})
                chart_blocks += (
                    f'      <div class="chart-block">'
                    f'<div class="chart-label">{_html.escape(label)}</div>'
                    f'<div class="chart-wrap"><canvas id="{chart_id}"></canvas></div>'
                    f"</div>\n"
                )

    card = (
        f'    <section class="device-card">\n'
        f'      <div class="device-header">'
        f'<span class="device-icon">{icon}</span>'
        f'<span class="device-name">{_html.escape(device_name)}</span>'
        f"</div>\n"
        f'      <table class="metrics-table">\n'
        f"        <thead><tr><th>Métrica</th><th>Valor</th><th>Timestamp</th></tr></thead>\n"
        f"        <tbody>\n{rows}        </tbody>\n"
        f"      </table>\n"
        f"{chart_blocks}"
        f"    </section>\n"
    )
    return card, charts_data


def _build_charts_js(all_charts: list[dict]) -> str:
    if not all_charts:
        return ""
    parts = ["<script>"]
    for c in all_charts:
        parts.append(
            f"new Chart(document.getElementById({json.dumps(c['id'])}),{{"
            f"type:'line',"
            f"data:{{"
            f"labels:{json.dumps(c['labels'])},"
            f"datasets:[{{"
            f"data:{json.dumps(c['data'])},"
            f"label:{json.dumps(c['label'])},"
            f"borderColor:'#06b6d4',"
            f"backgroundColor:'rgba(6,182,212,0.08)',"
            f"borderWidth:2,pointRadius:3,tension:0.35,fill:true"
            f"}}]}},"
            f"options:{{"
            f"responsive:true,maintainAspectRatio:false,"
            f"plugins:{{legend:{{display:false}},title:{{display:true,text:{json.dumps(c['label'])},color:'#94a3b8',font:{{size:11}}}}}},"
            f"scales:{{"
            f"x:{{ticks:{{color:'#94a3b8',maxTicksLimit:6}},grid:{{color:'rgba(51,65,85,0.4)'}}}},"
            f"y:{{ticks:{{color:'#94a3b8'}},grid:{{color:'rgba(51,65,85,0.4)'}},beginAtZero:false}}"
            f"}}}}}})"
        )
    parts.append("</script>")
    return "\n".join(parts)


def generate(
    metrics: list[MetricRecord],
    devices: list[dict],
    db_path: Path,
    html_path: Path,
    poll_interval: int,
) -> None:
    try:
        type_map = {d["name"]: d.get("type") for d in devices}

        by_device: dict[str, list[MetricRecord]] = defaultdict(list)
        for r in metrics:
            by_device[r.device_name].append(r)

        history_map: dict[tuple[str, str], list[MetricRecord]] = {}
        with Storage(db_path) as storage:
            for device_name, records in by_device.items():
                for record in records:
                    key = (device_name, record.oid)
                    history_map[key] = storage.query_recent(device_name, record.oid, N_HISTORY)

        device_cards = ""
        all_charts: list[dict] = []
        for device_name, records in by_device.items():
            card, charts = _build_device_card(
                device_name,
                type_map.get(device_name),
                records,
                history_map,
            )
            device_cards += card
            all_charts.extend(charts)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        html_content = _build_html(now_str, poll_interval, device_cards, _build_charts_js(all_charts))

        html_path = Path(html_path)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = html_path.with_suffix(".tmp")
        tmp.write_text(html_content, encoding="utf-8")
        tmp.replace(html_path)

    except Exception as exc:
        logger.error("Error generando reporte HTML en %s: %s", html_path, exc)
