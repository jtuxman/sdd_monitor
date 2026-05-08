## Why

APScheduler ejecuta el ciclo de polling `_poll_cycle` en un hilo secundario, pero la conexión SQLite se crea en el hilo principal. SQLite no permite compartir objetos de conexión entre hilos, lo que provoca un error en cada ciclo de recolección y hace que las métricas no se almacenen.

## What Changes

- La conexión SQLite dejará de crearse una sola vez al iniciar el scheduler.
- Cada ciclo de polling creará y cerrará su propia conexión SQLite dentro del mismo hilo de ejecución.
- El módulo `storage` expondrá una función que recibe la ruta de la base de datos y crea la conexión localmente.

## Capabilities

### New Capabilities

- Ninguna capacidad nueva; es una corrección de implementación.

### Modified Capabilities

- `metric-storage`: El contrato de almacenamiento cambia para que la conexión sea creada por llamada (por hilo) en lugar de una conexión compartida persistente.

## Impact

- `src/sdd_monitor/storage.py`: cambiar la gestión del ciclo de vida de la conexión.
- `src/sdd_monitor/scheduler.py`: pasar la ruta `db_path` al ciclo de polling en lugar de una conexión abierta.
- No hay cambios en la API pública del sistema ni en el formato de los datos almacenados.
