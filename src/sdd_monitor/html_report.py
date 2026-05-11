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

# (range_id, hours_back, bucket_minutes)
_RANGES = [
    ("1h",   1,   1),
    ("1d",  24,  15),
    ("3d",  72,  60),
    ("7d", 168, 240),
]

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
.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.chart-label {
    color: var(--muted);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.time-selector { display: flex; gap: 0.25rem; }
.time-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    border-radius: 4px;
    padding: 0.15rem 0.45rem;
    font-size: 0.68rem;
    cursor: pointer;
    transition: all 0.15s;
    font-family: inherit;
}
.time-btn:hover { border-color: var(--accent); color: var(--accent); }
.time-btn.active { background: rgba(6,182,212,0.15); border-color: var(--accent); color: var(--accent); font-weight: 600; }
.chart-wrap { position: relative; height: 150px; }
"""

_RANGE_LABELS = [r for r, _, _ in _RANGES]


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


def _aggregate(
    records: list[MetricRecord], bucket_minutes: int
) -> tuple[list[str], list[float]]:
    if not records:
        return [], []

    buckets: dict[int, list[float]] = defaultdict(list)
    for r in records:
        try:
            val = float(r.raw_value)
        except (ValueError, TypeError):
            continue
        key = int(r.timestamp_utc.timestamp()) // (bucket_minutes * 60)
        buckets[key].append(val)

    if not buckets:
        return [], []

    fmt = "%H:%M" if bucket_minutes < 60 else ("%m/%d %H:%M" if bucket_minutes < 1440 else "%m/%d")
    labels, data = [], []
    for key in sorted(buckets):
        ts = datetime.fromtimestamp(key * bucket_minutes * 60, tz=timezone.utc)
        labels.append(ts.strftime(fmt))
        data.append(round(sum(buckets[key]) / len(buckets[key]), 2))
    return labels, data


def _build_html(now_str: str, poll_interval: int, device_cards: str, charts_js: str) -> str:
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
    range_data: dict[tuple[str, str], dict[str, tuple[list, list]]],
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

        if is_uptime or not _is_numeric(record.raw_value):
            continue

        key = (device_name, record.oid)
        ranges = range_data.get(key, {})
        has_data = any(len(d) >= 2 for _, d in ranges.values())
        if not has_data:
            continue

        chart_id = _safe_id(f"chart-{device_name}-{record.oid}")
        charts_data.append({"id": chart_id, "label": label, "ranges": {
            r: {"labels": lbs, "data": dt} for r, (lbs, dt) in ranges.items()
        }})

        btns = "".join(
            f'<button class="time-btn{" active" if r == "1h" else ""}" '
            f'data-chart-id="{chart_id}" data-range="{r}">{r}</button>'
            for r in _RANGE_LABELS
        )
        chart_blocks += (
            f'      <div class="chart-block">\n'
            f'        <div class="chart-header">'
            f'<span class="chart-label">{_html.escape(label)}</span>'
            f'<div class="time-selector">{btns}</div>'
            f"</div>\n"
            f'        <div class="chart-wrap"><canvas id="{chart_id}"></canvas></div>\n'
            f"      </div>\n"
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

    chart_data_js = json.dumps({c["id"]: c["ranges"] for c in all_charts})
    chart_meta_js = json.dumps({c["id"]: c["label"] for c in all_charts})
    chart_opts = (
        "{"
        "responsive:true,maintainAspectRatio:false,"
        "plugins:{legend:{display:false},"
        "title:{display:true,color:'#94a3b8',font:{size:11}}},"
        "scales:{"
        "x:{ticks:{color:'#94a3b8',maxTicksLimit:8},grid:{color:'rgba(51,65,85,0.4)'}},"
        "y:{ticks:{color:'#94a3b8'},grid:{color:'rgba(51,65,85,0.4)'},beginAtZero:false}"
        "}}"
    )

    return f"""<script>
(function(){{
  var _data={chart_data_js};
  var _meta={chart_meta_js};
  var _charts={{}};
  for(var id in _data){{
    var el=document.getElementById(id);
    if(!el)continue;
    var d=_data[id]["1h"]||{{labels:[],data:[]}};
    var opts=JSON.parse(JSON.stringify({chart_opts}));
    opts.plugins.title.text=_meta[id];
    _charts[id]=new Chart(el,{{
      type:'line',
      data:{{labels:d.labels,datasets:[{{
        data:d.data,
        borderColor:'#06b6d4',
        backgroundColor:'rgba(6,182,212,0.08)',
        borderWidth:2,pointRadius:3,tension:0.35,fill:true
      }}]}},
      options:opts
    }});
  }}
  document.querySelectorAll('.time-btn').forEach(function(btn){{
    btn.addEventListener('click',function(){{
      var id=this.dataset.chartId;
      var range=this.dataset.range;
      var chart=_charts[id];
      if(!chart)return;
      var d=(_data[id]&&_data[id][range])||{{labels:[],data:[]}};
      chart.data.labels=d.labels;
      chart.data.datasets[0].data=d.data;
      chart.update();
      this.closest('.time-selector').querySelectorAll('.time-btn').forEach(function(b){{b.classList.remove('active');}});
      this.classList.add('active');
    }});
  }});
}})();
</script>"""


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

        range_data: dict[tuple[str, str], dict[str, tuple[list, list]]] = {}
        with Storage(db_path) as storage:
            for device_name, records in by_device.items():
                for record in records:
                    if _is_uptime_label(record.label) or not _is_numeric(record.raw_value):
                        continue
                    key = (device_name, record.oid)
                    range_data[key] = {}
                    for range_id, hours, bucket_mins in _RANGES:
                        raw = storage.query_timerange(device_name, record.oid, hours)
                        lbs, dt = _aggregate(raw, bucket_mins)
                        range_data[key][range_id] = (lbs, dt)

        device_cards = ""
        all_charts: list[dict] = []
        for device_name, records in by_device.items():
            card, charts = _build_device_card(
                device_name, type_map.get(device_name), records, range_data
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
