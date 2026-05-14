## ADDED Requirements

### Requirement: Consultar estadísticas de interfaces de un switch via CGI
El sistema SHALL proveer un script CGI en `scripts/interfaces.py` que, al recibir el parámetro `device=<nombre>`, realice un SNMP WALK sobre la ifXTable del switch correspondiente y retorne un JSON con las estadísticas de todas sus interfaces.

#### Scenario: Consulta exitosa
- **WHEN** el script CGI recibe `?device=<nombre>` y el switch responde al SNMP WALK
- **THEN** el script SHALL retornar un JSON con Content-Type `application/json` que contenga un array de interfaces con los campos: `name`, `alias`, `in_gb`, `out_gb`, `total_gb`, `status` (`up` o `down`), ordenado por `total_gb` descendente con interfaces `down` al final

#### Scenario: Dispositivo no encontrado en configuración
- **WHEN** el parámetro `device` no corresponde a ningún dispositivo en `config/devices.yaml`
- **THEN** el script SHALL retornar HTTP 404 con JSON `{"error": "device not found"}`

#### Scenario: Dispositivo no es switch
- **WHEN** el dispositivo existe en `config/devices.yaml` pero su `type` no es `switch`
- **THEN** el script SHALL retornar HTTP 400 con JSON `{"error": "device is not a switch"}`

#### Scenario: Timeout o error SNMP
- **WHEN** el switch no responde dentro del timeout configurado o retorna un error SNMP
- **THEN** el script SHALL retornar HTTP 502 con JSON `{"error": "<mensaje del error>"}`

#### Scenario: Fallback a contadores de 32 bits
- **WHEN** el WALK de `ifHCInOctets` no retorna datos para el switch
- **THEN** el script SHALL intentar el WALK de `ifInOctets` e `ifOutOctets` como alternativa

### Requirement: Conversión de octets a unidad legible
El script CGI SHALL convertir los valores de octets (ifHCInOctets, ifHCOutOctets) a gigabytes con 2 decimales. La presentación en el HTML SHALL mostrar el valor en TB cuando supere los 1000 GB, manteniendo el valor en GB en el JSON para preservar el ordenamiento correcto.

#### Scenario: Conversión de octets a GB
- **WHEN** el WALK retorna un valor de octets para una interfaz
- **THEN** el script SHALL calcular `gb = octets / 1_073_741_824` y redondearlo a 2 decimales, retornando el valor numérico en GB en el JSON

#### Scenario: Presentación en TB cuando el valor supera 1000 GB
- **WHEN** el valor de una columna (In, Out o Total) es mayor o igual a 1000 GB
- **THEN** el HTML SHALL mostrar el valor dividido entre 1024 con 2 decimales y la unidad "TB" en lugar de "GB"

#### Scenario: Presentación en GB cuando el valor es menor a 1000 GB
- **WHEN** el valor de una columna (In, Out o Total) es menor a 1000 GB
- **THEN** el HTML SHALL mostrar el valor con 2 decimales y la unidad "GB"
