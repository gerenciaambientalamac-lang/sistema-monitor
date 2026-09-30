# D06-R1 — Reconstrucción Offline-First

## Base
V5.6.26 D05 PC/Móvil Corregido.

## Principio
No se parcheó el Core D01-D05. Se reconstruyó el límite móvil de persistencia y sincronización porque el diseño anterior dependía de `fetch()` directo al servidor y no garantizaba idempotencia.

## Componentes reconstruidos
- IndexedDB `LLE_D06_OFFLINE_R1` versión 2.
- Stores locales: `meta`, `expedientes`, `queue`, `photos`, `gps`, `cache`, `maps`.
- Cola de operaciones con identidad `operation_id`.
- Estados: `PENDIENTE`, `ENVIANDO`, `ERROR_REINTENTABLE`.
- Persistencia de fotografías como `Blob`.
- Persistencia local de GPS.
- Eliminación offline de GPS/fotografías mediante operaciones pendientes.
- Caché de usuario y de actuaciones asignadas.
- Caché del expediente completo de las actuaciones pendientes mientras existe conectividad.
- Detección de servidor disponible separada de `navigator.onLine`.
- Service Worker con fallback de navegación offline.
- PWA manifest.
- Sincronización ordenada y actualización de códigos temporales.

## Idempotencia del servidor
Se incorporó `sync_operations` con `operation_id` único para:
- recepción desde Acta;
- expediente;
- GPS;
- eliminación de GPS;
- fotografía;
- eliminación de fotografía.

Una repetición de la misma operación devuelve la respuesta previamente confirmada y no crea un segundo registro.

## D01-D05
Se conservaron los controles de catálogos, personal, acta, participantes, máquina de estados y autorización de servidor.

## Auditoría
`AUDITORIA_D06_OFFLINE_FIRST_R1.py` → **27/27 PASS**.

También se verificó:
- idempotencia de expediente: PASS;
- idempotencia de GPS: PASS;
- idempotencia de fotografía: PASS;
- idempotencia de recepción offline: PASS;
- base de datos limpia después de pruebas;
- responsive PC/celular 360, 390, 412, 768 y 1366 px sin overflow en ambos sistemas.

## Prueba física pendiente
Todavía no se declara aprobado el trabajo de campo. La siguiente prueba es con un teléfono real:
1. sincronizar conectado;
2. cargar actuación asignada;
3. activar modo avión y apagar Wi-Fi/datos;
4. trabajar en la inspección;
5. registrar GPS;
6. tomar fotografías;
7. guardar/cerrar/reabrir;
8. recuperar conectividad;
9. verificar sincronización sin duplicados en el servidor.
