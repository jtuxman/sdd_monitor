## MODIFIED Requirements

### Requirement: Cargar configuración de dispositivos desde YAML
El sistema SHALL cargar todos los parámetros de dispositivos (nombre, host, versión SNMP, community string, OIDs, tipo de dispositivo) desde `config/devices.yaml` al iniciar. Ningún parámetro de red SHALL estar hardcodeado en el código fuente. El campo `oids` SHALL aceptar tanto strings simples (OID crudo) como objetos con campos `oid` y `label`. El campo `type` del dispositivo es opcional.

#### Scenario: YAML válido cargado al iniciar
- **WHEN** la aplicación inicia y `config/devices.yaml` existe y es válido
- **THEN** el collector SHALL tener una lista de dispositivos con sus OIDs asociados listos para consultar

#### Scenario: Archivo de configuración ausente
- **WHEN** `config/devices.yaml` no existe
- **THEN** la aplicación SHALL mostrar un mensaje de error claro y terminar sin intentar consultas SNMP

#### Scenario: YAML malformado
- **WHEN** `config/devices.yaml` contiene sintaxis YAML inválida
- **THEN** la aplicación SHALL mostrar un error descriptivo de parseo y terminar

#### Scenario: OID definido como string simple
- **WHEN** un OID en la lista `oids` es un string (ej. `"1.3.6.1.2.1.1.1.0"`)
- **THEN** el collector SHALL tratarlo como OID válido usando el string crudo como label

#### Scenario: OID definido como objeto con label
- **WHEN** un OID en la lista `oids` es un objeto con campos `oid` y `label`
- **THEN** el collector SHALL usar el valor de `oid` para la consulta SNMP y `label` como nombre legible del OID

#### Scenario: Dispositivo con campo type definido
- **WHEN** un dispositivo tiene el campo `type` con valor `switch`, `router`, `server` o `firewall`
- **THEN** el collector SHALL incluir ese valor en los datos del dispositivo disponibles para otras capas

#### Scenario: Dispositivo sin campo type
- **WHEN** un dispositivo no tiene el campo `type`
- **THEN** el collector SHALL tratar el tipo como ausente sin producir error
