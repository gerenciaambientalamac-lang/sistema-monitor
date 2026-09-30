# D06-R1 — Reconstrucción de entrada del Técnico

## Motivo

La pantalla inicial del Sistema 01 mostraba el flujo institucional como texto no interactivo. El Técnico podía ver “1. Denuncia / Solicitud”, pero el elemento no ejecutaba ninguna acción. Además, cuando no había una actuación cargada en el estado local, la bandeja de actuaciones permanecía oculta, dejando al usuario sin una entrada operativa clara.

## Reconstrucción

Se reconstruyó la entrada del módulo sin alterar el modelo institucional D01-D05 ni el núcleo Offline-First D06-R1.

### Cambios

1. Los cuatro pasos del flujo ahora son controles funcionales:
   - 1. Denuncia / Solicitud
   - 2. Acta
   - 3. Informe técnico
   - 4. Evidencias
2. El paso 1 abre la bandeja real de actuaciones del Técnico.
3. La bandeja se muestra aun cuando está vacía y explica que la recepción/asignación corresponde al flujo institucional.
4. Si existe una actuación asignada, el Técnico puede abrirla desde la bandeja.
5. Los pasos 2–4 no permiten avanzar si no existe una actuación seleccionada.
6. Se conserva la regla institucional: el Técnico no crea ni modifica la recepción desde este módulo.
7. Se añadió estado visible de conexión.
8. Se corrigió la ruta del escudo institucional del Sistema 01 para acceso LAN.
9. Se mantuvo IndexedDB, cola, Service Worker, sesión offline, caché de actuaciones, fotografías y GPS de D06-R1.

## Validación

- Auditoría específica GitHub/UI: **13/13 PASS**.
- Sintaxis JavaScript del Sistema 01: PASS.
- Servidor limpio probado en `127.0.0.1:8765`: `/api/health` PASS.
- Página `/01_SISTEMA_INSPECCIONES/`: HTTP 200 PASS.
- La base SQLite de ejecución y datos de prueba no se incluye en el paquete GitHub; el servidor la crea al iniciar.

## Pendiente de validación física

La interacción visual en Chrome/Windows y la prueba Offline-First real en PC/teléfono deben repetirse con esta reconstrucción antes de declarar D06-R1 como validado físicamente.
