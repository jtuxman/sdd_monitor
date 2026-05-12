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

## 6. Formateo de Uptime

- [x] 6.1 Agregar función `_format_uptime(centiseconds: str) -> str` en `html_report.py` que convierta centisegundos a formato `Xd Xh Xm`
- [x] 6.2 En `_build_device_card`, detectar si `label` contiene "uptime" (case-insensitive) y mostrar el valor formateado en lugar del crudo
- [x] 6.3 Excluir OIDs con label "uptime" de la generación de gráficas

## 7. Selector de rango temporal en gráficas

- [x] 7.1 Añadir `query_timerange(device_name: str, oid: str, hours: int) -> list[MetricRecord]` en `storage.py`
- [x] 7.2 Añadir `_aggregate(records, bucket_minutes) -> tuple[list[str], list[float]]` en `html_report.py` que agrupe registros en buckets y calcule promedio por bucket
- [x] 7.3 Definir `_RANGES = [("1h",1,1), ("1d",24,15), ("3d",72,60), ("7d",168,240)]` en `html_report.py`
- [x] 7.4 Actualizar `generate()` para consultar los 4 rangos por OID numérico usando `query_timerange` + `_aggregate` y construir `range_data`
- [x] 7.5 Actualizar `_build_device_card` para recibir `range_data` en lugar de `history_map` y generar botones de rango encima de cada canvas
- [x] 7.6 Actualizar `_build_charts_js` para embeber `window._chartData` con los 4 datasets por gráfica e inicializar con rango `1h`
- [x] 7.7 Añadir handler JS para los botones que actualice Chart.js sin recargar
- [x] 7.8 Añadir CSS para los botones de rango (`.time-btn`, `.time-selector`, `.chart-header`)
- [x] 7.9 Añadir tests para `Storage.query_timerange` y `_aggregate`

## 8. Zona horaria y tarjetas de error

- [x] 8.1 Usar UTC-6 fijo (`timezone(timedelta(hours=-6))`) para todos los timestamps de display en `html_report.py` (header, tabla, eje X de gráficas)
- [x] 8.2 Modificar `_query_oid` para retornar `tuple[str | None, str | None]` (valor, mensaje de error)
- [x] 8.3 Modificar `_collect_async` y `collect()` para retornar `tuple[list[MetricRecord], dict[str, str]]` con el mapa `device_name → error`
- [x] 8.4 Actualizar `scheduler._poll_cycle` para desempaquetar errores y pasarlos a `presentation.render()` y `html_report.generate()`
- [x] 8.5 Actualizar `html_report.generate()` para recibir `errors` y generar tarjeta de error por dispositivo sin respuesta
- [x] 8.6 Implementar `_build_error_card(device_name, device_type, error_msg)` con borde rojo en el HTML
- [x] 8.7 Actualizar tests de `collector` y `html_report` para el nuevo tipo de retorno

## 9. Vista de foco por dispositivo

- [x] 9.1 Reemplazar `<meta http-equiv="refresh">` por un `setTimeout(reloadPage, pollInterval * 1000)` en el JS embebido de `html_report.py`, con una variable `_focusActive` que impide la recarga cuando está en `true`
- [x] 9.2 Añadir atributo `data-device="<device_name>"` en cada tarjeta de dispositivo generada por `_build_device_card` e `_build_error_card`
- [x] 9.3 Implementar handler JS `enterFocus(deviceName)` que oculte todas las tarjetas excepto la seleccionada, establezca `_focusActive = true`, cancele el timer con `clearTimeout` y actualice `window.location.hash`
- [x] 9.4 Implementar handler JS `exitFocus()` que restaure la visibilidad de todas las tarjetas, establezca `_focusActive = false` y reinicie el `setTimeout`
- [x] 9.5 Añadir un botón de retorno (`← Volver`) que aparezca solo en vista de foco, implementado como elemento fijo en la página y controlado via CSS con clase `.focus-mode` en el `<body>`
- [x] 9.6 Al cargar la página, leer `window.location.hash` y si corresponde a un dispositivo existente, llamar automáticamente a `enterFocus(deviceName)`
- [x] 9.7 Añadir CSS para el modo foco: `.focus-mode .device-card { display: none }`, `.focus-mode .device-card.focused { display: block }`, estilos del botón de retorno

## 5. Tests

- [x] 5.1 Añadir test para `collector.load_devices` con OIDs como strings, como objetos y mezclados
- [x] 5.2 Añadir test para `Storage.query_recent` verificando orden, límite N y lista vacía
- [x] 5.3 Añadir test para `html_report.generate` verificando que el archivo HTML se crea y contiene las secciones esperadas (nombre de dispositivo, canvas, meta refresh)
