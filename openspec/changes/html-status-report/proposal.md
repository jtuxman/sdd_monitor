## Why

El monitor actualmente solo presenta métricas en terminal. Se necesita una vista persistente y accesible desde cualquier browser que muestre el estado actual de los dispositivos y el historial de métricas clave, publicada automáticamente en un servidor nginx ya existente.

## What Changes

- Nuevo módulo `html_report` que genera un archivo HTML estático tras cada ciclo de polling
- El HTML incluye: estado actual por dispositivo, gráficas históricas por OID (Chart.js CDN), auto-refresh via `<meta>`, icono por tipo de dispositivo
- **BREAKING**: Schema de `devices.yaml` extiende OIDs de strings simples a objetos `{oid, label}` con fallback para strings (compatibilidad hacia atrás)
- Nuevo campo opcional `type` en cada dispositivo (`switch`, `router`, `server`, `firewall`)
- Nueva variable de entorno `HTML_PATH` para configurar la ruta de salida del HTML
- `scheduler._poll_cycle` llama a `html_report.generate()` al final de cada ciclo
- `Storage` añade método `query_recent(device, oid, n)` para consultar los últimos N registros de un OID

## Capabilities

### New Capabilities

- `html-report`: Generación de reporte HTML estático con estado actual e historial de métricas por dispositivo, gráficas Chart.js, iconos por tipo, auto-refresh y publicación en directorio configurable

### Modified Capabilities

- `snmp-collection`: El schema de dispositivos en `devices.yaml` extiende el campo `oids` para soportar objetos `{oid, label}` además de strings simples
- `metric-storage`: Nuevo método de consulta `query_recent` para recuperar los últimos N registros de un OID específico por dispositivo

## Impact

- **Nuevos archivos**: `src/sdd_monitor/html_report.py`
- **Modificados**: `src/sdd_monitor/scheduler.py`, `src/sdd_monitor/storage.py`, `src/sdd_monitor/__main__.py`, `src/sdd_monitor/collector.py`
- **Configuración**: `config/devices.yaml` (schema extendido, compatible hacia atrás)
- **Dependencias**: ninguna nueva (Chart.js se carga desde CDN)
- **Variables de entorno**: nueva `HTML_PATH` (default: `data/report.html`)
