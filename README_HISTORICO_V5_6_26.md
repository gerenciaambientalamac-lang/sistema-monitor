## V5.6.25
Registro de denuncia/solicitud desde la pantalla de Acta por Técnico, con modo Sí/No, selección de expediente existente o alta de recepción mínima. La nueva actuación genera alerta al Gerente y queda pendiente de revisión/asignación; el Técnico creador puede continuar el Acta, pero no finalizar Informe hasta asignación formal.

# Sistema Integral de Gestión Ambiental y Gestión de Riesgo — La Libertad Este

## Versión
**V5.6.9 — ESTABILIZACIÓN**

## Flujo operativo institucional definitivo
**Denuncia / Solicitud → Asignación por el Gerente Ambiental → Acta de Inspección → Informe Técnico → Evidencias → Revisión / Validación → Remisión / Continuación → Expediente / Consulta integral.**

El **Expediente no es una pantalla de captura del Técnico**. Es la consulta integral del caso desde el Dashboard del Motor de Seguimiento, conservando recepción, asignación, Acta, Informe, evidencias, revisión, remisión, seguimiento, cierre e historial.

## Sistema 1 — Técnico Ambiental Distrital
El trabajo técnico se presenta en el orden: **1. Denuncia / Solicitud recibida (consulta) → 2. Acta de Inspección → 3. Informe Técnico → 4. Evidencias**.

Los datos de recepción se muestran como antecedente y no se modifican desde el Acta. El Informe distingue el **código de expediente**, el **código del Acta** y el **código del Informe**.

## Sistema 2 — Motor de Seguimiento
El Gerente Ambiental gestiona la recepción, asigna actuaciones a Técnicos Ambientales Distritales activos, revisa el Dashboard, registra validación o devolución y determina la continuación correspondiente, incluida la remisión a instituciones externas o dependencias municipales cuando proceda.

La remisión exige destino y motivo. El cierre exige validación institucional previa y un resultado o motivo de cierre.

## Despliegue local
Para una sola computadora use `INICIAR_SISTEMA_V5_6_22.bat`.

Para una prueba en red local use `INICIAR_SISTEMA_LAN_V5_6_22.bat` **solo en la PC que actuará como servidor**. Desde la PC del Gerente/Técnico se accederá mediante `http://IP-DEL-SERVIDOR:8001/`. Windows Firewall puede requerir autorización de Python para redes privadas.

## Auditoría y límites
Esta es una versión de desarrollo funcional para pruebas. No debe considerarse release de producción hasta completar pruebas institucionales en red, generación Word/PDF, respaldos, gestión real de usuarios, MFA, endurecimiento de despliegue y pruebas de seguridad/penetración.

No incluya en GitHub bases SQLite de producción, credenciales reales, sesiones, secretos ni datos personales.

## V5.6.11 — Alertas internas

Se incorporan alertas internas por usuario y expediente. El Gerente recibe alertas cuando ingresa una actuación desde un Técnico o cuando un Informe Técnico es finalizado y enviado a revisión. El Técnico recibe alertas cuando se le asigna una actuación, cuando un informe es devuelto para corrección, cuando se valida y cuando el expediente es remitido/finalizado. Las alertas quedan persistidas en SQLite con fecha, usuario, expediente, evento, estado leído/no leído y acción.

El módulo técnico incluye opciones locales para **Imprimir / guardar como PDF** mediante el diálogo de impresión del navegador y **Descargar Word (.doc)** mediante HTML compatible con Microsoft Word. La generación de archivos no equivale a validación institucional.

## V5.6.25 — Lanzadores corregidos

Esta carpeta corresponde a V5.6.25. Para una sola PC use `INICIAR_SISTEMA_V5_6_22.bat`. Para usar esta PC como servidor en la red local use `INICIAR_SISTEMA_LAN_V5_6_22.bat`. Las demás computadoras solo abren `http://IP-DEL-SERVIDOR:8001/` y no ejecutan el BAT LAN.


### Acceso LAN V5.6.26
En la PC servidor (Gerente) usar `INICIAR_SISTEMA_LAN_V5_6_26.bat`; el servidor detecta su IPv4 LAN y abre automáticamente el Monitor de Seguimiento. En la PC Técnico usar `INICIAR_TECNICO_LAN_V5_6_26.bat`, que abre automáticamente el Sistema de Inspecciones contra el servidor `192.168.1.175` para la prueba actual. No se requiere Python en la PC cliente. Para instalación definitiva se recomienda reservar la IP del servidor o reemplazarla por un nombre DNS institucional.

--- D06-R1 ARRANQUE CORREGIDO ---
Para la prueba PC + celular + Offline First, ejecutar en la PC: INICIAR_D06_R1_LAN_HTTPS.bat.
El celular no ejecuta BAT; usa la URL HTTPS LAN mostrada por la PC. Los lanzadores anteriores V5.6.25/V5.6.26 fueron retirados de esta distribucion para evitar confusiones de version.
