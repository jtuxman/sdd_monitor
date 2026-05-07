# poll-scheduling Specification

## Purpose
TBD - created by archiving change sdd-monitor. Update Purpose after archive.
## Requirements
### Requirement: Ejecutar ciclos de polling periódicos
El sistema SHALL ejecutar el ciclo completo collector → processor → storage → presentation de forma periódica y automática usando APScheduler. El intervalo de polling SHALL ser configurable.

#### Scenario: Inicio del scheduler
- **WHEN** la aplicación arranca correctamente con configuración válida
- **THEN** el scheduler SHALL iniciar y ejecutar el primer ciclo de polling inmediatamente, y luego repetirlo según el intervalo configurado

#### Scenario: Ciclo de polling completo
- **WHEN** el scheduler dispara un ciclo
- **THEN** SHALL ejecutar en secuencia: recolección SNMP, procesamiento, almacenamiento en SQLite y presentación en terminal

#### Scenario: Error en un ciclo no detiene el scheduler
- **WHEN** un ciclo de polling falla (ej. error de red o base de datos)
- **THEN** el scheduler SHALL registrar el error y continuar ejecutando ciclos futuros sin detenerse

#### Scenario: Intervalo configurable
- **WHEN** se configura el intervalo de polling en la configuración de la aplicación
- **THEN** el scheduler SHALL respetar ese intervalo entre ejecuciones de ciclos consecutivos

### Requirement: Detención controlada del scheduler
El sistema SHALL detenerse de forma ordenada ante señales del sistema operativo (SIGINT, SIGTERM), completando el ciclo en curso antes de terminar.

#### Scenario: Detención por Ctrl+C
- **WHEN** el usuario presiona Ctrl+C mientras el scheduler está corriendo
- **THEN** el sistema SHALL interceptar la señal, completar el ciclo en curso si está activo, y cerrar la conexión a la base de datos antes de terminar

