import html as _html
import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sdd_monitor.models import LivenessRecord, MetricRecord
from sdd_monitor.storage import Storage

logger = logging.getLogger(__name__)

_TZ_MX = timezone(timedelta(hours=-6))

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
    "ap": "📶",
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
.error-card { border-color: #ef4444; }
.error-card:hover { border-color: #f87171; }
.error-badge {
    background: rgba(239,68,68,0.12);
    color: #ef4444;
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 9999px;
    padding: 0.2rem 0.6rem;
    font-size: 0.7rem;
    font-weight: 600;
    margin-left: auto;
}
.error-msg {
    color: #f87171;
    font-size: 0.8rem;
    font-family: 'Menlo','Monaco',monospace;
    margin-top: 0.5rem;
    word-break: break-all;
    line-height: 1.5;
}
.device-card { cursor: pointer; }
#back-btn {
    display: none;
    position: fixed;
    top: 1rem;
    right: 1.5rem;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 0.5rem;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    cursor: pointer;
    z-index: 100;
    font-family: inherit;
    transition: border-color 0.2s, color 0.2s;
}
#back-btn:hover { border-color: var(--accent); color: var(--accent); }
.focus-mode #back-btn { display: block; }
.focus-mode .device-card { display: none; }
.focus-mode .device-card.focused { display: block; }
.iface-btn {
    display: none;
    margin-top: 1rem;
    background: rgba(6,182,212,0.1);
    border: 1px solid var(--accent);
    color: var(--accent);
    border-radius: 0.5rem;
    padding: 0.4rem 1rem;
    font-size: 0.8rem;
    cursor: pointer;
    font-family: inherit;
    transition: background 0.15s;
}
.focus-mode .device-card.focused .iface-btn { display: inline-block; }
.iface-btn:hover { background: rgba(6,182,212,0.2); }
.iface-btn:disabled { opacity: 0.5; cursor: wait; }
.iface-result { margin-top: 1rem; }
.iface-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    margin-top: 0.5rem;
}
.iface-table th {
    text-align: left;
    padding: 0.35rem 0.6rem;
    color: var(--muted);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    border-bottom: 1px solid var(--border);
}
.iface-table td {
    padding: 0.45rem 0.6rem;
    border-bottom: 1px solid rgba(51,65,85,0.4);
}
.iface-table tr:last-child td { border-bottom: none; }
.iface-total { font-weight: 700; color: var(--accent); font-family: 'Menlo','Monaco',monospace; }
.iface-table tr.status-down td { color: rgba(239,68,68,0.85); }
.iface-error { color: #f87171; font-size: 0.82rem; margin-top: 0.5rem; }
.ap-status-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(120px, 1fr));
    gap: 0.5rem;
    margin-top: 0.5rem;
}
.ap-status-item {
    background: rgba(15,23,42,0.35);
    border: 1px solid rgba(51,65,85,0.5);
    border-radius: 0.5rem;
    padding: 0.45rem 0.6rem;
    font-size: 0.8rem;
}
.ap-status-item .label { color: var(--muted); font-size: 0.72rem; display: block; margin-bottom: 0.2rem; }
.ap-status-item .value { color: var(--text); font-weight: 600; }
.status-up { color: #22c55e; font-weight: 600; }
.status-down { color: #ef4444; font-weight: 600; }
.recent-down-badge {
    margin-left: auto;
    background: rgba(245,158,11,0.18);
    border: 1px solid rgba(245,158,11,0.45);
    color: #fbbf24;
    border-radius: 9999px;
    padding: 0.2rem 0.6rem;
    font-size: 0.7rem;
    font-weight: 600;
}
.ap-liveness-detail { display: block; margin-top: 1rem; }
.liveness-chart-wrap { position: relative; height: 150px; margin-top: 0.6rem; }
.muted-note { color: var(--muted); font-size: 0.82rem; }
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
    records: list[MetricRecord],
    bucket_minutes: int,
    start_time: datetime | None = None,
) -> tuple[list[str], list[float | None]]:
    buckets: dict[int, list[float]] = {}
    for r in records:
        try:
            val = float(r.raw_value)
        except (ValueError, TypeError):
            continue
        key = int(r.timestamp_utc.timestamp()) // (bucket_minutes * 60)
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(val)

    if start_time is not None:
        now = datetime.now(timezone.utc)
        start_key = int(start_time.timestamp()) // (bucket_minutes * 60)
        end_key = int(now.timestamp()) // (bucket_minutes * 60)
        all_keys: list[int] = list(range(start_key, end_key + 1))
    else:
        if not buckets:
            return [], []
        all_keys = sorted(buckets.keys())

    fmt = "%H:%M" if bucket_minutes < 60 else ("%m/%d %H:%M" if bucket_minutes < 1440 else "%m/%d")
    labels: list[str] = []
    data: list[float | None] = []
    for key in all_keys:
        ts = datetime.fromtimestamp(key * bucket_minutes * 60, tz=_TZ_MX)
        labels.append(ts.strftime(fmt))
        if key in buckets:
            data.append(round(sum(buckets[key]) / len(buckets[key]), 2))
        else:
            data.append(None)
    return labels, data


def _build_interfaces_js() -> str:
    return """<script>
(function(){
  document.querySelectorAll('.iface-btn').forEach(function(btn){
    btn.addEventListener('click',function(e){
      e.stopPropagation();
      var device=btn.dataset.device;
      var result=btn.parentElement.querySelector('.iface-result');
      btn.disabled=true;
      btn.textContent='Cargando\u2026';
      result.innerHTML='';
      fetch('/cgi-bin/interfaces.py?device='+encodeURIComponent(device))
        .then(function(r){return r.json();})
        .then(function(data){
          if(data.error){
            result.innerHTML='<p class="iface-error">Error: '+data.error+'</p>';
            btn.textContent='\u21ba Reintentar';btn.disabled=false;return;
          }
          function fmtBytes(gb){
            if(gb>=1000)return (gb/1024).toFixed(2)+' TB';
            return gb.toFixed(2)+' GB';
          }
          var rows=data.interfaces.map(function(iface){
            var cls=iface.status==='down'?' class="status-down"':'';
            return '<tr'+cls+'>'
              +'<td>'+iface.name+'</td>'
              +'<td>'+(iface.alias||'\u2014')+'</td>'
              +'<td>'+fmtBytes(iface.in_gb)+'</td>'
              +'<td>'+fmtBytes(iface.out_gb)+'</td>'
              +'<td class="iface-total">'+fmtBytes(iface.total_gb)+'</td>'
              +'<td>'+(iface.status==='up'?'🟢 up':'🔴 down')+'</td>'
              +'</tr>';
          }).join('');
          result.innerHTML='<table class="iface-table"><thead><tr>'
            +'<th>Interfaz</th><th>Descripci\u00f3n</th>'
            +'<th>In (GB)</th><th>Out (GB)</th><th>Total (GB)</th><th>Estado</th>'
            +'</tr></thead><tbody>'+rows+'</tbody></table>';
          btn.textContent='\u21ba Actualizar';btn.disabled=false;
        })
        .catch(function(err){
          result.innerHTML='<p class="iface-error">Error de conexi\u00f3n: '+err.message+'</p>';
          btn.textContent='\u21ba Reintentar';btn.disabled=false;
        });
    });
  });
})();
</script>"""


def _aggregate_liveness(
    records: list[LivenessRecord],
    bucket_minutes: int,
    start_time: datetime,
) -> tuple[list[str], list[int | None]]:
    buckets: dict[int, list[int]] = {}
    for r in records:
        key = int(r.timestamp_utc.timestamp()) // (bucket_minutes * 60)
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(1 if r.is_up else 0)

    now = datetime.now(timezone.utc)
    start_key = int(start_time.timestamp()) // (bucket_minutes * 60)
    end_key = int(now.timestamp()) // (bucket_minutes * 60)
    all_keys = list(range(start_key, end_key + 1))

    fmt = "%H:%M" if bucket_minutes < 60 else ("%m/%d %H:%M" if bucket_minutes < 1440 else "%m/%d")
    labels: list[str] = []
    data: list[int | None] = []
    for key in all_keys:
        ts = datetime.fromtimestamp(key * bucket_minutes * 60, tz=_TZ_MX)
        labels.append(ts.strftime(fmt))
        if key in buckets:
            # Si hubo al menos una caida en el bucket, mostrar 0
            data.append(min(buckets[key]))
        else:
            data.append(None)
    return labels, data


def _build_liveness_cards(
    liveness: list[LivenessRecord],
    recent_down: dict[str, bool],
    liveness_ranges: dict[str, dict[str, tuple[list[str], list[int | None]]]],
) -> tuple[str, list[dict]]:
    if not liveness:
        return (
            '    <section class="device-card ap-liveness-card" data-device="ap-liveness-empty">\n'
            '      <div class="device-header"><span class="device-icon">📶</span><span class="device-name">Access Points</span></div>\n'
            '      <p class="muted-note">Sin datos de liveness AP.</p>\n'
            "    </section>\n"
        ), []

    cards = ""
    charts: list[dict] = []
    for row in sorted(liveness, key=lambda x: x.device_name.lower()):
        safe_name = _html.escape(row.device_name, quote=True)
        status_cls = "status-up" if row.is_up else "status-down"
        status_label = "UP" if row.is_up else "DOWN"
        https_label = "UP" if row.https_up else "DOWN"
        rtt = f"{row.ping_rtt_ms:.2f} ms" if row.ping_rtt_ms is not None else "-"
        ts = row.timestamp_utc.astimezone(_TZ_MX).strftime("%H:%M:%S UTC-6")
        badge = '<span class="recent-down-badge">Caida en 72h</span>' if recent_down.get(row.device_name, False) else ""

        chart_id = _safe_id(f"ap-live-{row.device_name}")
        ranges = liveness_ranges.get(row.device_name, {})
        charts.append(
            {
                "id": chart_id,
                "label": row.device_name,
                "ranges": {k: {"labels": v[0], "data": v[1]} for k, v in ranges.items()},
            }
        )

        btns = "".join(
            f'<button class="time-btn ap-live-btn{" active" if r == "3d" else ""}" '
            f'data-chart-id="{chart_id}" data-range="{r}">{r}</button>'
            for r in _RANGE_LABELS
        )
        cards += (
            f'    <section class="device-card ap-liveness-card" data-device="{safe_name}">\n'
            f'      <div class="device-header"><span class="device-icon">📶</span><span class="device-name">{_html.escape(row.device_name)}</span>{badge}</div>\n'
            f'      <div class="ap-status-grid">\n'
            f'        <div class="ap-status-item"><span class="label">Estado</span><span class="value {status_cls}">{status_label}</span></div>\n'
            f'        <div class="ap-status-item"><span class="label">HTTPS 443</span><span class="value">{https_label}</span></div>\n'
            f'        <div class="ap-status-item"><span class="label">RTT</span><span class="value">{rtt}</span></div>\n'
            f'        <div class="ap-status-item"><span class="label">Ultimo check</span><span class="value">{ts}</span></div>\n'
            f'      </div>\n'
            f'      <div class="ap-liveness-detail">\n'
            f'        <div class="chart-header"><span class="chart-label">Disponibilidad (1=UP, 0=DOWN)</span><div class="time-selector">{btns}</div></div>\n'
            f'        <div class="liveness-chart-wrap"><canvas id="{chart_id}"></canvas></div>\n'
            f'      </div>\n'
            "    </section>\n"
        )
    return cards, charts


def _build_liveness_js(liveness_charts: list[dict]) -> str:
    if not liveness_charts:
        return ""
    chart_data_js = json.dumps({c["id"]: c["ranges"] for c in liveness_charts})
    chart_meta_js = json.dumps({c["id"]: c["label"] for c in liveness_charts})
    tpl = """<script>
(function(){
  var _data=__DATA__;
  var _meta=__META__;
  var _charts={};
  for(var id in _data){
    var el=document.getElementById(id);
    if(!el)continue;
    var d=_data[id]["3d"]||{labels:[],data:[]};
    _charts[id]=new Chart(el,{
      type:'line',
      data:{labels:d.labels,datasets:[{
        data:d.data,
        borderColor:'#22c55e',
        backgroundColor:'rgba(34,197,94,0.12)',
        borderWidth:2,
        pointRadius:3,
        pointBackgroundColor:function(ctx){
          var y = (ctx && ctx.parsed) ? Number(ctx.parsed.y) : Number(ctx.raw);
          return y===0?'#ef4444':'#22c55e';
        },
        pointBorderColor:function(ctx){
          var y = (ctx && ctx.parsed) ? Number(ctx.parsed.y) : Number(ctx.raw);
          return y===0?'#ef4444':'#22c55e';
        },
        segment:{
          borderColor:function(ctx){
            var y0=Number(ctx.p0.parsed.y), y1=Number(ctx.p1.parsed.y);
            return (y0===0||y1===0)?'#ef4444':'#22c55e';
          },
          backgroundColor:function(ctx){
            var y0=Number(ctx.p0.parsed.y), y1=Number(ctx.p1.parsed.y);
            return (y0===0||y1===0)?'rgba(239,68,68,0.18)':'rgba(34,197,94,0.12)';
          }
        },
        stepped:false,tension:0.35,fill:true,spanGaps:true
      }]},
      options:{
        responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:false},title:{display:true,text:_meta[id],color:'#94a3b8',font:{size:11}}},
        scales:{
          x:{ticks:{color:'#94a3b8',maxTicksLimit:8},grid:{color:'rgba(51,65,85,0.4)'}},
          y:{min:0,max:1,ticks:{color:'#94a3b8',stepSize:1,callback:function(v){return v===1?'UP':'DOWN';}},grid:{color:'rgba(51,65,85,0.4)'}}
        }
      }
    });
  }
  document.querySelectorAll('.ap-live-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      var id=this.dataset.chartId, range=this.dataset.range, chart=_charts[id];
      if(!chart)return;
      var d=(_data[id]&&_data[id][range])||{labels:[],data:[]};
      chart.data.labels=d.labels;
      chart.data.datasets[0].data=d.data;
      chart.update();
      this.closest('.time-selector').querySelectorAll('.ap-live-btn').forEach(function(b){b.classList.remove('active');});
      this.classList.add('active');
    });
  });
})();
</script>"""
    return tpl.replace("__DATA__", chart_data_js).replace("__META__", chart_meta_js)


def _build_html(
    now_str: str,
    poll_interval: int,
    device_cards: str,
    charts_js: str,
    interfaces_js: str = "",
    liveness_cards: str = "",
    liveness_js: str = "",
) -> str:
    focus_js = f"""<script>
(function(){{
  var _pollInterval={poll_interval};
  var _focusActive=false;
  var _timer=null;
  function reloadPage(){{if(!_focusActive)window.location.reload();}}
  function startTimer(){{_timer=setTimeout(reloadPage,_pollInterval*1000);}}
  function enterFocus(name){{
    _focusActive=true;
    clearTimeout(_timer);
    document.body.classList.add('focus-mode');
    document.querySelectorAll('.device-card').forEach(function(c){{
      if(c.dataset.device===name)c.classList.add('focused');
    }});
    window.location.hash=name;
  }}
  function exitFocus(){{
    _focusActive=false;
    document.body.classList.remove('focus-mode');
    document.querySelectorAll('.device-card').forEach(function(c){{
      c.classList.remove('focused');
      var r=c.querySelector('.iface-result');
      if(r)r.innerHTML='';
      var b=c.querySelector('.iface-btn');
      if(b){{b.textContent='Ver interfaces';b.disabled=false;}}
    }});
    window.location.hash='';
    startTimer();
  }}
  document.querySelectorAll('.device-card').forEach(function(card){{
    card.addEventListener('click',function(e){{
      if(e.target.closest('button'))return;
      if(!_focusActive)enterFocus(card.dataset.device);
    }});
  }});
  document.getElementById('back-btn').addEventListener('click',exitFocus);
  var hash=window.location.hash.slice(1);
  if(hash){{
    var t=document.querySelector('.device-card[data-device="'+hash+'"]');
    if(t)enterFocus(hash);
  }}
  startTimer();
}})();
</script>"""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SDD Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>{_CSS}</style>
</head>
<body>
  <button id="back-btn">← Volver</button>
  <header>
    <div>
      <h1>SDD Monitor</h1>
      <p class="header-meta">Actualizado: {_html.escape(now_str)}</p>
    </div>
    <span class="refresh-badge">↻ {poll_interval}s</span>
  </header>
  <main class="devices-grid">
{device_cards}
{liveness_cards}
  </main>
{charts_js}
{interfaces_js}
{liveness_js}
{focus_js}
</body>
</html>"""


def _build_error_card(device_name: str, device_type: str | None, error_msg: str) -> str:
    icon = _ICONS.get(device_type or "", _DEFAULT_ICON)
    safe_name = _html.escape(device_name, quote=True)
    return (
        f'    <section class="device-card error-card" data-device="{safe_name}">\n'
        f'      <div class="device-header">'
        f'<span class="device-icon">{icon}</span>'
        f'<span class="device-name">{_html.escape(device_name)}</span>'
        f'<span class="error-badge">Sin respuesta</span>'
        f"</div>\n"
        f'      <p class="error-msg">{_html.escape(error_msg)}</p>\n'
        f"    </section>\n"
    )


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
            f"<td class='ts'>{record.timestamp_utc.astimezone(_TZ_MX).strftime('%H:%M:%S')} UTC-6</td>"
            f"</tr>\n"
        )

        if is_uptime or not _is_numeric(record.raw_value):
            continue

        key = (device_name, record.oid)
        ranges = range_data.get(key, {})
        has_data = any(sum(1 for v in d if v is not None) >= 2 for _, d in ranges.values())
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

    safe_name = _html.escape(device_name, quote=True)
    iface_section = ""
    if device_type == "switch":
        iface_section = (
            f'      <button class="iface-btn" data-device="{safe_name}">Ver interfaces</button>\n'
            f'      <div class="iface-result"></div>\n'
        )
    card = (
        f'    <section class="device-card" data-device="{safe_name}">\n'
        f'      <div class="device-header">'
        f'<span class="device-icon">{icon}</span>'
        f'<span class="device-name">{_html.escape(device_name)}</span>'
        f"</div>\n"
        f'      <table class="metrics-table">\n'
        f"        <thead><tr><th>Métrica</th><th>Valor</th><th>Timestamp</th></tr></thead>\n"
        f"        <tbody>\n{rows}        </tbody>\n"
        f"      </table>\n"
        f"{chart_blocks}"
        f"{iface_section}"
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
        borderWidth:2,pointRadius:3,tension:0.35,fill:true,spanGaps:true
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
    errors: dict[str, str] | None,
    db_path: Path,
    html_path: Path,
    poll_interval: int,
    liveness: list[LivenessRecord] | None = None,
) -> None:
    errors = errors or {}
    liveness = liveness or []
    try:
        type_map = {d["name"]: d.get("type") for d in devices}

        by_device: dict[str, list[MetricRecord]] = defaultdict(list)
        for r in metrics:
            by_device[r.device_name].append(r)

        range_data: dict[tuple[str, str], dict[str, tuple[list, list]]] = {}
        liveness_ranges: dict[str, dict[str, tuple[list[str], list[int | None]]]] = {}
        recent_down: dict[str, bool] = {}
        with Storage(db_path) as storage:
            for device_name, records in by_device.items():
                for record in records:
                    if _is_uptime_label(record.label) or not _is_numeric(record.raw_value):
                        continue
                    key = (device_name, record.oid)
                    range_data[key] = {}
                    for range_id, hours, bucket_mins in _RANGES:
                        raw = storage.query_timerange(device_name, record.oid, hours)
                        start = datetime.now(timezone.utc) - timedelta(hours=hours)
                        lbs, dt = _aggregate(raw, bucket_mins, start_time=start)
                        range_data[key][range_id] = (lbs, dt)
            for row in liveness:
                liveness_ranges[row.device_name] = {}
                for range_id, hours, bucket_mins in _RANGES:
                    raw_live = storage.query_liveness_timerange(row.device_name, hours)
                    start = datetime.now(timezone.utc) - timedelta(hours=hours)
                    lbs, dt = _aggregate_liveness(raw_live, bucket_mins, start_time=start)
                    liveness_ranges[row.device_name][range_id] = (lbs, dt)
                recent_down[row.device_name] = storage.had_liveness_down(row.device_name, hours=72)

        device_cards = ""
        all_charts: list[dict] = []
        for device_name, records in by_device.items():
            card, charts = _build_device_card(
                device_name, type_map.get(device_name), records, range_data
            )
            device_cards += card
            all_charts.extend(charts)

        for device_name, error_msg in errors.items():
            device_cards += _build_error_card(device_name, type_map.get(device_name), error_msg)

        liveness_cards, liveness_charts = _build_liveness_cards(liveness, recent_down, liveness_ranges)
        now_str = datetime.now(_TZ_MX).strftime("%Y-%m-%d %H:%M:%S UTC-6")
        html_content = _build_html(
            now_str, poll_interval, device_cards,
            _build_charts_js(all_charts),
            _build_interfaces_js(),
            liveness_cards,
            _build_liveness_js(liveness_charts),
        )

        html_path = Path(html_path)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = html_path.with_suffix(".tmp")
        tmp.write_text(html_content, encoding="utf-8")
        tmp.replace(html_path)

    except Exception as exc:
        logger.error("Error generando reporte HTML en %s: %s", html_path, exc)
