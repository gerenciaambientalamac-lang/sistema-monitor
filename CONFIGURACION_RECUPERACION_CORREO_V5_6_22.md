# Recuperación de acceso por correo electrónico — V5.6.25

La recuperación usa un enlace de un solo uso, con expiración de 30 minutos. Al restablecer la contraseña se revocan las sesiones activas.

## Variables SMTP del servidor
`LLE_SMTP_HOST`, `LLE_SMTP_PORT`, `LLE_SMTP_USER`, `LLE_SMTP_PASSWORD`, `LLE_SMTP_FROM`, `LLE_SMTP_TLS` y `LLE_PUBLIC_BASE_URL`.

Durante la prueba LAN, `LLE_PUBLIC_BASE_URL` puede apuntar a `http://192.168.1.175:8001`. Para instalación institucional se recomienda HTTPS y el dominio interno correspondiente.

Cada usuario debe tener registrado en `usuarios.email` el correo electrónico que realmente utiliza; puede ser personal o institucional.
