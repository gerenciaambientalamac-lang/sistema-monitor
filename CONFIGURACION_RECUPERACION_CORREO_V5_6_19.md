# Recuperación de acceso por correo institucional — V5.6.21

La recuperación usa un enlace de un solo uso, con expiración de 30 minutos. Al restablecer la contraseña se revocan las sesiones activas.

## Variables SMTP del servidor
`LLE_SMTP_HOST`, `LLE_SMTP_PORT`, `LLE_SMTP_USER`, `LLE_SMTP_PASSWORD`, `LLE_SMTP_FROM`, `LLE_SMTP_TLS` y `LLE_PUBLIC_BASE_URL`.

Durante la prueba LAN, `LLE_PUBLIC_BASE_URL` puede apuntar a `http://192.168.1.175:8001`. Para instalación institucional se recomienda HTTPS y el dominio interno correspondiente.

Cada usuario debe tener su correo electrónico de recuperación registrado en `usuarios.email`; puede ser personal o institucional..
