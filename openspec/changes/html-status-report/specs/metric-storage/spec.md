## ADDED Requirements

### Requirement: Consultar los últimos N registros de un OID por dispositivo
El sistema SHALL permitir recuperar los últimos N registros almacenados para un OID específico de un dispositivo específico, ordenados cronológicamente de más antiguo a más reciente.

#### Scenario: Consulta con historial disponible
- **WHEN** se solicitan los últimos N registros de un OID para un dispositivo y existen al menos 1 registro
- **THEN** el storage SHALL retornar hasta N registros ordenados de más antiguo a más reciente

#### Scenario: Consulta sin registros disponibles
- **WHEN** se solicitan registros de un OID para un dispositivo que no tiene datos almacenados
- **THEN** el storage SHALL retornar una lista vacía sin producir error

#### Scenario: N mayor que registros existentes
- **WHEN** se solicitan N registros pero existen menos de N en la base de datos
- **THEN** el storage SHALL retornar todos los registros disponibles sin error
