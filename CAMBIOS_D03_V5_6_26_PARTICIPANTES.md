# D03 — Integridad de participantes y trazabilidad de asignación — V5.6.26

## Alcance
Se continúa sobre V5.6.26 D02. No se modifica el Core, la máquina de estados ni los contratos de componentes.

## Hallazgo corregido
La validación de personal participante exigía que todo participante estuviera activo en cada guardado del expediente. Esto impedía editar un expediente histórico cuando uno de sus participantes había sido desactivado posteriormente.

## Corrección
- Un técnico participante **inactivo no puede incorporarse a una actuación nueva**.
- Un técnico participante que **ya estaba registrado en ese expediente antes de quedar inactivo puede conservarse y el expediente puede seguir editándose**.
- El responsable mantiene la misma regla histórica ya existente: puede permanecer como responsable del expediente aunque posteriormente quede inactivo.
- La asignación de actuaciones sigue siendo exclusiva del Gerente Ambiental.
- El distrito y origen registrados en recepción siguen siendo inmutables desde el módulo técnico.

## Resultado
Auditoría D03: **35/35 PASS**.
