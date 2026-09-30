# V5.6.9 — Consistencia de componentes ambientales

## Correcciones
- El componente ambiental principal se registra obligatoriamente en la Recepción del Motor de Seguimiento.
- La Recepción conserva componente principal, componentes adicionales, origen, distrito y demás datos fuente.
- El componente principal es inmutable durante Acta/Informe/Evidencias; el servidor rechaza intentos de cambiarlo.
- Acta e Informe reutilizan el mismo componente; no se permite que una actuación sea TP en recepción, RS en Acta u OI en Informe.
- El código del Informe y del Acta se deriva siempre del componente registrado en recepción.
- Se agregó MT al catálogo de nombres de informes especializados.
- Las opciones de corrección del Gerente ya no incluyen campos de origen, componente implícito, solicitante, distrito o técnico responsable como campos editables por el Técnico.
- “Sin vincular” en el punto GPS de fotografía pasó a “Sin punto GPS específico”.

## Pruebas de auditoría
- Sintaxis Python: PASS.
- Sintaxis JavaScript embebido: PASS.
- Recepción TP → asignación → técnico: PASS.
- Intento de cambiar TP a RS desde el Técnico: RECHAZADO por servidor.
- Códigos derivados: ACTA-TP-... / INF-TP-....
- Todos los componentes del catálogo: ver auditoría integral adjunta.
