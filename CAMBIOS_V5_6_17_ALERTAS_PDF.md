# V5.6.17 — Alertas del Técnico + impresión/PDF del Acta

- Se implementó la bandeja de alertas del Sistema 1 para usuarios autenticados, con contador, listado, marcar leída, marcar todas y acción contextual.
- Se conserva la generación de alertas del servidor para asignación, devolución, validación, remisión y finalización.
- La impresión del Acta dejó de depender de una ventana emergente/iframe: ahora se prepara un área de impresión dentro de la misma ventana y se ejecuta `window.print()` por una acción directa del usuario.
- “Guardar como PDF” se realiza desde el diálogo de impresión del navegador; no se intenta generar un PDF binario desde el navegador.
- La exportación Word continúa usando el Acta ya rellenada y convertida a texto, sin controles de formulario.
- Versión de `/api/health` y título actualizados a V5.6.17.
