## Why

Los equipos de red (routers, switches, servidores) requieren monitoreo continuo de sus métricas operativas. El proyecto SDD Monitor provee una herramienta de línea de comandos que consulta dispositivos vía SNMP, persiste las métricas en SQLite y las presenta en terminal, cubriendo la necesidad de visibilidad de red sin depender de plataformas externas.

## What Changes

- Proyecto Python nuevo con arquitectura de capas: collector → processor → storage → presentation
- Capa `collector`: consultas SNMP v2c/v3 a dispositivos definidos en `config/devices.yaml`
- Capa `processor`: normalización y transformación de los datos SNMP recibidos
- Capa `storage`: persistencia de métricas en SQLite usando el módulo estándar `sqlite3`
- Capa `presentation`: salida formateada en terminal usando `rich`
- Scheduler periódico (via `APScheduler`) para polls automáticos de dispositivos
- Configuración externalizada en `config/devices.yaml` y variables de entorno con `python-dotenv`
- Suite de tests con `pytest`
- Gestión de dependencias con `pyproject.toml`

## Capabilities

### New Capabilities

- `snmp-collection`: Consulta periódica de OIDs a dispositivos de red vía SNMP v2c/v3, configurados en YAML
- `metric-storage`: Persistencia de métricas recolectadas en base de datos SQLite local
- `terminal-display`: Presentación formateada de métricas en terminal usando Rich
- `poll-scheduling`: Ejecución periódica automática del ciclo collector → processor → storage → presentation

### Modified Capabilities

## Impact

- **Dependencias nuevas**: `pysnmp` o `easysnmp`, `rich`, `APScheduler`, `pyyaml`, `python-dotenv`, `pytest`
- **Archivos de configuración**: `config/devices.yaml` (dispositivos), `.env` (variables de entorno sensibles)
- **Base de datos**: archivo SQLite local (ej. `data/metrics.db`)
- **Sin impacto en sistemas externos**: opera de forma read-only sobre los dispositivos de red (solo consultas SNMP GET)
