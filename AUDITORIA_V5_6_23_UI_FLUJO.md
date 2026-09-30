# Auditoría V5.6.25 — Ordenamiento UI y flujo técnico

## Correcciones
- Se elimina el problema de maquetación que desplazaba el contenido principal del Motor de Seguimiento al estar el panel de recuperación dentro de la cuadrícula del aplicativo.
- Se incorpora una tarjeta visible **Cómo va el proceso** con las 8 etapas institucionales y conteo de expedientes por etapa.
- La navegación lateral del Motor de Seguimiento ahora desplaza a las secciones funcionales correspondientes.
- La pantalla del Técnico incorpora una barra de 4 pasos: Denuncia/Solicitud → Acta → Informe Técnico → Evidencias.
- Al finalizar correctamente una actuación técnica, el sistema vuelve automáticamente a Inicio/Mis actuaciones, sin borrar el expediente del servidor.
- Al abrir una nueva actuación asignada, el navegador descarta el estado local anterior y carga el expediente desde el servidor, evitando que casillas, medios de verificación, delimitación o constancias del expediente anterior aparezcan marcadas.
- Al registrar una actuación nueva desde campo, el estado técnico también se inicia limpio.
- En Denuncia/Solicitud del Técnico, el componente ambiental principal se muestra como **registrado y marcado visualmente**, pero queda no editable porque lo define la recepción institucional.
- La selección de componentes adicionales se mantiene separada del componente principal y no permite duplicarlo.
- Se mantienen autenticación, sesiones, alertas y recuperación por correo personal/institucional.

## Pruebas
- JavaScript embebido de Sistema 1: PASS (Node --check).
- JavaScript embebido de Sistema 2: PASS (Node --check).
- API /api/health: PASS, V5.6.25, SQLite, autenticación habilitada.
- Inicio de sesión Gerente por API: PASS.
- Consulta /api/expedientes: PASS.
