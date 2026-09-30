# V5.5.1 — Corrección de nomenclatura y separación conceptual

## Cambio principal
Se eliminó del formulario la expresión **“Materia ambiental”** porque podía confundirse con el origen de la actuación o con una categoría jurídica.

## Nueva estructura
1. **Origen de la actuación** — por qué se inicia la diligencia.
2. **Componente ambiental principal** — qué asunto ambiental se verifica.
3. **Componentes ambientales relacionados** — otros componentes realmente involucrados.
4. **Formulario técnico especializado** — se determina posteriormente según la actuación y el componente verificado.

## Regla institucional
“Denuncia ambiental” es un **origen**, no un componente ambiental.

## Catálogo de componentes
OI, RS, VH, RH, AU, TP, CO, CR, CS, MT, EP, ZR y GR.

## Compatibilidad
El servidor mantiene compatibilidad controlada con códigos históricos DA/MT para no invalidar registros anteriores. La interfaz de nuevos expedientes ya no ofrece DA como componente.

## Pruebas realizadas
- Auditoría especial de arranque: **41 PASS / 0 FAIL**.
- Autenticación de las tres cuentas de prueba: PASS.
- Creación de expediente de prueba para los 13 componentes del nuevo catálogo: **13/13 PASS**.
- SQLite íntegra y sin expediente de prueba conservado en el paquete de distribución.


## Corrección de navegación del Acta
- Se agregó botón explícito «← Regresar a Expediente para revisar» al final del Acta, antes de guardar y continuar al Informe.
- El retorno es de navegación y no finaliza ni cambia el estado del expediente.
- Los campos del Acta permanecen en pantalla al regresar para facilitar la corrección de datos omitidos antes del guardado final.
