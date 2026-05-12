## 1. Script CGI — SNMP WALK de interfaces

- [x] 1.1 Crear `scripts/interfaces.py` con shebang `#!/usr/bin/env python3` y lógica CGI básica: leer `QUERY_STRING`, parsear parámetro `device`, retornar JSON con headers HTTP correctos
- [x] 1.2 Implementar `load_device(name)` que lee `config/devices.yaml` y retorna el dict del dispositivo o `None` si no existe; retornar 404 si no encontrado, 400 si `type != switch`
- [x] 1.3 Implementar `walk_interfaces(host, community, port, timeout)` usando `pysnmp` `nextCmd` sobre `ifXTable` (ifName, ifHCInOctets, ifHCOutOctets, ifOperStatus, ifAlias) agrupando por índice de interfaz
- [x] 1.4 Implementar fallback: si `ifHCInOctets` no retorna datos, repetir WALK con `ifInOctets` e `ifOutOctets` de ifTable
- [x] 1.5 Implementar `octets_to_gb(octets) -> float` que calcula `octets / 1_073_741_824` redondeado a 2 decimales
- [x] 1.6 Construir el array de resultado ordenado: interfaces `up` por `total_gb` desc, luego interfaces `down` por `total_gb` desc; serializar como JSON y escribir a stdout
- [x] 1.7 Envolver la lógica principal en try/except para capturar timeouts y errores SNMP y retornar HTTP 502 con JSON de error

## 2. Documentación de instalación nginx

- [x] 2.1 Crear `scripts/README.md` con instrucciones para: instalar `fcgiwrap`, agregar bloque `location /cgi-bin/` en nginx apuntando a la carpeta `scripts/`, dar permisos de ejecución a `interfaces.py`, y recargar nginx

## 3. Integración en html_report.py

- [x] 3.1 En `_build_device_card`, agregar el botón "Ver interfaces" (con `data-device="<name>"`) solo cuando el device tenga `type == switch`; incluir un `<div class="iface-result">` vacío donde se inyectará la tabla
- [x] 3.2 Implementar `_build_interfaces_js()` que retorna el bloque JS con: handler del click en el botón, `fetch('/cgi-bin/interfaces.py?device=<name>')`, indicador de carga, render de la tabla HTML con las columnas especificadas e inyección en `div.iface-result`, y manejo de errores con mensaje descriptivo
- [x] 3.3 Agregar CSS para la tabla de interfaces: `.iface-table`, filas con `status-down` en rojo tenue, columna Total en negrita, estado visual del botón durante la carga
- [x] 3.4 Llamar a `_build_interfaces_js()` desde `generate()` e incluir el resultado en el HTML generado
