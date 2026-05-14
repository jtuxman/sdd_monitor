## ADDED Requirements

### Requirement: Mostrar estado de liveness de AP en terminal
La presentación en terminal SHALL incluir una sección dedicada a Access Points monitoreados localmente, mostrando estado actual, latencia ICMP, estado HTTPS y timestamp del último chequeo.

#### Scenario: AP marcado como disponible
- **WHEN** el último snapshot de liveness de un AP indica disponibilidad
- **THEN** la presentación SHALL mostrar el AP como `UP` con indicador visual positivo y su latencia en ms

#### Scenario: AP marcado como no disponible
- **WHEN** el último snapshot de liveness de un AP indica no disponibilidad o error
- **THEN** la presentación SHALL mostrar el AP como `DOWN` con indicador visual de alerta y mensaje resumido del error

#### Scenario: Sin datos de liveness
- **WHEN** no existen snapshots de liveness para APs en el ciclo actual
- **THEN** la presentación SHALL mostrar un mensaje informativo indicando ausencia de datos de liveness sin producir error
