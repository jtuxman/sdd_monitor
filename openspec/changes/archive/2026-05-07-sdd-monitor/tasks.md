## 1. Configuración del proyecto

- [x] 1.1 Crear `pyproject.toml` con dependencias: `pysnmp`, `rich`, `APScheduler`, `pyyaml`, `python-dotenv`, `pytest`
- [x] 1.2 Crear estructura de directorios: `src/sdd_monitor/`, `config/`, `tests/`, `data/`
- [x] 1.3 Crear `.env.example` con las variables de entorno necesarias (ruta de la base de datos, credenciales SNMPv3)
- [x] 1.4 Crear `config/devices.yaml` de ejemplo con un dispositivo ficticio documentando todos los campos posibles

## 2. Capa collector

- [x] 2.1 Implementar `src/sdd_monitor/collector.py`: función que carga `config/devices.yaml` y valida su estructura
- [x] 2.2 Implementar consulta SNMP v2c usando `pysnmp` para un dispositivo y lista de OIDs
- [x] 2.3 Extender el collector para soportar SNMP v3 con credenciales desde variables de entorno
- [x] 2.4 Implementar manejo de errores por dispositivo (timeout, host inalcanzable) sin interrumpir la recolección de otros
- [x] 2.5 Implementar manejo de OID no encontrado en el dispositivo (log de advertencia, continuar)
- [x] 2.6 Definir la estructura de datos de retorno (`dataclass` con campos: `device_name`, `oid`, `raw_value`, `timestamp_utc`)

## 3. Capa processor

- [x] 3.1 Implementar `src/sdd_monitor/processor.py`: función que recibe resultados crudos del collector y los normaliza
- [x] 3.2 Implementar conversión de tipos SNMP (Counter32, OctetString, etc.) a tipos Python estándar
- [x] 3.3 Verificar que el processor no importa módulos de collector, storage ni presentation

## 4. Capa storage

- [x] 4.1 Implementar `src/sdd_monitor/storage.py`: creación automática de la base de datos y tabla de métricas al iniciar
- [x] 4.2 Implementar función de inserción de métricas normalizadas en SQLite
- [x] 4.3 Implementar función de consulta de métricas por dispositivo, ordenadas por marca de tiempo descendente
- [x] 4.4 Implementar cierre ordenado de la conexión a la base de datos
- [x] 4.5 Verificar que el storage no importa módulos de collector, processor ni presentation

## 5. Capa presentation

- [x] 5.1 Implementar `src/sdd_monitor/presentation.py`: función que recibe lista de métricas y las renderiza con `rich`
- [x] 5.2 Implementar tabla Rich con columnas: dispositivo, OID, valor, marca de tiempo
- [x] 5.3 Implementar visualización de errores de dispositivo en color distintivo (rojo o advertencia)
- [x] 5.4 Implementar mensaje informativo cuando no hay métricas disponibles
- [x] 5.5 Verificar que la presentation no realiza operaciones de red ni de base de datos

## 6. Scheduler y orquestación

- [x] 6.1 Implementar `src/sdd_monitor/scheduler.py`: ciclo completo collector → processor → storage → presentation
- [x] 6.2 Configurar APScheduler con intervalo configurable desde `.env` o variable de entorno
- [x] 6.3 Implementar manejo de errores en el job del scheduler (log del error, el scheduler no se detiene)
- [x] 6.4 Implementar detención ordenada ante SIGINT/SIGTERM: completar ciclo en curso y cerrar base de datos
- [x] 6.5 Crear punto de entrada `__main__.py` o script CLI que arranque el scheduler

## 7. Tests

- [x] 7.1 Escribir tests unitarios para el collector: carga de YAML válido, YAML ausente, YAML malformado
- [x] 7.2 Escribir tests unitarios para el collector: mock de respuesta SNMP v2c exitosa
- [x] 7.3 Escribir tests unitarios para el collector: mock de timeout y OID no encontrado
- [x] 7.4 Escribir tests unitarios para el processor: conversión de tipos SNMP
- [x] 7.5 Escribir tests unitarios para el storage: creación de esquema, inserción y consulta con base de datos en memoria
- [x] 7.6 Escribir tests unitarios para la presentation: verificar que renderiza sin errores con datos válidos y con lista vacía
- [x] 7.7 Configurar `pytest` en `pyproject.toml` y verificar que todos los tests pasan
