## Context

SDD Monitor es un proyecto nuevo sin código preexistente. El objetivo es construir un monitor de red SNMP en Python con arquitectura de capas estrictamente separadas. Los dispositivos a monitorear son routers, switches y servidores que exponen métricas vía SNMP v2c o v3. Los datos se persisten localmente y se presentan en terminal.

## Goals / Non-Goals

**Goals:**
- Arquitectura limpia de 4 capas desacopladas: collector, processor, storage, presentation
- Soporte SNMP v2c y v3 sin credenciales hardcodeadas
- Persistencia confiable en SQLite sin dependencias externas de base de datos
- Presentación enriquecida en terminal con `rich`
- Polling periódico configurable por dispositivo
- Configuración 100% externalizada en YAML y `.env`

**Non-Goals:**
- Interfaz web, dashboard gráfico o API REST
- Autenticación de usuarios
- Alertas o notificaciones
- Soporte SNMP v1
- Escritura/modificación de OIDs en dispositivos (solo lectura)

## Decisions

### D1: `pysnmp` como librería SNMP
Usamos `pysnmp` (pura Python) sobre `easysnmp` (bindings C).

**Alternativas consideradas:**
- `easysnmp`: más rápida pero requiere libsnmp-dev instalado, complica el setup y la portabilidad.
- `pysnmp`: sin dependencias nativas, mantiene el proyecto portable y más fácil de instalar con `pip`.

### D2: SQLite con `sqlite3` estándar (sin ORM)
Usamos el módulo `sqlite3` de la librería estándar directamente.

**Alternativas consideradas:**
- SQLAlchemy: overhead innecesario para un esquema simple de métricas; agrega una dependencia pesada.
- `sqlite3` directo: control total del esquema, zero dependencias adicionales, suficiente para el volumen esperado.

### D3: `APScheduler` para el scheduler
Usamos `APScheduler` (BlockingScheduler) sobre el paquete `schedule`.

**Alternativas consideradas:**
- `schedule`: API más simple pero carece de soporte nativo para intervalos por trabajo y manejo de errores en jobs.
- `APScheduler`: más maduro, permite configurar intervalos distintos por dispositivo y maneja excepciones en jobs sin detener el scheduler.

### D4: Configuración de dispositivos en `config/devices.yaml`
Todos los parámetros de red (host, community, OIDs) viven en el YAML. Secretos adicionales (credenciales SNMPv3) van en `.env` cargado con `python-dotenv`.

### D5: Separación estricta de capas
Cada capa expone una interfaz mínima hacia la siguiente. El scheduler orquesta el ciclo completo sin que ninguna capa conozca a la anterior. Las capas se comunican mediante estructuras de datos simples (dataclasses o dicts).

### D6: Estructura de directorios
```
sdd_monitor/
├── config/
│   └── devices.yaml
├── src/
│   └── sdd_monitor/
│       ├── collector.py
│       ├── processor.py
│       ├── storage.py
│       ├── presentation.py
│       └── scheduler.py
├── tests/
├── .env.example
└── pyproject.toml
```

## Risks / Trade-offs

- [Dispositivos SNMP inaccesibles durante tests] → Mitigation: mockear las respuestas SNMP en la suite de tests; documentar cómo levantar un simulador SNMP para pruebas de integración.
- [pysnmp v6 tiene breaking changes respecto a v5] → Mitigation: fijar la versión en `pyproject.toml` y documentar la versión soportada.
- [SQLite no escala a miles de dispositivos o alta frecuencia de polling] → Mitigation: aceptado dentro del alcance actual; fuera del alcance futuro se puede migrar a PostgreSQL.
- [OIDs inválidos o dispositivos no accesibles en tiempo de ejecución] → Mitigation: capturar errores por dispositivo/OID individualmente y loguear sin detener el ciclo.
