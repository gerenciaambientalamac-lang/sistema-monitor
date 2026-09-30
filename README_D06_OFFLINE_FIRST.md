# D06 — Reestructuración Offline-First V5.6.26

## Objetivo
Permitir que el Técnico Ambiental continúe una inspección cuando el teléfono no tenga Wi-Fi ni datos móviles, conservando expediente, fotografías y GPS localmente y sincronizando al recuperar conectividad.

## Arquitectura
- Core D01-D05: conservado.
- IndexedDB: persistencia local de expedientes, cola, fotografías, GPS y caché.
- Service Worker: shell móvil offline.
- SyncManager: operaciones pendientes con reintento.
- Idempotencia local: guardados de expediente se agrupan por expediente.
- Fotografías: Blob local + operación pendiente.
- GPS: registro local + operación pendiente.
- Recuperación: el expediente local puede reabrirse sin servidor.

## Importante: HTTPS
Para que una PWA pueda volver a abrirse sin conexión después de cerrar el navegador en un teléfono, el origen debe ser seguro. `http://IP-LAN:8001` no es suficiente para Service Worker en un teléfono.

Para la prueba D06 se agregó:
- `GENERAR_CERTIFICADO_LAN_D06.py`
- `INICIAR_SISTEMA_LAN_D06_HTTPS.bat`

El certificado de desarrollo debe ser aceptado/instalado en el teléfono. Para producción institucional se recomienda un certificado emitido por una CA institucional o una PKI interna confiable.

## Prueba de campo simulada
1. En PC ejecutar `INICIAR_SISTEMA_LAN_D06_HTTPS.bat`.
2. Abrir la URL HTTPS en el teléfono conectado a la LAN.
3. Iniciar sesión y abrir/cargar una actuación.
4. Verificar que la aplicación quede instalada/cargada y que el Service Worker esté activo.
5. Activar modo avión.
6. Continuar la inspección.
7. Registrar datos, fotografías y GPS.
8. Cerrar y volver a abrir la aplicación mientras continúa el modo avión.
9. Comprobar que los datos permanecen.
10. Desactivar modo avión.
11. Comprobar la sincronización automática.
12. Verificar en el servidor que exista un único expediente y que las evidencias se hayan sincronizado.

## Estado
Esta versión implementa la primera reestructuración D06. La prueba física en un teléfono real y la auditoría de sincronización contra el servidor deben ejecutarse antes de declarar D06 como cerrado.
