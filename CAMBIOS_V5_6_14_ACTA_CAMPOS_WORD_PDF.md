# V5.6.14 — Acta: campos de ubicación y documentos estáticos

## Cambios
- Se habilitan en el Acta los campos de cantón/caserío/colonia/urbanización, lugar específico, dirección/domicilio y referencia del sitio para precisar la información verificada en campo.
- La ubicación verificada en campo se guarda en campos separados (`acta_*_campo`) para no sobrescribir los datos originales de recepción.
- El Informe Técnico prioriza la dirección verificada en campo cuando está disponible.
- La exportación a Word deja de transportar controles HTML editables: inputs, selects, textarea y casillas se convierten en valores estáticos listos para imprimir/archivar.
- La impresión/PDF usa la misma representación estática.
- La generación de Word/PDF no cambia el estado, no valida y no finaliza la actuación.
