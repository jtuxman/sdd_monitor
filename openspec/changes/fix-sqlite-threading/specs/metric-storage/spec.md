## MODIFIED Requirements

### Requirement: Persistir métricas en SQLite
El sistema SHALL almacenar cada métrica recolectada en una base de datos SQLite local. El archivo de base de datos SHALL ser configurable vía variable de entorno. La conexión SQLite SHALL crearse y cerrarse dentro del mismo hilo que ejecuta la inserción, nunca compartirse entre hilos.

#### Scenario: Almacenamiento exitoso de métricas
- **WHEN** el processor entrega un conjunto de métricas normalizadas al storage
- **THEN** el storage SHALL insertar cada métrica como un registro en la tabla correspondiente, incluyendo: nombre del dispositivo, OID, valor normalizado y marca de tiempo UTC

#### Scenario: Creación automática del esquema
- **WHEN** la aplicación inicia y la base de datos SQLite no existe aún
- **THEN** el storage SHALL crear el archivo de base de datos y las tablas necesarias automáticamente

#### Scenario: Base de datos ya existente
- **WHEN** la aplicación inicia y ya existe una base de datos con el esquema correcto
- **THEN** el storage SHALL conectarse y agregar nuevos registros sin modificar los existentes

#### Scenario: Conexión creada y cerrada en el mismo hilo
- **WHEN** el ciclo de polling se ejecuta en un hilo secundario
- **THEN** la conexión SQLite SHALL abrirse y cerrarse dentro de ese mismo hilo, sin reutilizar conexiones creadas en otros hilos
