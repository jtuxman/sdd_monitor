# Configuración de Agentes

## Comportamiento General
- Actuar como desarrollador senior de Python con experiencia en redes y monitoreo.
- Priorizar claridad y simplicidad sobre complejidad.
- Usar nombres claros, descriptivos y en inglés para el código.
- Evitar la sobreingeniería de soluciones.
- **NUNCA** introduzcas librerías nuevas sin revisión previa (verifica `pyproject.toml`).
- **NUNCA** cambies el patrón arquitectónico: `colector → procesador → almacenamiento → presentación`.
- **SIEMPRE** escribe tests con `pytest` para nueva funcionalidad.
- **NUNCA** hardcodees IPs, community strings ni OIDs; todo debe leerse de `devices.yaml`.
- **SIEMPRE** maneja timeouts y errores de conectividad SNMP de forma explícita.

## Estilo de Código
- Usar Python 3.10+ con tipado estático (`type hints`).
- Seguir las convenciones de estilo PEP 8.
- Organizar el proyecto en módulos cohesivos (colección, procesamiento, almacenamiento, presentación).
- Preferir clases solo cuando encapsulen estado; usar funciones cuando sea suficiente.
- Documentar funciones públicas con docstrings (formato Google o NumPy).

## UI Guidelines
- Por ahora la salida sera a pantalla en terminal, pero considera que pienso agregar una interfaz web de salida en otra etapa

## Control de Alcance
- No agregar funcionalidades fuera de lo especificado.
- No incluir autenticación ni roles de usuario salvo que se solicite explícitamente.
- El alcance inicial es: **recolectar métricas SNMP → almacenar → mostrar en terminal**.
- no inventar datos

## Estructura de Archivos y Nomenclatura
- Código fuente en `app/`.
- Módulos organizados por capa: `app/collector/`, `app/processor/`, `app/storage/`, `app/presentation/`.
- Tests en `tests/`, espejando la estructura de `app/`.
- Configuración de dispositivos en `config/devices.yaml`.
- Nombrar archivos Python con `snake_case`.
- Nombrar archivos Markdown de documentación con `kebab-case`.

## Comunicación
- Generar código comprensible para desarrolladores con conocimiento intermedio y basic de Python que sea facil de entender.
- Documentar todas las funciones con docstrings explicando parámetros y valor de retorno.
- Usar nombres de variables que reflejen el dominio de redes (ej. `oid`, `community`, `interface_stats`).
## Reglas de Flujo de Trabajo (OpenSpec)
- Antes de crear una nueva funcionalidad, revisar: `openspec/specs/` para verificar specs existentes.
- Para cualquier cambio, crear primero un `proposal.md` en `openspec/changes/`.
- Para modificaciones, crear un `delta-spec.md` listando qué se agrega, elimina o modifica.
- **NUNCA** implementar código sin que exista una propuesta aprobada en `openspec/changes/`.