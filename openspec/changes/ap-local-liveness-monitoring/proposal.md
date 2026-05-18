## Why

El monitoreo basado en Meraki Dashboard puede tardar minutos en reflejar la caida de un Access Point, lo cual retrasa la respuesta operativa. Se requiere un chequeo local de disponibilidad para detectar caidas en tiempo cercano a real desde la red donde estan los equipos.

## What Changes

- Nuevo flujo de monitoreo local de APs por `ping` (ICMP) y verificacion de puerto `443/TCP`
- Nueva configuracion en `devices.yaml` para marcar equipos tipo AP que deban monitorearse por liveness local
- Registro en SQLite del estado de disponibilidad (`up/down`), latencia y timestamp del ultimo chequeo
- Integracion al scheduler existente para ejecutar chequeos de liveness en cada ciclo sin bloquear el pipeline principal
- Seccion dedicada en terminal y HTML para APs con estado actual, latencia y tiempo desde ultimo `up`
- Historial de liveness de AP con graficas por rango temporal (`1h`, `1d`, `3d`, `7d`) para ver periodos sin respuesta
- Indicador visual en la pagina principal cuando un AP perdio contacto en algun momento de las ultimas 72 horas
- En la pagina principal, cada AP se muestra con su grafica de liveness visible por defecto en `3d`; al hacer click entra a vista individual (mismo patron de interaccion que switches)
- Reporte HTML: en cada tarjeta (SNMP, error sin respuesta, AP liveness) mostrar el nombre monitoreado del dispositivo y la direccion configurada en `host` (IP o hostname)
- Manejo de fallas de red por dispositivo sin detener ciclos futuros

## Capabilities

### New Capabilities
- `ap-local-liveness`: Deteccion local de disponibilidad de Access Points mediante ICMP y chequeo de servicio HTTPS

### Modified Capabilities
- `metric-storage`: Agregar persistencia de eventos/snapshots de disponibilidad para APs
- `poll-scheduling`: Extender el ciclo periodico para ejecutar chequeos de liveness local de APs
- `terminal-display`: Mostrar estado de APs (`up/down`), latencia y ultima vez visto en consola
- `html-report`: Mostrar APs en home con grafica de liveness visible (default `3d`), mantener indicador de perdida reciente y soportar vista individual al click; en todas las tarjetas relevantes, mostrar nombre monitoreado (`name`) y direccion de monitoreo (`host`)

## Impact

- **Nuevos archivos**: `src/sdd_monitor/collector_liveness.py` (o modulo equivalente), tests de collector liveness
- **Modificados**: `src/sdd_monitor/scheduler.py`, `src/sdd_monitor/storage.py`, `src/sdd_monitor/presentation.py`, `src/sdd_monitor/html_report.py`, `config/devices.yaml`
- **Base de datos**: nueva tabla para snapshots de disponibilidad AP
- **Dependencias**: preferir libreria estandar (`subprocess` + `socket`) para evitar nuevas dependencias
- **Variables de entorno opcionales**: timeout de ping/tcp y numero de intentos por ciclo
