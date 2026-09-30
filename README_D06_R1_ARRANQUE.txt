D06-R1 - ARRANQUE CORREGIDO
============================

1) PRUEBA PC + CELULAR / LAN + OFFLINE
---------------------------------------
En la PC SERVIDORA ejecute SOLO:

    INICIAR_D06_R1_LAN_HTTPS.bat

El BAT mostrara la URL HTTPS LAN, por ejemplo:

    https://192.168.1.xxx:8001/

Mantenga abierta la ventana del servidor.

En el celular NO se ejecuta ningun BAT. Abra el navegador y use la URL mostrada por la PC.

2) ACCESO TECNICO
------------------
En la PC puede ejecutar:
    ABRIR_TECNICO_D06_R1.bat

En el celular se entra manualmente a:
    https://IP-DE-LA-PC:8001/01_SISTEMA_INSPECCIONES/

3) ACCESO GERENTE
------------------
En la PC puede ejecutar:
    ABRIR_GERENTE_D06_R1.bat

4) MODO LOCAL SOLO PC
---------------------
Si no se necesita celular/LAN:
    INICIAR_D06_R1_LOCAL.bat

5) PRUEBA OFFLINE
-----------------
Primero conecte el celular al servidor y cargue/sincronice lo necesario.
Luego apague Wi-Fi y datos moviles (modo avion) y realice la inspeccion.
No cierre la ventana del servidor de la PC durante la prueba; el celular debe quedar sin conectividad mientras se simula el trabajo de campo.

NOTA
----
Los BAT V5.6.25/V5.6.26 anteriores fueron retirados de esta distribucion para evitar arrancar una version equivocada.


NOTA DE ARRANQUE D06-R1 — HTTPS
--------------------------------
INICIAR_D06_R1_LAN_HTTPS.bat verifica automáticamente el módulo Python 'cryptography'.
Si no está instalado, intenta instalarlo con 'python -m pip install cryptography' durante la primera puesta en marcha.
La primera instalación requiere Internet. Una vez instalado y generado tls\cert.pem + tls\key.pem, las siguientes ejecuciones no necesitan reinstalar el módulo.

No abrir index.html mediante file:/// para la prueba Offline-First. Debe utilizarse la URL HTTPS LAN que muestra el BAT.


D06-R1 UI — reconstrucción de entrada del Técnico
- Los cuatro pasos del flujo ahora son controles funcionales y accesibles.
- El paso 1 abre la bandeja real de actuaciones del Técnico.
- Si no hay actuaciones, se muestra un estado vacío explícito y un botón de actualización.
- Los pasos 2–4 exigen una actuación seleccionada antes de abrirse.
- La bandeja conserva el flujo institucional: la recepción se crea en Seguimiento/Gerencia y el Técnico solo inicia/continúa la captura.
- El estado de conexión se muestra en la pantalla inicial.
- El escudo institucional del Sistema 01 usa una ruta absoluta del módulo para evitar el icono roto cuando se accede por LAN.
