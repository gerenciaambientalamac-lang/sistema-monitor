# V5.3 — Seguridad y control de acceso

Esta versión corrige las vulnerabilidades de seguridad detectadas en V5.2.

## Controles incorporados
- Autenticación por usuario y contraseña con PBKDF2-HMAC-SHA256.
- Sesiones servidoras con token aleatorio almacenado como hash en SQLite.
- Cookie `HttpOnly` y `SameSite=Strict`.
- Roles `TECNICO`, `GERENTE` y `ADMIN`.
- El servidor determina el usuario y rol; ya no confía en `_actor` ni en `user` enviados por el navegador.
- El servidor controla los cambios de estado; un técnico no puede autoaprobar un expediente.
- El técnico solo puede editar sus propios expedientes como responsable.
- Gerente/Administrador controlan revisión, validación y remisión.
- Gestión de personal restringida a Gerente/Administrador.
- Bloqueo de recursos sensibles: `server.py`, SQLite, JSON, bytecode y archivos ocultos.
- CORS abierto eliminado.
- Cabeceras HTTP de endurecimiento: CSP, X-Content-Type-Options, X-Frame-Options y Referrer-Policy.
- Límite básico contra fuerza bruta: 10 intentos de inicio de sesión por IP en 5 minutos.
- Tamaño máximo de solicitudes JSON: 2 MB.
- El servidor escucha en `127.0.0.1` por defecto. Para una LAN controlada debe configurarse explícitamente `LLE_BIND`; se recomienda HTTPS mediante un proxy institucional antes de exponer credenciales en red.
- Contraseñas iniciales marcadas para cambio obligatorio y función de cambio de contraseña.

## Usuarios iniciales de primera ejecución
- `admin` / `LLE-Admin-2026!`
- `gerente` / `LLE-Gerente-2026!`
- `tecnico` / `LLE-Tecnico-2026!`

**Estas credenciales son únicamente de instalación/prueba. El sistema obliga a cambiarlas al primer acceso.**

## Prueba de seguridad V5.3
Resultado esperado y verificado:
- API sin sesión: `401`.
- Credenciales incorrectas: `401`.
- Más de 10 intentos en 5 minutos: `429`.
- API de expedientes con rol correcto después de cambio de contraseña: `200`.
- Técnico intentando validar: `403`.
- Gerente intentando crear/editar expediente técnico: `403`.
- Suplantación mediante `_actor`, `user` o `status`: no otorga privilegios; el estado es controlado por servidor.
- `server.py`, SQLite y bytecode: `404`.
- CORS abierto: ausente.
- Cookie de sesión: `HttpOnly; SameSite=Strict`.
- Cabeceras de seguridad: presentes.
- Bind predeterminado: `127.0.0.1:8001`.

## Pendientes antes de producción institucional
1. HTTPS/TLS mediante infraestructura institucional o proxy inverso.
2. Integración de usuarios reales y administración de cuentas, en lugar de las cuentas iniciales.
3. MFA si la política institucional lo requiere.
4. Almacenamiento seguro de fotografías/documentos y política de copias de respaldo.
5. Prueba de recuperación ante desastre y restauración de SQLite.
