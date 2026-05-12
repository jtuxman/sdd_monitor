## Why

Al monitorear switches Cisco, el operador necesita saber qué interfaces tienen más tráfico acumulado sin tener que acceder al CLI del equipo. Esta información no está disponible en el reporte actual y requiere una consulta puntual bajo demanda, no en cada ciclo de polling.

## What Changes

- Nuevo script CGI `scripts/interfaces.py` que recibe un nombre de dispositivo, ejecuta SNMP WALK sobre la ifXTable del switch y retorna un JSON con las interfaces ordenadas por tráfico total (in + out) en GB
- El HTML generado por `html_report.py` incluye un botón "Ver interfaces" visible únicamente en la vista de foco de dispositivos de tipo `switch`
- Al hacer click, el browser llama al script CGI via `fetch()` y renderiza la tabla de interfaces sin recargar la página
- La consulta SNMP se realiza **solo al hacer click**, no en cada ciclo de polling
- Configuración nginx: activar `fcgiwrap` y agregar bloque `location /cgi-bin/` para ejecutar el script

## Capabilities

### New Capabilities

- `switch-interface-stats`: Consulta on-demand de estadísticas de tráfico por interfaz en switches Cisco via CGI, con resultado embebido dinámicamente en la vista de foco del HTML

### Modified Capabilities

- `html-report`: La vista de foco de un switch incluye ahora un botón que dispara la consulta de interfaces y renderiza su resultado en el DOM

## Impact

- **Nuevos archivos**: `scripts/interfaces.py` (script CGI), `scripts/README.md` (instrucciones nginx)
- **Modificados**: `src/sdd_monitor/html_report.py` (botón + JS fetch + render de tabla)
- **Infraestructura**: nginx requiere `fcgiwrap` instalado y un bloque `location /cgi-bin/` apuntando a `scripts/`
- **Dependencias**: ninguna nueva (`pysnmp` ya es dependencia del proyecto)
- **Sin cambios**: `scheduler.py`, `storage.py`, `models.py`, `__main__.py`, `collector.py`
