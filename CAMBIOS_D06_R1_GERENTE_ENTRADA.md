# D06-R1 — Corrección de entrada al Sistema 02 (Gerente)

## Hallazgo
La ruta `/02_MOTOR_SEGUIMIENTO/` estaba protegida por la comprobación de autenticación antes de entregar el HTML del shell. Por ello, un usuario no autenticado que seleccionaba **02 · Seguimiento** recibía un JSON `Autenticación requerida` en lugar de la pantalla de inicio de sesión.

## Reconstrucción
Se ajustó `server.py` para que el HTML público del Sistema 02 y su escudo institucional puedan entregarse sin sesión, igual que el shell de acceso del Sistema 01. Las operaciones y APIs continúan protegidas por autenticación.

## Resultado esperado
- `https://IP:8001/02_MOTOR_SEGUIMIENTO/` entrega la pantalla de acceso institucional.
- Sin sesión: aparece el formulario de inicio de sesión, no un JSON de autenticación.
- Después del login como GERENTE/ADMIN: se habilita el dashboard y sus operaciones.
- Las APIs (`/api/*`) siguen requiriendo autenticación.
