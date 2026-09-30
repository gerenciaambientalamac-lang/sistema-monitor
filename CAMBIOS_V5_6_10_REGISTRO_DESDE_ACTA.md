# V5.6.10 — Registro de denuncia/solicitud desde Acta

Se agrega al Sistema 1 una opción para que el Técnico Ambiental Distrital pueda registrar desde la pantalla del Acta una denuncia o solicitud que aún no exista en la recepción institucional.

## Reglas
- El Técnico registra únicamente datos mínimos de recepción.
- El servidor genera el código único del expediente.
- El nuevo caso queda en `RECIBIDO_PENDIENTE_ASIGNACION`.
- El Técnico no puede asignarse el caso ni convertir este registro en una asignación propia.
- La actuación aparece en la cola del Gerente para revisión y asignación.
- Se registra en `expedientes`, `recepciones`, `historial` y `versiones`.
- No se altera la actuación que el Técnico tenga abierta en el Acta.
