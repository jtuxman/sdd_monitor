## ADDED Requirements

### Requirement: Cargar configuración de dispositivos desde YAML
El sistema SHALL cargar todos los parámetros de dispositivos (nombre, host, versión SNMP, community string, OIDs) desde `config/devices.yaml` al iniciar. Ningún parámetro de red SHALL estar hardcodeado en el código fuente.

#### Scenario: YAML válido cargado al iniciar
- **WHEN** la aplicación inicia y `config/devices.yaml` existe y es válido
- **THEN** el collector SHALL tener una lista de dispositivos con sus OIDs asociados listos para consultar

#### Scenario: Archivo de configuración ausente
- **WHEN** `config/devices.yaml` no existe
- **THEN** la aplicación SHALL mostrar un mensaje de error claro y terminar sin intentar consultas SNMP

#### Scenario: YAML malformado
- **WHEN** `config/devices.yaml` contiene sintaxis YAML inválida
- **THEN** la aplicación SHALL mostrar un error descriptivo de parseo y terminar

### Requirement: Recolectar métricas SNMP de dispositivos
El sistema SHALL consultar cada dispositivo configurado vía SNMP GET para todos los OIDs definidos en su entrada de configuración.

#### Scenario: Consulta SNMP v2c exitosa
- **WHEN** un dispositivo está configurado con `snmp_version: 2c` y una community string válida
- **THEN** el collector SHALL retornar un resultado con el nombre del dispositivo, cada OID consultado, su valor crudo y una marca de tiempo UTC

#### Scenario: Consulta SNMP v3 exitosa
- **WHEN** un dispositivo está configurado con `snmp_version: 3` y credenciales v3 válidas obtenidas de variables de entorno
- **THEN** el collector SHALL realizar un SNMP GET autenticado y retornar resultados en la misma estructura que v2c

#### Scenario: Dispositivo inalcanzable
- **WHEN** el host de un dispositivo es inalcanzable o agota el tiempo de espera durante la consulta SNMP
- **THEN** el collector SHALL registrar un error para ese dispositivo y retornar un resultado vacío para él, sin interrumpir la recolección de otros dispositivos

#### Scenario: OID no encontrado en el dispositivo
- **WHEN** un OID de la configuración no existe en el dispositivo destino
- **THEN** el collector SHALL registrar una advertencia para ese OID y continuar recolectando los OIDs restantes del dispositivo

### Requirement: Aislar el collector de otras capas
La capa collector SHALL NOT tener conocimiento del almacenamiento ni de la presentación. SHALL retornar resultados SNMP crudos como estructuras de datos simples (dataclass o dict) al llamador.

#### Scenario: El collector retorna datos estructurados
- **WHEN** el collector consulta exitosamente un dispositivo
- **THEN** SHALL retornar una lista de registros, cada uno conteniendo: `device_name`, `oid`, `raw_value`, `timestamp_utc`
