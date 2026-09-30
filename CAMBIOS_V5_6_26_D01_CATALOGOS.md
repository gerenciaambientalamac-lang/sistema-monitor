# D01 — Catálogos maestros y consistencia PC → API → SQLite

## Correcciones incorporadas

1. **Distritos**: se conserva un único catálogo canónico de cinco distritos:
   - Antiguo Cuscatlán
   - Huizúcar
   - Nuevo Cuscatlán
   - San José Villanueva
   - Zaragoza
2. **Tipo de actuación**: se normaliza el catálogo a ocho valores:
   - Inspección
   - Visita técnica
   - Verificación
   - Seguimiento
   - De oficio
   - A solicitud
   - Interinstitucional
   - Otra
3. **Modalidad de inspección**: se valida por identificador estable:
   - INDIVIDUAL
   - CONJUNTA_TAD
   - CONJUNTA_MUNICIPAL
   - INTERINSTITUCIONAL
4. **Origen**: el servidor ahora valida el catálogo antes de crear una recepción.
5. **Distrito**: el servidor valida el distrito al crear una recepción cuando se informa.
6. **Tipo de actuación y modalidad**: el servidor valida ambos catálogos durante recepción y guardado técnico.
7. El Monitor de Seguimiento incorpora **Tipo de actuación** en la recepción institucional.
8. El Tipo de actuación del Acta queda como dato proveniente de la recepción y no puede divergir mediante edición local.
9. Se corrige la identificación de versión del servidor: `V5.6.26` en health, banner HTTP y arranque.

## Regla de arquitectura
No se modificaron Core, flujo de estados, permisos, códigos documentales ni motores. D01 corrige únicamente catálogo, validación y propagación de datos.
