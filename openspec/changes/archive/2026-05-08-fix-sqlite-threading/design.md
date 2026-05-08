## Context

`Storage` crea la conexión SQLite en `__init__`, en el hilo principal. APScheduler usa un hilo secundario para ejecutar `_poll_cycle`, lo que viola la restricción de SQLite: una conexión solo puede usarse en el hilo que la creó.

Estado actual en `scheduler.py`:
```
hilo principal → Storage(db_path)  ← conexión creada aquí
hilo APScheduler → _poll_cycle(devices, storage) ← conexión usada aquí ✗
```

## Goals / Non-Goals

**Goals:**
- Eliminar el error `SQLite objects created in a thread can only be used in that same thread`.
- Que cada ciclo de polling cree su propia conexión SQLite dentro del hilo que lo ejecuta.
- Mantener el comportamiento externo idéntico (misma tabla, mismos datos).

**Non-Goals:**
- No migrar a una base de datos diferente.
- No introducir un pool de conexiones ni concurrencia avanzada.
- No cambiar el esquema de la tabla `metrics`.

## Decisions

**Decisión: conexión por llamada en lugar de conexión compartida**

`_poll_cycle` recibirá `db_path: Path` en lugar de una instancia `Storage`. Abrirá y cerrará la conexión dentro del mismo ciclo usando `Storage` como context manager (`with Storage(db_path) as s:`).

Alternativas consideradas:
- `check_same_thread=False` en `sqlite3.connect`: descarta el error pero introduce condiciones de carrera reales si alguna vez hay más de una instancia del job.
- Pool de conexiones con `threading.local`: sobreingeniería para el alcance actual del proyecto.
- Usar `ThreadPoolExecutor=0` en APScheduler (forzar hilo principal): rompe el modelo de scheduler y bloquea señales del SO.

**Decisión: `Storage` ya implementa context manager**

`Storage.__enter__` / `__exit__` ya existen en el código. No es necesario modificar `Storage`, solo cambiar cómo lo usa `scheduler.py`.

## Risks / Trade-offs

- [Riesgo] Abrir/cerrar conexión en cada ciclo agrega latencia mínima → Aceptable dado el intervalo de 60 segundos entre ciclos.
- [Riesgo] Si `db_path` es inválida, el error ocurre en el hilo del scheduler → Ya estaba manejado por el `try/except` en `_poll_cycle`.
