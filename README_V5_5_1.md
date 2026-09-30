# V5.5.1 — Evidencia fotográfica real y múltiples puntos GPS

**Sistema:** Gerencia Ambiental y Gestión de Riesgo — Alcaldía Municipal de La Libertad Este.

## Punto de partida
V5.5.1 se desarrolla sobre el CORE V5.4, cuya prueba integral previa obtuvo **50/50 PASS** y quedó aprobada para continuar a la siguiente etapa.

## Alcance de esta versión
- Captura de fotografías reales desde cámara o galería mediante `multipart/form-data`.
- Almacenamiento físico de fotografías fuera de `payload_json`, en `storage/fotografias/<expediente>/`.
- Metadatos fotográficos normalizados: código FOT-###, nombre original, MIME, tamaño, SHA-256, descripción, fecha de captura, usuario, punto GPS relacionado y hecho relacionado.
- Múltiples puntos GPS por expediente, cada uno con código P-###, latitud, longitud, DATUM WGS84, precisión, altitud opcional, fecha/hora, descripción y hecho relacionado.
- Relación Fotografía ↔ Punto GPS ↔ Hecho.
- Consulta autenticada de evidencias y de fotografías.
- Validación de tipo/contenido de imagen y límite de 12 MB por fotografía.
- Bloqueo de nuevas modificaciones de fotografías/GPS cuando el expediente deja de admitir edición.
- Integridad SQLite y claves foráneas.

## Modelo de datos
### `fotografias`
Guarda la referencia física y trazabilidad de cada fotografía. El archivo binario no se inserta en `payload_json`.

### `puntos_gps`
Guarda cada lectura GPS de forma independiente; no se limita a una sola coordenada por expediente.

### Almacenamiento
`storage/fotografias/<codigo_expediente>/` contiene los archivos con nombres internos aleatorios. El nombre original queda como metadato.

## Reglas institucionales preservadas
- El Técnico Ambiental Distrital responsable continúa siendo quien registra la actuación técnica.
- El distrito de la actuación sigue siendo independiente del técnico.
- Los participantes continúan sujetos a personal activo.
- El cliente no determina `status` ni identidad.
- Las fotografías y GPS no pueden modificarse después del bloqueo del expediente.
- La validación institucional continúa correspondiendo al Motor de Seguimiento.

## Prueba funcional V5.5.1
La batería funcional ejecutada sobre una base SQLite nueva obtuvo **15 PASS / 0 FAIL**, incluyendo: login, creación de borrador, dos puntos GPS, fotografía real, vínculos GPS/hecho, recuperación del archivo, hash SHA-256, finalización y bloqueo posterior, `integrity_check` y `foreign_key_check`.

## Importante
Esta es una versión funcional de desarrollo. No se considera release institucional definitivo hasta completar las pruebas posteriores previstas: Actas especializadas, informes especializados, generación Word/PDF, respaldos, despliegue LAN y pruebas integrales finales.

## Credenciales provisionales de prueba — V5.5.1

Durante la fase de desarrollo y pruebas, las cuentas provisionales se mantienen sincronizadas con las credenciales publicadas para esta versión:

- `tecnico` / `LLE-Tecnico-2026!` — rol TECNICO
- `gerente` / `LLE-Gerente-2026!` — rol GERENTE
- `admin` / `LLE-Admin-2026!` — rol ADMIN

En esta versión de desarrollo, al inicializar el servidor se sincronizan nuevamente el hash de contraseña, el estado activo y `debe_cambiar=0` de estas tres cuentas. Esto evita que una base SQLite reutilizada conserve contraseñas modificadas durante pruebas anteriores.

**Importante:** esta sincronización automática es exclusivamente para cuentas provisionales de desarrollo. Antes de producción debe sustituirse por gestión real de usuarios, política institucional de contraseñas y controles de administración de cuentas.
