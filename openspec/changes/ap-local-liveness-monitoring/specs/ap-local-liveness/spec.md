## ADDED Requirements

### Requirement: Monitorear disponibilidad local de Access Points
El sistema SHALL ejecutar chequeos locales de disponibilidad para dispositivos AP configurados para liveness en cada ciclo de polling. Cada chequeo SHALL incluir prueba ICMP (ping) y verificacion de servicio HTTPS en `tcp/443`.

#### Scenario: AP disponible por ICMP y HTTPS
- **WHEN** un AP responde al ping y acepta conexion TCP en el puerto 443 dentro del timeout configurado
- **THEN** el sistema SHALL marcar el AP como `up` y registrar latencia ICMP en milisegundos

#### Scenario: AP sin respuesta ICMP
- **WHEN** un AP no responde al ping dentro del timeout configurado
- **THEN** el sistema SHALL marcar el resultado de ping como fallido y registrar el motivo del error

#### Scenario: AP responde ICMP pero falla HTTPS
- **WHEN** un AP responde al ping pero no acepta conexion al puerto 443
- **THEN** el sistema SHALL registrar `https_up = false` y mantener el resultado ICMP reportado para diagnostico

#### Scenario: Error de chequeo no detiene monitoreo de otros APs
- **WHEN** ocurre una excepcion durante el chequeo de un AP especifico
- **THEN** el sistema SHALL registrar el error de ese AP y continuar con los chequeos del resto de APs en el mismo ciclo
