# D04 — Integridad del Acta Maestro y devolución/corrección — V5.6.26

## Alcance
D04 continúa directamente sobre V5.6.26 D03. No modifica el Core, la máquina de estados ni los contratos institucionales ya validados.

## Hallazgos corregidos

### 1. Tipo de actuación y modalidad podían ser alterados por un cliente técnico
Aunque D01 unificó los catálogos y la interfaz dejó el tipo de actuación controlado por recepción, el servidor todavía aceptaba una mutación enviada directamente a `/api/expediente`.

### Corrección
El servidor toma de la recepción:
- Tipo de actuación.
- Modalidad de inspección.

Si el Técnico intenta cambiar cualquiera de esos valores, la operación es rechazada.

Los valores se vuelven a escribir desde la fuente de recepción antes de persistir el expediente.

### 2. Alcance de devolución no estaba limitado por catálogo servidor
La interfaz mostraba un catálogo de campos/secciones de corrección, pero el servidor aceptaba cualquier cadena enviada como alcance.

### Corrección
Se incorporó `CORRECTION_SCOPE_KEYS` como catálogo servidor. El Gerente solo puede devolver un expediente con campos/secciones reconocidos por el sistema. Los valores se normalizan y se eliminan duplicados antes de persistirlos.

## Reglas conservadas
- D01: catálogos maestros, distritos, origen y componentes.
- D02: gestión de personal por Gerente y control de técnicos activos/inactivos.
- D03: conservación histórica de participantes que posteriormente pasan a inactivos.
- La devolución continúa limitada a los campos autorizados por el Gerente.
- El estado continúa siendo propiedad del servidor.

## Resultado
Auditoría D04: **32/32 PASS**.
