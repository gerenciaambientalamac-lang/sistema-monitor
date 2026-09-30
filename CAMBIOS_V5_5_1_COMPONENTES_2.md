# V5.5.1 — Corrección de componentes principal y relacionados

## Regla implementada
El **Componente ambiental principal** y los **Componentes ambientales relacionados** utilizan el mismo catálogo porque ambos identifican componentes ambientales. Sin embargo, el componente seleccionado como principal **no puede seleccionarse como relacionado**.

Al cambiar el componente principal:
- se deshabilita automáticamente esa misma opción en la lista de relacionados;
- si ya estaba seleccionada como relacionada, se desmarca;
- el servidor/estado no conserva duplicidad entre principal y relacionados.

La misma regla se aplica en la captura del Expediente y en los datos previos del Acta.

## Ejemplo
Principal: `RS — Residuos sólidos`

Relacionados disponibles: `VH`, `RH`, `CO`, `EP`, etc.

`RS` queda deshabilitado en relacionados y no puede duplicarse.
