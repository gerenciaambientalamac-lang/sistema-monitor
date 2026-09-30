# D05 — V5.6.26 — Máquina de estados e integridad de transiciones

## Alcance
D05 continúa desde D04 sin rehacer D01–D04 ni modificar el Core.

Se auditó el ciclo institucional:

`RECIBIDO_PENDIENTE_ASIGNACION → ASIGNADO_A_INSPECCION → BORRADOR → INFORME_FINALIZADO_PENDIENTE_VB → DEVUELTO → INFORME_FINALIZADO_PENDIENTE_VB → VB_APROBADO → REMITIDO → FINALIZADO`

También se probaron los controles de autoridad y los intentos de manipular el estado desde el navegador/API.

## Hallazgo corregido
Durante la prueba de devolución/corrección se detectó que un POST técnico que no incluía `tecnicos_participantes` podía ser rechazado como si hubiera modificado participantes, aunque el valor histórico almacenado fuera simplemente un campo derivado por el servidor.

La corrección se limita a la comparación del alcance de una devolución:

- si `tecnicos_participantes` no viene en el POST, su ausencia no se considera una modificación;
- si el cliente sí lo envía, se compara normalmente;
- por tanto, no se permite agregar/quitar participantes fuera del alcance autorizado.

No se modificó el modelo de participantes de D03 ni ninguna transición del Core.

## Controles D05
- El Técnico no puede revisar, validar, devolver, remitir ni cerrar.
- El estado enviado por el cliente no tiene autoridad.
- Un expediente en revisión no puede ser editado técnicamente.
- La devolución solo permite los campos autorizados.
- La corrección autorizada puede guardarse y posteriormente finalizarse nuevamente.
- La validación solo ocurre desde `INFORME_FINALIZADO_PENDIENTE_VB`.
- La remisión solo ocurre desde `VB_APROBADO`.
- El cierre solo ocurre desde `VB_APROBADO` o `REMITIDO`.
- Un expediente `FINALIZADO` no puede volver a revisión, remisión, cierre ni edición técnica.
- Las versiones conservan numeración estrictamente creciente.
- El estado de cada versión coincide con el `status` de su payload.
- El estado de la fila `expedientes` coincide con el estado del payload final.

## Auditoría
**45/45 PASS**.

La prueba se ejecutó sobre una copia limpia de D04. El paquete de entrega se reconstruye nuevamente desde D04 limpio para no incluir los datos generados durante las pruebas.
