## 1. Extender schema de devices.yaml

- [x] 1.1 Actualizar `collector.load_devices` para aceptar OIDs como string simple u objeto `{oid, label}`, normalizando siempre a `{oid, label}` internamente
- [x] 1.2 Actualizar `collector._query_oid` y `collector._collect_async` para pasar y retornar el `label` junto al OID en cada `MetricRecord`
- [x] 1.3 Actualizar `models.MetricRecord` para incluir el campo opcional `label: str | None`
- [x] 1.4 Actualizar `config/devices.yaml` con el campo `type` en `switch-core` y objetos `{oid, label}` para los OIDs existentes

## 2. Extender Storage con query_recent

- [x] 2.1 Añadir método `query_recent(device_name: str, oid: str, n: int = 20) -> list[MetricRecord]` en `storage.py` que retorne los últimos N registros ordenados de más antiguo a más reciente

## 3. Implementar módulo html_report

- [x] 3.1 Crear `src/sdd_monitor/html_report.py` con función `generate(metrics: list[MetricRecord], db_path: Path, html_path: Path, poll_interval: int) -> None`
- [x] 3.2 Implementar la consulta de historial: para cada combinación `(device_name, oid)` en `metrics`, llamar a `Storage.query_recent` para obtener los últimos 20 registros
- [x] 3.3 Implementar la detección de valores numéricos para decidir si renderizar gráfica o texto
- [x] 3.4 Implementar el mapeo de `type` a emoji: `switch→🔀`, `router→🌐`, `server→🖥️`, `firewall→🔒`, default→`📡`
- [x] 3.5 Implementar la generación del HTML: CSS embebido moderno, una tarjeta por dispositivo con icono, tabla de estado actual y canvas de Chart.js por OID numérico
- [x] 3.6 Incluir `<meta http-equiv="refresh" content="<poll_interval>">` en el `<head>` del HTML
- [x] 3.7 Implementar escritura atómica del HTML (escribir a archivo temporal y renombrar) para evitar que nginx sirva un archivo parcial
- [x] 3.8 Capturar y loggear errores de escritura sin interrumpir el polling

## 4. Integrar en scheduler y __main__

- [x] 4.1 Añadir lectura de `HTML_PATH` en `__main__.py` con default `data/report.html` y pasarla a `scheduler.run()`
- [x] 4.2 Actualizar firma de `scheduler.run()` para recibir `html_path: Path`
- [x] 4.3 Llamar a `html_report.generate()` al final de `_poll_cycle`, después de `presentation.render()`

## 5. Tests

- [x] 5.1 Añadir test para `collector.load_devices` con OIDs como strings, como objetos y mezclados
- [x] 5.2 Añadir test para `Storage.query_recent` verificando orden, límite N y lista vacía
- [x] 5.3 Añadir test para `html_report.generate` verificando que el archivo HTML se crea y contiene las secciones esperadas (nombre de dispositivo, canvas, meta refresh)
