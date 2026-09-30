# V5.6.25 — PDF directo

- Se separan las acciones de **Imprimir** y **Guardar PDF** en Acta e Informe Técnico.
- **Guardar PDF** genera y descarga directamente un archivo `.pdf` desde el servidor, sin abrir el diálogo de impresión, cuando el servidor dispone de un motor PDF compatible.
- En Windows se utiliza Microsoft Edge/Google Chrome en modo headless; en entornos donde esté disponible, WeasyPrint se utiliza como alternativa.
- Si el motor PDF no está disponible, el sistema conserva el flujo alternativo de impresión y permite usar “Guardar como PDF” del navegador.
- La generación del documento no cambia el estado, no valida y no finaliza la actuación.
- Se incorporó `/api/documento/pdf`, protegido por sesión autenticada y con límites de tamaño y nombre de archivo.
