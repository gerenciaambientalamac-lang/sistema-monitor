# V5.6.12 — Registro de actuación desde Acta

Se consolida la opción para el Técnico Ambiental Distrital de registrar desde la pantalla de Acta una denuncia/solicitud que aún no figure en el registro institucional.

## Regla operativa
- Si la actuación ya fue registrada: el Técnico selecciona un expediente al que tenga acceso y vincula el Acta.
- Si no está registrada: el Técnico captura únicamente los datos mínimos de recepción.
- El servidor genera el código `AMB-LLE-AAAA-NNNN`, registra recepción e historial y genera alerta al Gerente (y al Administrador).
- La nueva actuación queda `RECIBIDO_PENDIENTE_ASIGNACION`.
- El Técnico que la registró puede continuar guardando el borrador del Acta, pero **no puede finalizar el Informe** ni enviarlo a revisión hasta que el Gerente realice la asignación formal.
- Esto no concede al Técnico facultades de asignación ni de validación.
