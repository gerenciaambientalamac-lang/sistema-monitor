# D02 — Personal técnico, activación y asignación — V5.6.26

## Alcance
Se continúa sobre la V5.6.26 corregida en D01, sin modificar Core, máquina de estados ni contratos de componentes.

## Correcciones aplicadas
1. La gestión de altas/bajas/activación del personal técnico queda administrada exclusivamente por el **Gerente Ambiental** desde API y UI.
2. El alta normaliza espacios del nombre y cargo.
3. Se rechazan nombres/cargos vacíos o excesivamente largos.
4. Se evita duplicar personal aunque el nombre cambie solo en mayúsculas/minúsculas o espacios.
5. La modificación de estado exige que el registro de personal exista.
6. La interfaz de configuración de personal solo se muestra al rol Gerente.
7. Se conserva la regla existente: personal inactivo no puede recibir nuevas asignaciones, pero permanece en el histórico.

## Auditoría
`AUDITORIA_D02_PERSONAL_V5_6_26.py`

Resultado: **22/22 PASS**.

La base de datos de la versión entregada se reconstruyó desde la V5.6.26 D01 limpia después de las pruebas; no contiene los expedientes utilizados durante la auditoría.
