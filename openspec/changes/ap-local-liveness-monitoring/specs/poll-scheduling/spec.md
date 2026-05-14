## MODIFIED Requirements

### Requirement: Ejecutar ciclos de polling periódicos
El sistema SHALL ejecutar el ciclo completo collector → processor → storage → presentation de forma periódica y automática usando APScheduler. El intervalo de polling SHALL ser configurable. El ciclo SHALL incluir adicionalmente el chequeo local de liveness para APs configurados.

#### Scenario: Inicio del scheduler
- **WHEN** la aplicación arranca correctamente con configuración válida
- **THEN** el scheduler SHALL iniciar y ejecutar el primer ciclo de polling inmediatamente, y luego repetirlo según el intervalo configurado

#### Scenario: Ciclo de polling completo
- **WHEN** el scheduler dispara un ciclo
- **THEN** SHALL ejecutar en secuencia: recolección SNMP, chequeo local de liveness de APs, procesamiento, almacenamiento en SQLite y presentación en terminal

#### Scenario: Error en un ciclo no detiene el scheduler
- **WHEN** un ciclo de polling falla (ej. error de red o base de datos)
- **THEN** el scheduler SHALL registrar el error y continuar ejecutando ciclos futuros sin detenerse

#### Scenario: Intervalo configurable
- **WHEN** se configura el intervalo de polling en la configuración de la aplicación
- **THEN** el scheduler SHALL respetar ese intervalo entre ejecuciones de ciclos consecutivos

#### Scenario: Error de liveness no detiene el ciclo
- **WHEN** falla el chequeo local de liveness de un AP durante el ciclo
- **THEN** el scheduler SHALL registrar el error de ese AP y continuar con el resto de etapas y dispositivos
