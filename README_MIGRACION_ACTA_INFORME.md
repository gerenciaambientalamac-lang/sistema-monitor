# V5.1 – Prueba limpia: migración automática Acta → Informe

Esta versión conserva la arquitectura V5.1 con SQLite y añade la regla de que el Informe Técnico reutiliza automáticamente la información levantada en el Acta.

## Reglas de esta prueba
- El Acta es la fuente primaria de los datos levantados en campo.
- El Informe reutiliza automáticamente identificación, origen, ubicación, técnico, fecha/hora, objeto, alcance, hechos, manifestaciones, medios de verificación, coordenadas y evidencias.
- Las evidencias y coordenadas se mantienen vinculadas al expediente; no se cargan nuevamente en el Informe.
- Los hallazgos del Informe pueden iniciarse a partir de los hechos del Acta, quedando el análisis/valoración a cargo del técnico.
- La revisión y validación institucional se gestionan en el Motor de Seguimiento.
- No se incorpora V.º B.º del Gerente dentro del Informe.
- Esta carpeta inicia sin base de datos para comprobar que SQLite se crea desde cero.

## Inicio
Ejecutar `INICIAR_SISTEMA_V5_1.bat` y abrir `http://localhost:8001/`.
