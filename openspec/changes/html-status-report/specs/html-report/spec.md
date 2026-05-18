## ADDED Requirements

### Requirement: Generar reporte HTML estático tras cada poll
El sistema SHALL generar un archivo HTML estático al finalizar cada ciclo de polling. La ruta de salida SHALL ser configurable vía la variable de entorno `HTML_PATH`, con valor por defecto `data/report.html`.

#### Scenario: Generación exitosa del HTML
- **WHEN** un ciclo de polling completa con al menos un dispositivo configurado
- **THEN** el sistema SHALL escribir un archivo HTML válido en la ruta definida por `HTML_PATH`, sobreescribiendo el archivo anterior

#### Scenario: Error de escritura en la ruta de salida
- **WHEN** la ruta definida en `HTML_PATH` no tiene permisos de escritura o el directorio no existe
- **THEN** el sistema SHALL registrar el error en el log y continuar el polling sin interrumpir la operación

#### Scenario: HTML_PATH no configurado
- **WHEN** la variable de entorno `HTML_PATH` no está definida
- **THEN** el sistema SHALL usar `data/report.html` como ruta por defecto

### Requirement: Mostrar estado actual por dispositivo
El HTML generado SHALL incluir una sección por cada dispositivo configurado con el último valor recibido para cada OID en el ciclo de polling más reciente. En la cabecera visible de cada tarjeta de dispositivo, el HTML SHALL mostrar el **nombre monitoreado** (el campo `name` definido para el dispositivo en la configuración) y la **dirección de monitoreo** (el valor del campo `host`, de forma que sea identificable la IP o hostname contra el que se hace el poll).

#### Scenario: Estado actual visible
- **WHEN** el HTML es abierto en un browser
- **THEN** SHALL mostrar el nombre monitoreado (`name`), la dirección de monitoreo (`host`), el icono del dispositivo, y para cada OID: la etiqueta legible (o el OID crudo si no hay label), el valor actual y la marca de tiempo UTC del último registro

#### Scenario: OID de uptime muestra tiempo legible
- **WHEN** el label de un OID contiene "uptime" (case-insensitive)
- **THEN** el sistema SHALL convertir el valor de centisegundos a formato legible (Xd Xh Xm) en lugar del número crudo

#### Scenario: Dispositivo sin métricas en el último poll
- **WHEN** un dispositivo no retornó métricas en el ciclo más reciente
- **THEN** el HTML SHALL mostrar el dispositivo con un indicador de error o sin datos, sin omitir la tarjeta del dispositivo

### Requirement: Mostrar historial de métricas con gráfica y selector de rango
El HTML generado SHALL incluir una gráfica de línea por cada OID numérico con un selector de rango temporal (`1h`, `1d`, `3d`, `7d`) que cambia los datos mostrados sin recargar la página. Los datos de cada rango SHALL consultarse desde SQLite y agregarse por bucket de tiempo antes de embeberse en el HTML.

Los buckets de agregación son:
- **1h**: datos crudos (bucket de 1 minuto)
- **1d**: promedio por bucket de 15 minutos
- **3d**: promedio por bucket de 1 hora
- **7d**: promedio por bucket de 4 horas

#### Scenario: Gráfica con historial disponible
- **WHEN** existen 2 o más registros históricos para un OID de un dispositivo en el rango activo
- **THEN** el HTML SHALL renderizar una gráfica de línea con Chart.js mostrando valores en el eje Y y marcas de tiempo en el eje X

#### Scenario: Cambio de rango temporal
- **WHEN** el usuario hace clic en un botón de rango (1h, 1d, 3d, 7d) sobre una gráfica
- **THEN** la gráfica SHALL actualizar sus datos sin recargar la página, marcando el botón seleccionado como activo

#### Scenario: Rango sin datos suficientes
- **WHEN** un rango no tiene 2 o más registros en SQLite
- **THEN** la gráfica SHALL mostrarse vacía para ese rango sin producir error

#### Scenario: OID sin historial suficiente
- **WHEN** ningún rango tiene datos suficientes para un OID
- **THEN** el HTML SHALL mostrar el valor actual sin gráfica

#### Scenario: OID no numérico
- **WHEN** el valor de un OID no es convertible a número (ej. sysDescr es texto)
- **THEN** el HTML SHALL mostrar el valor como texto sin intentar renderizar gráfica

#### Scenario: OID de uptime no muestra gráfica
- **WHEN** el label de un OID contiene "uptime" (case-insensitive)
- **THEN** el HTML SHALL mostrar solo el valor formateado como texto sin renderizar gráfica de historial

### Requirement: Auto-refresh de la página
El HTML generado SHALL incluir un mecanismo de recarga automática del browser alineado con el intervalo de polling configurado, que SHALL suspenderse automáticamente cuando el usuario entre en vista de foco.

#### Scenario: Recarga automática activa en vista general
- **WHEN** el HTML es abierto en un browser y el usuario no ha seleccionado ningún dispositivo
- **THEN** la página SHALL recargarse automáticamente cada `POLL_INTERVAL` segundos via `<meta http-equiv="refresh">`

#### Scenario: Auto-refresh suspendido en vista de foco
- **WHEN** el usuario entra en la vista de foco de un dispositivo
- **THEN** el auto-refresh SHALL quedar suspendido para ese dispositivo y el usuario podrá analizar las gráficas sin interrupciones

### Requirement: Vista de foco por dispositivo
El HTML generado SHALL permitir que el usuario haga click en la tarjeta de cualquier dispositivo para ver solo ese dispositivo en pantalla completa, con el auto-refresh suspendido para análisis sin interrupciones.

#### Scenario: Entrar en vista de foco
- **WHEN** el usuario hace click en la tarjeta de un dispositivo
- **THEN** la página SHALL ocultar todas las demás tarjetas de dispositivos, mostrar únicamente la tarjeta del dispositivo seleccionado en modo expandido, suspender el auto-refresh y mostrar un botón de retorno visible

#### Scenario: Retornar a vista general
- **WHEN** el usuario hace click en el botón de retorno estando en vista de foco
- **THEN** la página SHALL restaurar la vista general con todas las tarjetas visibles y reactivar el auto-refresh

#### Scenario: Vista de foco persistida por URL hash
- **WHEN** el usuario entra en vista de foco de un dispositivo
- **THEN** la URL SHALL actualizarse con un hash (`#<device-name>`) de forma que al recargar manualmente la página se restaure la vista de foco del mismo dispositivo

#### Scenario: Vista de foco al cargar con hash en URL
- **WHEN** el HTML se carga con un hash en la URL que corresponde a un dispositivo existente
- **THEN** la página SHALL entrar directamente en vista de foco de ese dispositivo sin mostrar la vista general

### Requirement: Icono por tipo de dispositivo
El HTML generado SHALL mostrar un icono distinto por cada dispositivo según el valor del campo `type` definido en `devices.yaml`.

#### Scenario: Tipo de dispositivo reconocido
- **WHEN** un dispositivo tiene `type: switch`, `router`, `server` o `firewall`
- **THEN** el HTML SHALL mostrar el emoji correspondiente junto al nombre del dispositivo

#### Scenario: Tipo de dispositivo ausente o desconocido
- **WHEN** un dispositivo no tiene campo `type` o tiene un valor no reconocido
- **THEN** el HTML SHALL mostrar un icono genérico de red (📡) sin error
