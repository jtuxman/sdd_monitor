# metric-storage Specification

## Purpose
TBD - created by archiving change sdd-monitor. Update Purpose after archive.
## Requirements
### Requirement: Persistir métricas en SQLite
El sistema SHALL almacenar cada métrica recolectada en una base de datos SQLite local. El archivo de base de datos SHALL ser configurable vía variable de entorno.

#### Scenario: Almacenamiento exitoso de métricas
- **WHEN** el processor entrega un conjunto de métricas normalizadas al storage
- **THEN** el storage SHALL insertar cada métrica como un registro en la tabla correspondiente, incluyendo: nombre del dispositivo, OID, valor normalizado y marca de tiempo UTC

#### Scenario: Creación automática del esquema
- **WHEN** la aplicación inicia y la base de datos SQLite no existe aún
- **THEN** el storage SHALL crear el archivo de base de datos y las tablas necesarias automáticamente

#### Scenario: Base de datos ya existente
- **WHEN** la aplicación inicia y ya existe una base de datos con el esquema correcto
- **THEN** el storage SHALL conectarse y agregar nuevos registros sin modificar los existentes

### Requirement: Consultar métricas almacenadas
El sistema SHALL permitir recuperar métricas almacenadas filtradas por dispositivo y rango de tiempo.

#### Scenario: Consulta por dispositivo
- **WHEN** se solicitan métricas de un dispositivo específico
- **THEN** el storage SHALL retornar todos los registros correspondientes a ese dispositivo ordenados por marca de tiempo descendente

#### Scenario: Dispositivo sin métricas
- **WHEN** se solicitan métricas de un dispositivo que no tiene registros almacenados
- **THEN** el storage SHALL retornar una lista vacía sin producir error

### Requirement: Aislar el storage de otras capas
La capa storage SHALL NOT tener conocimiento del collector, el processor ni la presentación. SHALL exponer únicamente métodos de inserción y consulta sobre estructuras de datos simples.

#### Scenario: Interfaz de storage sin dependencias de otras capas
- **WHEN** se instancia el módulo de storage
- **THEN** SHALL NOT importar ni referenciar módulos de collector, processor ni presentation

