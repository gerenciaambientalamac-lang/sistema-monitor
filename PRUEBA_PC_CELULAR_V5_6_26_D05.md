# PRUEBA PC Y CELULAR — V5.6.26 D05

Fecha de prueba: 2026-09-29

## Alcance

Prueba de interfaz de los dos módulos institucionales en resoluciones de PC, tablet y celular, además de verificación de acceso HTTP/API y modo LAN.

## Resultados

### Sistema 1 — Inspecciones
- PC 1366x768: PASS
- Tablet 768x844: PASS
- Celular 360x844: PASS
- Celular 390x844: PASS
- Celular 412x844: PASS
- Sin desplazamiento horizontal en las resoluciones probadas.

### Sistema 2 — Monitor de Seguimiento
- PC 1366x768: PASS
- Tablet 768x844: PASS
- Celular 360x844: PASS
- Celular 390x844: PASS
- Celular 412x844: PASS
- Sin desplazamiento horizontal en las resoluciones probadas.

## Corrección realizada durante la prueba

Se detectó en Sistema 2 un desbordamiento horizontal en celular provocado por las rejillas de recepción/personal/remisión y por la barra de navegación horizontal.

La corrección fue exclusivamente de interfaz responsive:
- `min-width: 0` en contenedores relevantes.
- navegación horizontal contenida dentro de su barra.
- rejillas de formularios pasan a una columna en pantallas pequeñas.
- resumen de proceso pasa a 2 columnas en celular.
- tablas permiten desplazamiento horizontal interno cuando corresponde.
- formularios y tarjetas quedan limitados al ancho disponible.

No se modificó el Core, servidor, modelo de datos, máquina de estados ni reglas D01-D05.

## API / servidor

- `/api/health`: PASS — V5.6.26.
- Login Gerente: PASS.
- `/api/me` Gerente: PASS.
- Login Técnico: PASS.
- `/api/me` Técnico: PASS.
- Servidor LAN con `LLE_BIND=0.0.0.0`: PASS.
- Acceso LAN de prueba a `/api/health`: PASS.

## Base de datos

Después de las pruebas:
- Expedientes: 0
- Personal: 1
- Usuarios: 3
- Notificaciones: 0
- Asignaciones: 0

No se incorporaron registros de prueba al paquete final.

## Dictamen técnico

La interfaz queda validada para las resoluciones probadas de PC, tablet y celular. La prueba confirma además que el servidor puede exponerse en LAN mediante la configuración prevista por los scripts de inicio.

La prueba con un teléfono físico conectado a la red institucional debe realizarse como prueba de campo final, porque depende de la red Wi-Fi/LAN, firewall de Windows, IP real del servidor y navegador del dispositivo.
