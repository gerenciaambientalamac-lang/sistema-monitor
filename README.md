# Sistema La Libertad Este — V5.6.26 D06-R1

Sistema de Gestión Ambiental y Gestión de Riesgo para la Municipalidad de La Libertad Este.

## D06-R1 — Offline First

Esta versión reconstruye el flujo de trabajo técnico para permitir trabajo de campo con conectividad intermitente o nula, manteniendo una cola local de operaciones y sincronización posterior con el servidor.

### Componentes

- `server.py` — servidor HTTP/HTTPS, API y SQLite local.
- `01_SISTEMA_INSPECCIONES/` — Sistema 1, Técnico Ambiental Distrital.
- `02_MOTOR_SEGUIMIENTO/` — Sistema 2, Motor de Seguimiento.
- `01_SISTEMA_INSPECCIONES/offline-core.js` — persistencia local, cola e identidad de operaciones.
- `01_SISTEMA_INSPECCIONES/sw.js` — Service Worker/PWA.
- `01_SISTEMA_INSPECCIONES/manifest.json` — manifiesto PWA.
- `GENERAR_CERTIFICADO_LAN_D06.py` — certificado HTTPS local para LAN.
- `INICIAR_D06_R1_LAN_HTTPS.bat` — arranque recomendado para pruebas PC + celular.

## Requisitos

- Windows 10/11 para los lanzadores `.bat`.
- Python 3.10+; se recomienda Python 3.13.
- Dependencias de `requirements.txt`.
- Para la primera generación del certificado HTTPS se requiere instalar `cryptography`.

Instalación:

```bash
python -m pip install -r requirements.txt
```

## Arranque LAN HTTPS

En la PC que funcionará como servidor:

```text
INICIAR_D06_R1_LAN_HTTPS.bat
```

El servidor se enlaza a `0.0.0.0:8001` y muestra la IP LAN detectada, por ejemplo:

```text
https://192.168.1.72:8001/
```

Mantenga abierta la consola del servidor.

**No abra `index.html` mediante `file:///`.** La aplicación debe cargarse desde el servidor HTTP/HTTPS.

En el celular conectado a la misma red Wi-Fi, abra la URL HTTPS mostrada por el servidor. El certificado es local/autofirmado para la LAN; el navegador puede mostrar una advertencia que debe aceptarse para la prueba.

## Prueba Offline First

1. Conecte inicialmente el equipo móvil al servidor.
2. Inicie sesión y cargue la información necesaria para el trabajo de campo.
3. Verifique que la aplicación esté operativa.
4. Active modo avión o desactive Wi-Fi y datos móviles.
5. Realice la inspección sin conectividad.
6. Capture información, fotografías y ubicación cuando estén disponibles.
7. Cierre y vuelva a abrir la aplicación para comprobar recuperación local.
8. Restablezca la conectividad.
9. Compruebe la sincronización de la cola con el servidor.

La prueba física PC + celular sigue siendo necesaria; una auditoría estructural no sustituye esa validación.

## Desarrollo

Servidor local sin HTTPS para pruebas rápidas:

```bash
LLE_BIND=127.0.0.1 LLE_PORT=8001 LLE_HTTPS=0 python server.py
```

En Windows PowerShell:

```powershell
$env:LLE_BIND="127.0.0.1"
$env:LLE_PORT="8001"
$env:LLE_HTTPS="0"
python server.py
```

## Auditorías

Los scripts `AUDITORIA_*.py` y los reportes incluidos documentan las auditorías D01–D06-R1 realizadas sobre esta línea de desarrollo.

## Datos y seguridad

Este repositorio está preparado para código fuente. No deben subirse:

- bases SQLite con datos reales;
- fotografías de inspecciones;
- certificados o claves privadas (`tls/*.pem`);
- sesiones, tokens o credenciales institucionales;
- datos personales reales.

La base SQLite se crea localmente al iniciar el servidor cuando no existe. Los usuarios de prueba definidos por el código son únicamente para desarrollo y deben sustituirse por un mecanismo de configuración segura antes de producción.

## Estado

**D06-R1 — rama de reconstrucción Offline First.**

La publicación en GitHub no significa que el sistema haya sido aprobado para producción. Antes de producción deben completarse pruebas institucionales, seguridad, gestión de secretos, respaldos, despliegue y validación física en PC/celular.

## D06-R1 — Reconstrucción de entrada del Técnico

La entrada del Sistema 01 fue reconstruida para que el flujo visible sea realmente operativo. Los cuatro pasos son controles funcionales; el paso 1 abre la bandeja de actuaciones y los pasos 2–4 requieren una actuación seleccionada. La recepción continúa perteneciendo al flujo institucional de Seguimiento/Gerencia. Consulte `CAMBIOS_D06_R1_UI_ENTRADA_TECNICO.md`.
