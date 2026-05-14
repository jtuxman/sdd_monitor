## Context

SDD Monitor hoy recolecta metricas SNMP periodicas y las presenta en terminal/HTML, pero no tiene un mecanismo rapido de deteccion de disponibilidad para Access Points. El usuario necesita saber en segundos si un AP esta vivo desde la red local, sin depender de dashboards cloud con latencia de varios minutos.

El cambio cruza multiples modulos (collector, scheduler, storage, presentation y reporte HTML) y agrega un nuevo tipo de dato operacional (liveness), por lo que requiere diseno explicito antes de implementacion.

## Goals / Non-Goals

**Goals:**
- Detectar estado de AP (`up`/`down`) localmente por ciclo de polling.
- Medir latencia ICMP cuando el host responde.
- Verificar disponibilidad de servicio HTTPS (`tcp/443`) por AP.
- Persistir snapshots de liveness en SQLite para consulta y render.
- Mostrar estado de APs en terminal y HTML en una seccion dedicada.
- Mantener el scheduler resiliente: fallas por AP no detienen ciclos futuros.

**Non-Goals:**
- Integracion con Meraki Dashboard API.
- Alertamiento por correo/telegram/slack.
- Descubrimiento automatico de APs.
- Reemplazar el pipeline SNMP existente para switches/routers.
- Monitoreo avanzado de radios/SSID/canales en esta iteracion.

## Decisions

### 1. Estrategia de liveness: ICMP + TCP 443
**Decision**: ejecutar dos chequeos por AP en cada ciclo: (a) ping ICMP para alcance y RTT, (b) conexion TCP al puerto 443 para verificar servicio de gestion web.
**Rationale**: ping solo no valida disponibilidad del servicio, y TCP solo no da latencia de red. La combinacion da mejor diagnostico operativo con bajo costo.
**Alternatives considered**:
- Solo ICMP: mas simple, pero ciego ante falla de servicio HTTPS.
- Solo TCP 443: no entrega RTT ICMP y puede fallar por ACL aun cuando el equipo responde a ping.

### 2. Implementacion sin nuevas dependencias
**Decision**: usar libreria estandar (`subprocess` para ping y `socket` para TCP) en lugar de dependencias externas.
**Rationale**: reduce complejidad de despliegue y evita cambios de empaquetado.
**Alternatives considered**:
- `pythonping`/`scapy`: mas control, pero aumenta superficie de dependencias y permisos.

### 3. Modelo de estado por ciclo
**Decision**: guardar un snapshot por AP por ciclo con campos: `device_name`, `is_up`, `ping_rtt_ms`, `https_up`, `error`, `timestamp_utc`.
**Rationale**: modelo simple para vistas actuales y potencial historico basico.
**Alternatives considered**:
- Guardar solo ultimo estado en memoria: se pierde trazabilidad entre reinicios.
- Guardar eventos de cambio exclusivamente: mas compacto, pero complica consultas de estado actual.

### 4. Integracion al scheduler en ruta no bloqueante del pipeline principal
**Decision**: ejecutar liveness despues del collector SNMP y antes de presentation/html, capturando errores por AP para no romper el ciclo.
**Rationale**: permite que la salida de terminal/HTML muestre en el mismo tick tanto metricas SNMP como salud de AP.
**Alternatives considered**:
- Job separado en APScheduler: desacopla, pero puede desalinear timestamps y agregar complejidad de coordinacion.

### 5. Configuracion por dispositivo
**Decision**: reutilizar `devices.yaml` con un flag opt-in (ej. `liveness: true`) y aplicarlo principalmente a `type: ap` o equipos seleccionados.
**Rationale**: evita un segundo inventario de dispositivos y mantiene una sola fuente de verdad.
**Alternatives considered**:
- Archivo aparte de APs: mayor duplicacion y riesgo de drift de configuracion.

## Risks / Trade-offs

- **Ping no permitido por firewall/ACL** -> marcar `ping` como fallido pero continuar con check TCP 443; reflejar ambos estados por separado.
- **Comando `ping` con diferencias por SO** -> encapsular parser y parametros para Linux (scope actual del servidor).
- **Aumento de duracion del ciclo por muchos APs** -> aplicar timeout corto por check y ejecucion concurrente acotada.
- **Falsos negativos transitorios** -> registrar error detallado por ciclo y considerar futuras ventanas de confirmacion (fuera de alcance actual).

## Migration Plan

1. Extender esquema SQLite con tabla de liveness (crear automaticamente si no existe).
2. Actualizar `devices.yaml` para marcar APs a monitorear por liveness.
3. Desplegar version nueva del monitor.
4. Verificar en terminal y HTML la nueva seccion de APs.
5. Rollback: deshabilitar `liveness` en dispositivos o regresar a version previa; el resto del pipeline SNMP permanece operativo.

## Open Questions

- Definir umbral exacto de timeout para ping y TCP (p.ej. 1s o 2s).
- Definir si `is_up` final debe requerir ambos checks exitosos o solo uno.
- Confirmar nombre final del tipo de dispositivo en config (`ap` vs `access-point`).
