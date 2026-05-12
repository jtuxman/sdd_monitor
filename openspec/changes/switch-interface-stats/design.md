## Context

SDD Monitor genera un HTML estático servido por nginx. La vista de foco de un switch muestra métricas de polling periódico, pero no tiene acceso al tráfico por interfaz porque ese dato requiere un SNMP WALK (consulta de tabla), no un GET de OID individual. El operador quiere consultar ese dato de forma puntual, sin cargarlo en cada ciclo de polling.

## Goals / Non-Goals

**Goals:**
- Consulta on-demand de estadísticas de interfaz al hacer click en un botón dentro de la vista de foco de un switch
- Mostrar todas las interfaces del switch ordenadas por tráfico total (in + out) en GB, descendente
- Usar OIDs de 64 bits (ifXTable) para correcta representación en switches Cisco de alta velocidad
- Script CGI independiente del proceso sdd_monitor principal

**Non-Goals:**
- Persistencia histórica de estadísticas de interfaces
- Consulta automática en cada ciclo de polling
- Soporte para dispositivos que no sean `type: switch`
- Autenticación o control de acceso al endpoint CGI
- Soporte SNMPv3

## Decisions

### 1. CGI script vs HTTP server embebido en sdd_monitor
**Decisión**: Script CGI independiente (`scripts/interfaces.py`) ejecutado por nginx via `fcgiwrap`.
**Razón**: No requiere cambios en el proceso principal, no agrega threads ni puertos, y nginx ya está corriendo. El script es stateless y se activa solo al recibir una petición.
**Alternativa descartada**: HTTP server embebido — añade complejidad al proceso principal y requiere gestión de threads y puertos adicionales.

### 2. ifTable (32-bit) vs ifXTable (64-bit)
**Decisión**: `ifXTable` — `ifHCInOctets` (1.3.6.1.2.1.31.1.1.1.6.X) e `ifHCOutOctets` (1.3.6.1.2.1.31.1.1.1.10.X).
**Razón**: Los contadores de 32-bit (`ifInOctets`/`ifOutOctets`) se desbordan en ~4GB — en un switch Cisco de 1Gbps se desborda cada 34 segundos de tráfico sostenido. Los contadores de 64-bit no se desbordan en la práctica.
**Alternativa descartada**: `ifInOctets`/`ifOutOctets` — inviable para interfaces de alta velocidad.

### 3. Nombre de interfaz: ifName vs ifDescr vs ifAlias
**Decisión**: `ifName` (1.3.6.1.2.1.31.1.1.1.1.X) como identificador principal, `ifAlias` (1.3.6.1.2.1.31.1.1.1.18.X) como descripción secundaria si existe.
**Razón**: `ifName` da el nombre corto canónico del IOS (Gi0/1, Te1/1). `ifDescr` da el nombre largo de hardware. `ifAlias` es la descripción libre configurada por el admin (ej. "Uplink SW-Core") y aporta contexto operativo.
**Alternativa descartada**: Solo `ifDescr` — verboso y no corresponde al nombre que usan los operadores.

### 4. Identificación del dispositivo en el CGI
**Decisión**: El browser envía el nombre del dispositivo (`?device=switch-core`), el script CGI busca sus credenciales (host, community, port) en `config/devices.yaml`.
**Razón**: Las credenciales SNMP no se exponen en la URL ni en el HTML. El nombre del dispositivo es suficiente para identificar la entrada en el YAML.

### 5. Ordenamiento de interfaces
**Decisión**: Ordenar por `total_bytes = hc_in + hc_out` descendente. Mostrar valor en GB con 2 decimales. Interfaces con `ifOperStatus = down` se muestran al final, marcadas visualmente.
**Razón**: Las interfaces con más tráfico son las de mayor interés operativo. Las interfaces down son menos relevantes pero no deben ocultarse.

## Risks / Trade-offs

- **fcgiwrap no instalado en el servidor** → El script no ejecuta. Mitigación: `scripts/README.md` incluye instrucciones de instalación.
- **Switch sin soporte ifXTable** → El WALK retorna vacío. Mitigación: el script hace fallback a `ifInOctets`/`ifOutOctets` si `ifHCInOctets` no retorna datos.
- **Timeout en SNMP WALK** → El browser queda esperando. Mitigación: timeout configurable en el script (default 5s); el browser muestra error si el fetch falla.
- **Muchas interfaces (48+)** → La tabla puede ser larga. Mitigación: aceptable, el usuario puede hacer scroll en la vista de foco.

## Migration Plan

1. Copiar `scripts/interfaces.py` al servidor
2. Instalar `fcgiwrap`: `sudo apt install fcgiwrap`
3. Agregar bloque `location /cgi-bin/` en la config nginx (ver `scripts/README.md`)
4. Recargar nginx: `sudo nginx -s reload`
5. Sin rollback especial: si se elimina el bloque nginx, el botón falla silenciosamente con un mensaje de error en el HTML
