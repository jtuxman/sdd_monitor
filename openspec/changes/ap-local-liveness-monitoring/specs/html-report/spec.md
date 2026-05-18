## ADDED Requirements

### Requirement: Vista principal de AP con estado, grafica e indicador de caida reciente
La pagina principal SHALL mostrar cada AP con estado actual (`UP`/`DOWN`), su grafica historica de liveness visible y un indicador visual de advertencia cuando haya habido perdida de contacto en ultimas 72 horas. Cada tarjeta de AP SHALL mostrar de forma visible el nombre monitoreado del dispositivo (`name` en la configuracion) y la direccion de monitoreo (`host`, IP o hostname segun la configuracion).

#### Scenario: Identificacion del AP en la tarjeta
- **WHEN** la pagina principal muestra una tarjeta de AP
- **THEN** el HTML SHALL renderizar el nombre monitoreado (`name`) y el valor de `host` de ese AP de forma claramente visible junto al estado y la grafica

#### Scenario: AP estable en ultimas 72 horas
- **WHEN** el AP no tiene snapshots `is_up = false` en ultimas 72 horas
- **THEN** la tarjeta principal SHALL mostrar solo el estado actual sin badge de advertencia

#### Scenario: AP con perdida de contacto reciente
- **WHEN** el AP tiene uno o mas snapshots `is_up = false` en ultimas 72 horas
- **THEN** la tarjeta principal SHALL mostrar un badge visual (ej. `Caida en 72h`) para invitar al usuario a revisar el detalle

#### Scenario: Grafica visible en la pagina principal
- **WHEN** la pagina principal carga con datos de liveness de AP
- **THEN** cada tarjeta de AP SHALL mostrar su grafica de disponibilidad sin requerir entrar a vista enfocada

### Requirement: Grafica historica de liveness en vista enfocada de AP
En la vista detallada/enfocada de un AP, el HTML SHALL mostrar una grafica de disponibilidad historica con selector de rango temporal (`1h`, `1d`, `3d`, `7d`) equivalente al flujo de switches.

#### Scenario: Render de grafica con historial
- **WHEN** existen snapshots de liveness para el AP en el rango activo
- **THEN** el HTML SHALL renderizar una serie temporal de disponibilidad (`1 = up`, `0 = down`) con eje X en tiempo y eje Y en estado

#### Scenario: Cambio de rango temporal en liveness
- **WHEN** el usuario selecciona otro rango (`1h`, `1d`, `3d`, `7d`) en la grafica de liveness
- **THEN** la grafica SHALL actualizarse sin recargar la pagina, usando los datos correspondientes al rango

#### Scenario: Rango por defecto de liveness para AP
- **WHEN** la grafica de liveness de un AP se renderiza (en home o en vista enfocada) por primera vez
- **THEN** la grafica SHALL inicializarse por defecto en el rango `3d` para facilitar la deteccion rapida de caidas recientes

#### Scenario: Click en AP abre vista individual
- **WHEN** el usuario hace click sobre una tarjeta de AP en la pagina principal
- **THEN** la pagina SHALL entrar en vista individual (focus mode) del AP seleccionado, con el mismo comportamiento de navegacion usado para switches

#### Scenario: Rango sin datos de liveness
- **WHEN** el AP no tiene snapshots en el rango seleccionado
- **THEN** el HTML SHALL mostrar la grafica vacia o un mensaje "sin datos" sin producir error

#### Scenario: Codificacion visual de estado en la grafica
- **WHEN** la grafica de liveness renderiza puntos o segmentos con valor `DOWN (0)`
- **THEN** esos puntos/segmentos SHALL mostrarse en color rojo para destacar la caida

#### Scenario: Codificacion visual de disponibilidad
- **WHEN** la grafica de liveness renderiza puntos o segmentos con valor `UP (1)`
- **THEN** esos puntos/segmentos SHALL mostrarse en color verde para indicar disponibilidad

#### Scenario: Linea continua y area rellena como switches
- **WHEN** la grafica de liveness de AP se renderiza
- **THEN** SHALL usar linea con `tension` suave, puntos conectados (`spanGaps: true` donde aplique) y area semitransparente bajo la curva (`fill: true`), alineado al estilo de las graficas SNMP de switches

#### Scenario: Relleno que marca caidas
- **WHEN** un segmento de la serie cruza o permanece en `DOWN (0)`
- **THEN** el area bajo ese tramo SHALL distinguirse visualmente (p. ej. tinte rojo semitransparente) frente a los tramos `UP (1)` (tinte verde semitransparente), coherente con los colores de linea/puntos ya definidos
