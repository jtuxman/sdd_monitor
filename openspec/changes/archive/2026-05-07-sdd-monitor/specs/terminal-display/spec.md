## ADDED Requirements

### Requirement: Mostrar métricas en terminal usando Rich
El sistema SHALL presentar las métricas recolectadas en terminal con formato enriquecido usando la librería `rich`. La salida SHALL ser legible e identificar claramente el dispositivo, el OID y el valor de cada métrica.

#### Scenario: Visualización de métricas de un poll
- **WHEN** se completa un ciclo de recolección con métricas disponibles
- **THEN** la capa de presentación SHALL mostrar una tabla o panel por dispositivo con columnas para: nombre del dispositivo, OID, valor y marca de tiempo

#### Scenario: Sin métricas disponibles
- **WHEN** un ciclo de recolección no produce métricas (todos los dispositivos fallaron)
- **THEN** la presentación SHALL mostrar un mensaje informativo indicando que no hay métricas disponibles, sin producir error

#### Scenario: Error de dispositivo visible en terminal
- **WHEN** un dispositivo falló durante la recolección
- **THEN** la presentación SHALL mostrar el nombre del dispositivo y el motivo del error de forma distinguible visualmente (ej. color rojo o ícono de advertencia)

### Requirement: Aislar la presentación de otras capas
La capa de presentación SHALL NOT acceder directamente a la base de datos ni al collector. SHALL recibir únicamente los datos ya procesados como estructuras simples y formatearlos para la salida.

#### Scenario: Presentación recibe datos estructurados
- **WHEN** la capa de presentación es invocada
- **THEN** SHALL aceptar como entrada una lista de registros de métricas (estructuras simples) y renderizarlos sin realizar operaciones de red ni de base de datos
