# V5.6.15 — Corrección de separación en exportación Word/PDF

Se corrigió la exportación del Acta para que los datos capturados no queden concatenados entre controles al abrir el archivo en Word.

## Cambio
- Cada campo se transforma en un bloque independiente con etiqueta y valor.
- Se preservan saltos de línea de áreas de texto.
- Los campos se muestran con separación visual y borde propio en la salida documental.
- Las casillas de verificación se exportan como ☑ / ☐.
- La versión impresa/PDF utiliza la misma representación estática.
- La exportación no modifica el estado de la actuación ni implica validación.

## Verificación estática
- JavaScript embebido: PASS
- Función de exportación presente: PASS
- Conversión label → bloque etiqueta/valor: PASS
- Separación de campos con CSS: PASS
- Preservación de textarea: PASS
- Checkbox/radio: PASS
