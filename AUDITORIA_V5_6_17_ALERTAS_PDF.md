# AUDITORÍA V5.6.17 — ALERTAS DEL TÉCNICO + IMPRESIÓN/PDF DEL ACTA

## Resultado

**20/20 PASS** en revisión estática y pruebas de servidor realizadas en entorno local.

### Alertas
1. Bandeja de alertas del Sistema 1 presente.
2. Contador de no leídas implementado.
3. Carga desde `/api/notificaciones` implementada.
4. Marcar una alerta como leída implementado.
5. Marcar todas como leídas implementado.
6. Acción contextual para abrir actuación/informe implementada.
7. El código del expediente de la alerta se carga antes de abrir el destino.
8. Actualización automática de alertas cada 5 segundos.
9. Servidor genera alerta al técnico al asignar actuación.
10. Servidor genera alerta al técnico al devolver informe.
11. Servidor genera alerta al técnico al validar informe.
12. Servidor genera alerta al técnico al remitir expediente.
13. Servidor genera alerta al técnico al finalizar expediente.

### Impresión / PDF
14. La impresión del Acta ya no depende de `iframe` ni de ventana emergente.
15. Se crea un área `#printRoot` dentro de la misma ventana.
16. Se usa `window.print()` en respuesta a la acción del usuario.
17. CSS de impresión oculta la interfaz y conserva solamente el Acta.
18. La salida del Acta usa datos ya capturados y convierte controles a texto limpio.
19. Las casillas se representan como `☑` / `☐` en la salida.
20. La exportación Word continúa sin controles de formulario y con campos separados.

## Comprobaciones técnicas
- JavaScript del Sistema 1: PASS (`node --check`).
- Python del servidor: PASS (`py_compile`).
- `/api/health`: PASS, versión V5.6.17.
- Login técnico: PASS.
- `/api/notificaciones`: PASS.

## Alcance de la prueba
La impresión física y el diálogo nativo de “Guardar como PDF” dependen del navegador/Windows del equipo del usuario y deben validarse manualmente. La implementación evita el popup/iframe que provocó el bloqueo observado anteriormente.
