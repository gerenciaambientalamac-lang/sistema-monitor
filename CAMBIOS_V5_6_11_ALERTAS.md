# V5.6.11 — Alertas internas y salida documental

## Objetivo
Incorporar avisos internos por usuario y expediente para facilitar el trabajo coordinado entre Gerencia y Técnicos Ambientales Distritales en una instalación con una PC servidor y varias estaciones cliente.

## Alertas implementadas
- Nueva actuación registrada por un Técnico: alerta al Gerente.
- Actuación asignada por el Gerente: alerta al Técnico responsable.
- Informe técnico finalizado y enviado a revisión: alerta al Gerente.
- Informe devuelto para corrección: alerta al Técnico responsable.
- Informe validado: alerta al Técnico responsable.
- Expediente remitido: alerta al Técnico responsable.
- Expediente finalizado: alerta al Técnico responsable.
- Las alertas se almacenan en SQLite con usuario destinatario, expediente, tipo de evento, título, mensaje, fecha/hora, estado leído/no leído y acción.
- El usuario puede marcar una alerta individual o todas como leídas.
- La bandeja se actualiza periódicamente sin recargar manualmente la página.

## Salida documental
En el módulo del Técnico se incorporan:
- **Imprimir / PDF:** abre el diálogo de impresión del navegador para imprimir o seleccionar una impresora PDF.
- **Word:** genera un archivo `.doc` compatible con Microsoft Word a partir del contenido visible del informe.

La generación documental no cambia el estado del expediente ni equivale a revisión, visto bueno o validación institucional.

## Seguridad
- Las alertas son privadas por usuario.
- No se confía en el usuario enviado por el navegador para determinar el destinatario: el servidor deriva las relaciones desde la sesión, el personal y las asignaciones.
- La lectura de alertas se valida contra el usuario autenticado.
