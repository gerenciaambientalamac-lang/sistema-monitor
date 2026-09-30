# V5.6.21 — Alertas de asignación en tiempo real

- Cada nueva asignación dirigida a un Técnico genera una ventana modal visible inmediatamente en su sesión abierta.
- La alerta no depende de que el Técnico abra la campana.
- La página consulta alertas cada 2 segundos.
- La ventana muestra expediente, mensaje, fecha/hora y botón para abrir la actuación.
- Abrir la alerta la marca como leída y carga el expediente correspondiente.
- Si se cierra el modal, la alerta permanece en la bandeja como no leída.
- Se solicita/usa Notification API cuando el navegador tiene permiso.
- Se usa sonido cuando el navegador permite reproducción de audio tras interacción del usuario.
- En PC, tableta o celular funciona mientras la página/PWA esté abierta y conectada al servidor.
- Notificación con aplicación completamente cerrada/suspendida requerirá Push/Web Push + HTTPS.
