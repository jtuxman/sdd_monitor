## ADDED Requirements

### Requirement: Botón de consulta de interfaces en vista de foco de switch
El HTML generado SHALL incluir un botón "Ver interfaces" visible únicamente dentro de la vista de foco de dispositivos con `type: switch`. Al hacer click, el botón SHALL disparar una consulta al script CGI y renderizar la tabla de interfaces en el DOM sin recargar la página.

#### Scenario: Botón visible solo en switches
- **WHEN** el usuario entra en la vista de foco de un dispositivo con `type: switch`
- **THEN** el HTML SHALL mostrar el botón "Ver interfaces" dentro de la tarjeta del dispositivo

#### Scenario: Botón ausente en dispositivos que no son switch
- **WHEN** el usuario entra en la vista de foco de un dispositivo con `type` distinto a `switch`
- **THEN** el HTML SHALL no mostrar ningún botón de interfaces

#### Scenario: Click en botón con respuesta exitosa
- **WHEN** el usuario hace click en "Ver interfaces" y el CGI retorna datos
- **THEN** el HTML SHALL renderizar una tabla con columnas: Interfaz, Descripción, Entrada (GB), Salida (GB), Total (GB), Estado; ordenada por Total descendente con interfaces `down` al final marcadas visualmente en rojo

#### Scenario: Tabla de interfaces se limpia al salir de la vista de foco
- **WHEN** el usuario hace click en "← Volver" para regresar a la vista general
- **THEN** el HTML SHALL limpiar la tabla de interfaces y restaurar el botón a su estado inicial ("Ver interfaces") para que la siguiente vez que se entre en foco el dispositivo se muestre sin datos previos cargados

#### Scenario: Click en botón con error del CGI
- **WHEN** el usuario hace click en "Ver interfaces" y el CGI retorna un error o no está disponible
- **THEN** el HTML SHALL mostrar un mensaje de error descriptivo en lugar de la tabla, sin romper el resto de la vista de foco

#### Scenario: Estado de carga durante la consulta
- **WHEN** el usuario hace click en "Ver interfaces" y la consulta está en curso
- **THEN** el HTML SHALL mostrar un indicador de carga hasta recibir la respuesta del CGI
