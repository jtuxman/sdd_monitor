# Configuración de Agentes

## Comportamiento General
- Actuar como desarrollador senior de Python con experiencia en redes y monitoreo.
- Priorizar claridad y simplicidad sobre complejidad.
- Usar nombres claros y descriptivos en inglés para el código.
- Evitar la sobreingeniería de soluciones.
- **NUNCA** introduzcas librerías nuevas sin revisión previa (verifica `pyproject.toml`).
- **NUNCA** cambies el patrón arquitectónico: `colector → procesador → almacenamiento → presentación → reporte HTML`.
- **SIEMPRE** escribe tests con `pytest` para nueva funcionalidad.
- **NUNCA** hardcodees IPs, community strings ni OIDs; todo debe leerse de `devices.yaml`.
- **SIEMPRE** maneja timeouts y errores de conectividad SNMP de forma explícita.

## Stack Tecnológico Actual
- **Lenguaje**: Python 3.10+, tipado estático con type hints
- **SNMP**: `pysnmp>=7` (API asyncio, `pysnmp.hlapi.v3arch.asyncio`); soporta v2c y v3
- **Almacenamiento**: SQLite via `sqlite3` — conexión abierta y cerrada por hilo
- **Presentación CLI**: `rich` — tabla en terminal tras cada poll
- **Reporte web**: HTML estático generado tras cada poll, publicado en directorio nginx vía `HTML_PATH`; usa Chart.js desde CDN para gráficas históricas
- **Scheduler**: `APScheduler>=3.10,<4` con `BlockingScheduler`
- **Configuración**: `config/devices.yaml` + `python-dotenv`
- **Tests**: `pytest` + `pytest-mock`

## Variables de Entorno
| Variable | Default | Descripción |
|---|---|---|
| `DB_PATH` | `data/metrics.db` | Ruta al archivo SQLite |
| `HTML_PATH` | `data/report.html` | Ruta de salida del reporte HTML |
| `POLL_INTERVAL` | `60` | Intervalo de polling en segundos |
| `SNMPV3_USERNAME` | — | Usuario SNMPv3 |
| `SNMPV3_AUTH_KEY` | — | Clave de autenticación SNMPv3 |
| `SNMPV3_PRIV_KEY` | — | Clave de privacidad SNMPv3 |

## Schema de devices.yaml
```yaml
devices:
  - name: switch-core          # identificador único
    type: switch               # switch | router | server | firewall (opcional, para icono en HTML)
    host: 172.16.0.1
    port: 161
    snmp_version: 2c           # 2c | 3
    community: public          # solo para v2c
    timeout: 2
    retries: 1
    oids:
      - oid: 1.3.6.1.2.1.1.1.0   # formato objeto (recomendado)
        label: Descripción
      - 1.3.6.1.2.1.1.3.0        # formato string simple (compatible)
```

## Estilo de Código
- Seguir PEP 8.
- Preferir clases solo cuando encapsulen estado; usar funciones cuando sea suficiente.
- Sin comentarios obvios; solo comentar el *por qué* cuando no sea evidente.
- Sin docstrings en funciones internas; docstring breve en funciones públicas de módulo.
- Usar `str | None` en lugar de `Optional[str]`.

## Estructura de Archivos
```
src/sdd_monitor/
  collector.py      # consultas SNMP, carga de devices.yaml
  processor.py      # normalización de valores crudos
  storage.py        # persistencia SQLite (Storage class)
  presentation.py   # tabla Rich en terminal
  html_report.py    # generación de reporte HTML estático
  scheduler.py      # APScheduler, ciclo de polling
  models.py         # MetricRecord dataclass
  __main__.py       # punto de entrada, lee variables de entorno
config/
  devices.yaml      # dispositivos SNMP a monitorear
tests/              # espeja estructura de src/sdd_monitor/
```

## Control de Alcance
- No agregar autenticación ni roles salvo que se solicite explícitamente.
- No embeber servidor HTTP — el HTML se publica en nginx externo.
- No inventar datos; si un dispositivo no responde, registrar el error y continuar.
- Toda nueva funcionalidad requiere propuesta en `openspec/changes/` antes de implementar.

## Reglas de Flujo OpenSpec
- Revisar `openspec/specs/` antes de cualquier cambio para verificar specs existentes.
- Para nueva funcionalidad: crear `proposal.md` → `design.md` → `specs/` → `tasks.md` (`/opsx:propose`).
- Para implementar: `/opsx:apply`.
- Al completar: `/opsx:archive` (sincroniza delta specs con specs principales).
- **NUNCA** implementar sin propuesta aprobada en `openspec/changes/`.
