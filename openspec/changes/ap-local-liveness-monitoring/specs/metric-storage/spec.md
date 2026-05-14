## ADDED Requirements

### Requirement: Persistir snapshots de liveness de AP
El sistema SHALL almacenar en SQLite un snapshot de liveness por AP y por ciclo, incluyendo estado `up/down`, resultado de chequeo HTTPS, latencia ICMP (si existe), error (si existe) y marca de tiempo UTC.

#### Scenario: Snapshot almacenado exitosamente
- **WHEN** finaliza un ciclo de chequeo de liveness para un AP
- **THEN** el storage SHALL insertar un registro con los campos de estado y timestamp del ciclo

#### Scenario: AP sin latencia disponible
- **WHEN** un AP no responde a ICMP pero si existe resultado de HTTPS o error
- **THEN** el storage SHALL guardar el snapshot con `ping_rtt_ms` nulo sin fallar la insercion

### Requirement: Consultar ultimo estado de liveness por AP
El sistema SHALL permitir consultar el ultimo snapshot disponible para cada AP monitoreado.

#### Scenario: Consulta de ultimo estado por AP
- **WHEN** la capa de presentacion solicita el estado actual de APs
- **THEN** el storage SHALL retornar el registro mas reciente por cada AP ordenado por nombre de dispositivo
