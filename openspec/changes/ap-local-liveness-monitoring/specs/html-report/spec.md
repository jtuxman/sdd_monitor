## ADDED Requirements

### Requirement: Vista principal de AP con estado resumido e indicador de caida reciente
La pagina principal SHALL mantener una vista resumida de APs mostrando estado actual (`UP`/`DOWN`) sin desplegar por defecto la grafica historica de liveness. Cuando un AP haya perdido contacto al menos una vez en ultimas 72 horas, SHALL mostrar un indicador visual de advertencia.

#### Scenario: AP estable en ultimas 72 horas
- **WHEN** el AP no tiene snapshots `is_up = false` en ultimas 72 horas
- **THEN** la tarjeta principal SHALL mostrar solo el estado actual sin badge de advertencia

#### Scenario: AP con perdida de contacto reciente
- **WHEN** el AP tiene uno o mas snapshots `is_up = false` en ultimas 72 horas
- **THEN** la tarjeta principal SHALL mostrar un badge visual (ej. `Caida en 72h`) para invitar al usuario a revisar el detalle

### Requirement: Grafica historica de liveness en vista enfocada de AP
En la vista detallada/enfocada de un AP, el HTML SHALL mostrar una grafica de disponibilidad historica con selector de rango temporal (`1h`, `1d`, `3d`, `7d`) equivalente al flujo de switches.

#### Scenario: Render de grafica con historial
- **WHEN** existen snapshots de liveness para el AP en el rango activo
- **THEN** el HTML SHALL renderizar una serie temporal de disponibilidad (`1 = up`, `0 = down`) con eje X en tiempo y eje Y en estado

#### Scenario: Cambio de rango temporal en liveness
- **WHEN** el usuario selecciona otro rango (`1h`, `1d`, `3d`, `7d`) en la grafica de liveness
- **THEN** la grafica SHALL actualizarse sin recargar la pagina, usando los datos correspondientes al rango

#### Scenario: Rango por defecto de liveness para AP
- **WHEN** el usuario entra al detalle de liveness de un AP por primera vez
- **THEN** la grafica SHALL inicializarse por defecto en el rango `3d` para facilitar la deteccion rapida de caidas recientes

#### Scenario: Rango sin datos de liveness
- **WHEN** el AP no tiene snapshots en el rango seleccionado
- **THEN** el HTML SHALL mostrar la grafica vacia o un mensaje "sin datos" sin producir error
