## 1. Colector de liveness local

- [x] 1.1 Crear `src/sdd_monitor/collector_liveness.py` con chequeos ICMP (`ping`) y TCP (`443`) usando libreria estandar
- [x] 1.2 Implementar filtrado de dispositivos habilitados para liveness (p. ej. `type: ap` y/o `liveness: true`)
- [x] 1.3 Definir estructura de resultado por dispositivo (`is_up`, `ping_rtt_ms`, `https_up`, `error`, `timestamp_utc`)
- [x] 1.4 Agregar manejo de timeout y errores por dispositivo sin detener el resto de chequeos

## 2. Persistencia y consultas SQLite

- [x] 2.1 Extender `storage.py` para crear tabla de snapshots de liveness de AP
- [x] 2.2 Implementar insercion de snapshots de liveness por ciclo
- [x] 2.3 Implementar consulta del ultimo estado por AP para presentacion

## 3. Integracion al scheduler y configuracion

- [x] 3.1 Integrar collector de liveness en el ciclo de polling sin romper el flujo SNMP existente
- [x] 3.2 Propagar resultados de liveness hacia capas de presentacion (terminal/html)
- [x] 3.3 Actualizar configuracion de dispositivos para marcar APs monitoreados por liveness

## 4. Presentacion terminal y HTML

- [x] 4.1 Actualizar `presentation.py` para mostrar seccion de APs con estado `UP/DOWN`, RTT y HTTPS
- [x] 4.2 Actualizar `html_report.py` para incluir seccion de liveness de APs
- [x] 4.3 Mostrar mensajes informativos cuando no haya datos de liveness

## 5. Pruebas

- [x] 5.1 Agregar tests unitarios para `collector_liveness` (up/down, timeout, errores)
- [x] 5.2 Agregar tests de storage para insercion/consulta de snapshots de liveness
- [x] 5.3 Actualizar tests de scheduler/presentation/html para el nuevo flujo de datos
