## 1. Modificar scheduler.py

- [x] 1.1 Cambiar la firma de `_poll_cycle` para recibir `db_path: Path` en lugar de `storage: Storage`
- [x] 1.2 Dentro de `_poll_cycle`, abrir la conexión con `with Storage(db_path) as storage:` y mover la lógica de inserción dentro del bloque
- [x] 1.3 En `run()`, eliminar la creación de `Storage(db_path)` fuera del job y pasar `db_path` como argumento al job
- [x] 1.4 Eliminar `storage.close()` del bloque `finally` en `run()` (ya no hay conexión persistente que cerrar)

## 2. Verificar tests existentes

- [x] 2.1 Revisar `tests/test_storage.py` para confirmar que los tests siguen pasando con la nueva forma de uso
- [x] 2.2 Actualizar mocks en `tests/` que pasen una instancia `Storage` a `_poll_cycle` para que ahora pasen un `Path`

## 3. Prueba de integración

- [x] 3.1 Ejecutar `python -m sdd_monitor` y confirmar que no aparece el error de threading en el log
- [x] 3.2 Verificar que los registros se están insertando correctamente en la base de datos SQLite
