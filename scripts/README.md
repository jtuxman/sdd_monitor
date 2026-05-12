# Scripts CGI — SDD Monitor

## interfaces.py

Script CGI que realiza un SNMP WALK sobre la ifXTable de un switch Cisco y retorna estadísticas de tráfico por interfaz en formato JSON.

### Requisitos

- Python 3.10+
- `pysnmp` (ya instalado como dependencia del proyecto)
- `pyyaml` (ya instalado como dependencia del proyecto)
- `fcgiwrap` instalado en el servidor nginx

---

## Instalación en nginx

### 1. Instalar fcgiwrap

```bash
sudo apt install fcgiwrap
sudo systemctl enable fcgiwrap
sudo systemctl start fcgiwrap
```

### 2. Dar permisos de ejecución al script

```bash
chmod +x /ruta/al/proyecto/scripts/interfaces.py
```

### 3. Agregar bloque CGI en la configuración de nginx

Edita tu archivo de configuración nginx (p.ej. `/etc/nginx/sites-available/sdd-monitor`):

```nginx
server {
    listen 80;
    # ... tu configuración existente ...

    # Directorio raíz donde está report.html
    root /ruta/al/proyecto/data;

    # CGI para scripts Python
    location /cgi-bin/ {
        alias /ruta/al/proyecto/scripts/;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $request_filename;
        fastcgi_param DOCUMENT_ROOT /ruta/al/proyecto/scripts;
    }
}
```

> Reemplaza `/ruta/al/proyecto` con la ruta real del proyecto en tu servidor.

### 4. Recargar nginx

```bash
sudo nginx -t        # verificar configuración
sudo nginx -s reload # aplicar cambios
```

### 5. Verificar

```bash
curl "http://localhost/cgi-bin/interfaces.py?device=switch-core"
```

Debe retornar un JSON con la lista de interfaces.

---

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `SDD_CONFIG` | `../config/devices.yaml` (relativo al script) | Ruta al archivo de configuración de dispositivos |

Ejemplo para configurar en nginx:

```nginx
location /cgi-bin/ {
    # ...
    fastcgi_param SDD_CONFIG /ruta/al/proyecto/config/devices.yaml;
}
```

---

## Respuestas

| Status | Descripción |
|---|---|
| `200 OK` | `{"interfaces": [...]}` — array ordenado por tráfico total desc |
| `400 Bad Request` | Parámetro `device` ausente o el dispositivo no es un switch |
| `404 Not Found` | El nombre de dispositivo no existe en `devices.yaml` |
| `502 Bad Gateway` | Error de red o timeout al consultar el switch via SNMP |

### Estructura de cada interfaz en la respuesta

```json
{
  "name": "Gi0/1",
  "alias": "Uplink SW-Core",
  "in_gb": 12.34,
  "out_gb": 8.56,
  "total_gb": 20.90,
  "status": "up"
}
```
