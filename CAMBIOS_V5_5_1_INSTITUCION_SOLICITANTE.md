# V5.5.1 — Institución solicitante flexible

- El campo **Institución solicitante** es de texto libre.
- Se incorporó una lista de sugerencias sin obligar a seleccionar una opción.
- Sugerencias: Fiscalía, Juzgado Ambiental, ASA, MARN, Concejo Municipal y Otras dependencias municipales.
- El usuario puede escribir cualquier otra institución o dependencia y, cuando corresponda, una referencia no contemplada por el catálogo.
- La misma lógica se aplica al campo equivalente del Acta.
- No se modifica el catálogo de origen ni de componentes ambientales.

### Corrección de navegación y validación previa al avance
- `Guardar y continuar` en Expediente y Acta ahora espera (`await`) el guardado antes de cambiar de pestaña.
- Si falta un campo obligatorio, el sistema permanece en la sección actual, identifica los campos faltantes y señala el primero para corrección.
- Si el servidor rechaza el guardado, no se realiza ninguna navegación automática.
- En el cierre del Acta se mantiene el botón explícito `← Regresar a Expediente para revisar`.
- La firma impresa no se considera un campo electrónico obligatorio ni bloquea la edición antes de finalizar.
