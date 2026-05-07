# Proyecto: SDD Monitor

## Descripción
Monitor de red basado en SNMP desarrollado en Python. Recolecta métricas de dispositivos de red (routers, switches, servidores) de forma periódica, las almacena localmente y las presenta en terminal.

## Stack Tecnológico
- **Lenguaje**: Python 3.10+
- **Protocolo**: SNMP v2c / v3
- **Librería SNMP**: `pysnmp` o `easysnmp`
- **Almacenamiento**: SQLite via `sqlite3`
- **Presentación CLI**: `rich`
- **Scheduler**: `schedule` o `APScheduler`
- **Configuración**: `devices.yaml` + `python-dotenv`
- **Tests**: `pytest`
- **Gestión de dependencias**: `pyproject.toml`

## Arquitectura
El sistema sigue un flujo de capas estrictamente separadas:

```
colector → procesador → almacenamiento → presentación
```

- **collector**: consultas SNMP a los dispositivos
- **processor**: transformación y normalización de los datos recibidos
- **storage**: persistencia en SQLite
- **presentation**: salida formateada en terminal (Rich)

## Configuración de Dispositivos
Los dispositivos monitoreados se definen en `config/devices.yaml`. Ningún dato de red (IP, community string, OID) debe estar hardcodeado en el código.

Estructura esperada del archivo:
```yaml
devices:
  - name: router-principal
    host: 192.168.1.1
    snmp_version: 2c
    community: public
    oids:
      - 1.3.6.1.2.1.1.1.0  # sysDescr
      - 1.3.6.1.2.1.2.2.1.10  # ifInOctets
```

## Alcance Actual
- Recolectar métricas SNMP de dispositivos reales
- Almacenar métricas en SQLite
- Mostrar resultados en terminal

## Alcance Futuro (no implementar aún)
- Interfaz web para visualización de métricas
- Autenticación de usuarios
- Alertas y notificaciones

## Dominio
- **OID** (Object Identifier): identificador único de una métrica SNMP
- **Community string**: cadena de autenticación básica en SNMP v1/v2c
- **MIB** (Management Information Base): base de datos que define los OIDs disponibles en un dispositivo
- **Poll**: ciclo de consulta periódica a un dispositivo
