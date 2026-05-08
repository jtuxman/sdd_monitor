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
El HTML generado SHALL incluir una sección por cada dispositivo configurado con el último valor recibido para cada OID en el ciclo de polling más reciente.

#### Scenario: Estado actual visible
- **WHEN** el HTML es abierto en un browser
- **THEN** SHALL mostrar el nombre del dispositivo, su icono, y para cada OID: la etiqueta legible (o el OID crudo si no hay label), el valor actual y la marca de tiempo UTC del último registro

#### Scenario: Dispositivo sin métricas en el último poll
- **WHEN** un dispositivo no retornó métricas en el ciclo más reciente
- **THEN** el HTML SHALL mostrar el dispositivo con un indicador de error o sin datos, sin omitir la tarjeta del dispositivo

### Requirement: Mostrar historial de métricas con gráfica
El HTML generado SHALL incluir una gráfica de línea por cada OID numérico, mostrando los últimos 20 registros históricos obtenidos desde el almacenamiento SQLite.

#### Scenario: Gráfica con historial disponible
- **WHEN** existen 2 o más registros históricos para un OID de un dispositivo
- **THEN** el HTML SHALL renderizar una gráfica de línea con Chart.js mostrando los valores en el eje Y y las marcas de tiempo en el eje X

#### Scenario: OID sin historial suficiente
- **WHEN** existe menos de 2 registros históricos para un OID
- **THEN** el HTML SHALL mostrar el valor actual sin gráfica, o una gráfica con un solo punto

#### Scenario: OID no numérico
- **WHEN** el valor de un OID no es convertible a número (ej. sysDescr es texto)
- **THEN** el HTML SHALL mostrar el valor como texto sin intentar renderizar gráfica

### Requirement: Auto-refresh de la página
El HTML generado SHALL incluir un mecanismo de recarga automática del browser alineado con el intervalo de polling configurado.

#### Scenario: Recarga automática activa
- **WHEN** el HTML es abierto en un browser
- **THEN** la página SHALL recargarse automáticamente cada `POLL_INTERVAL` segundos via `<meta http-equiv="refresh">`

### Requirement: Icono por tipo de dispositivo
El HTML generado SHALL mostrar un icono distinto por cada dispositivo según el valor del campo `type` definido en `devices.yaml`.

#### Scenario: Tipo de dispositivo reconocido
- **WHEN** un dispositivo tiene `type: switch`, `router`, `server` o `firewall`
- **THEN** el HTML SHALL mostrar el emoji correspondiente junto al nombre del dispositivo

#### Scenario: Tipo de dispositivo ausente o desconocido
- **WHEN** un dispositivo no tiene campo `type` o tiene un valor no reconocido
- **THEN** el HTML SHALL mostrar un icono genérico de red (📡) sin error
