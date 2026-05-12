## Context

SDD Monitor actualmente persiste métricas en SQLite y las presenta en terminal via Rich. El usuario dispone de un servidor nginx en su red donde quiere publicar automáticamente el estado de los dispositivos monitoreados. La generación del HTML ocurre dentro del proceso Python existente, sin infraestructura adicional.

## Goals / Non-Goals

**Goals:**
- Generar un único archivo HTML estático tras cada ciclo de polling
- Mostrar estado actual (último valor) e historial (últimos 20 registros) por OID por dispositivo
- Gráficas de línea con Chart.js cargado desde CDN
- Icono por tipo de dispositivo (`switch`, `router`, `server`, `firewall`) via campo `type` en YAML
- Etiquetas legibles por OID via campo `label` en YAML, con fallback al OID crudo
- Auto-refresh de la página cada `POLL_INTERVAL` segundos via `<meta http-equiv="refresh">`
- Ruta de salida configurable via `HTML_PATH` (default: `data/report.html`)
- Diseño moderno con CSS embebido, sin frameworks CSS

**Non-Goals:**
- Servidor HTTP embebido en el proceso Python
- Autenticación o control de acceso
- Alertas o notificaciones
- Soporte offline (Chart.js requiere CDN)
- Múltiples archivos HTML o rutas separadas por dispositivo (la vista de foco es JS dentro del único HTML)

## Decisions

### 1. Chart.js CDN vs SVG generado en Python
**Decisión**: Chart.js desde CDN (`https://cdn.jsdelivr.net/npm/chart.js`).
**Razón**: El servidor nginx tiene salida a internet. Chart.js produce gráficas de línea interactivas (tooltip, hover) con una sola etiqueta `<script>`. SVG inline requeriría lógica de normalización y renderizado en Python sin beneficio visual equivalente.
**Alternativa descartada**: SVG sparklines — apropiado solo si no hubiera acceso a CDN.

### 2. Momento de generación del HTML
**Decisión**: Al final de cada `_poll_cycle`, después de `presentation.render()`.
**Razón**: El HTML refleja siempre el estado del último poll completado. No requiere scheduler separado ni lógica de debounce.
**Alternativa descartada**: Job aparte en el scheduler — añade complejidad sin beneficio dado que el intervalo ya es configurable.

### 3. Fuente de datos para el historial
**Decisión**: `Storage.query_recent(device_name, oid, n=20)` consulta SQLite.
**Razón**: Los últimos 20 registros por OID son suficientes para una gráfica de tendencia. Leer de SQLite garantiza que el historial persiste entre reinicios del proceso.
**Alternativa descartada**: Buffer en memoria — se pierde al reiniciar el proceso.

### 4. Compatibilidad hacia atrás del schema de OIDs
**Decisión**: `collector.py` acepta tanto strings simples como objetos `{oid, label}` en la lista `oids`. Si el item es string, `label` es el OID crudo.
**Razón**: Evita romper configuraciones existentes. La migración es opcional y progresiva.

### 5. HTML auto-contenido (CSS inline)
**Decisión**: Todo el CSS va embebido en `<style>` dentro del HTML generado.
**Razón**: El archivo es copiado a nginx sin dependencias de archivos adicionales. Sin Tailwind, sin Bootstrap — solo variables CSS y grid layout.

### 6. Iconos de dispositivo
**Decisión**: Emoji mapeados desde el campo `type`:
- `switch` → 🔀, `router` → 🌐, `server` → 🖥️, `firewall` → 🔒, default → 📡
**Razón**: Sin dependencias de imagen, funciona en cualquier browser moderno, fácil de extender.

### 7. Vista de foco por dispositivo — mecanismo de auto-refresh
**Decisión**: Reemplazar `<meta http-equiv="refresh">` por un `setTimeout` en JavaScript que verifica si hay un dispositivo en foco antes de recargar. Al entrar en foco, se cancela el timer via `clearTimeout`; al salir, se reinicia.
**Razón**: El `<meta>` no puede cancelarse desde JavaScript una vez insertado en el DOM. Un `setTimeout` JS da el mismo comportamiento en vista general y permite suspender la recarga en vista de foco sin modificar el DOM del `<head>`. El hash en la URL (`#device-name`) persiste el estado de foco entre recargas manuales.
**Alternativa descartada**: Generar un HTML por dispositivo — añade complejidad de escritura de múltiples archivos y enlaces entre ellos sin beneficio dado que el foco es una operación puramente de presentación.

## Risks / Trade-offs

- **CDN no disponible** → La gráfica no renderiza pero el HTML con la tabla de estado actual sigue siendo legible. Mitigación: el diseño degrada graciosamente (tabla visible sin JS).
- **HTML_PATH sin permisos de escritura** → El error se registra en el log pero no interrumpe el polling. Mitigación: logging claro con el path afectado.
- **20 registros insuficientes para tendencias largas** → Aceptable para el caso de uso actual (monitoreo operativo). Mitigación: la constante `N_HISTORY` en `html_report.py` permite ajuste sin cambio de interfaz.
- **Cambio de schema de OIDs es breaking si el código no maneja strings** → Mitigado por compatibilidad hacia atrás explícita en `collector.py`.

## Migration Plan

1. Actualizar `config/devices.yaml` con campos `type` y `label` (opcional, no requerido)
2. Añadir `HTML_PATH` a `.env` apuntando al directorio nginx
3. Desplegar nueva versión — el HTML se genera desde el primer poll
4. Sin rollback especial: si se elimina `html_report`, el scheduler simplemente deja de llamarlo
