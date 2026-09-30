# V5.5.1 — Modelo Maestro del Acta de Inspección

## Objetivo
Esta versión congela el modelo funcional del Acta como documento de campo transversal. El Acta captura los datos comunes una sola vez en el expediente y los prepara para alimentar posteriormente cualquiera de los siete formularios técnicos.

## Separación conceptual: origen, componente y formulario
Para evitar confusiones, el sistema separa tres conceptos que no deben mezclarse:

- **Origen de la actuación:** indica por qué se inicia la diligencia (por ejemplo, denuncia ambiental, solicitud de inspección, requerimiento institucional, oficio o seguimiento).
- **Componente ambiental:** identifica el asunto o componente ambiental que será verificado en campo.
- **Formulario técnico especializado:** corresponde al formato de informe que se utilizará posteriormente según la actuación.

### Catálogo de componentes ambientales
- OI — Otros componentes ambientales
- RS — Residuos sólidos
- VH — Vertidos / descargas
- RH — Recursos hídricos
- AU — Arbolado urbano
- TP — Tala / poda
- CO — Contaminación ambiental
- CR — Ruido
- CS — Suelo
- MT — Movimientos de tierra
- EP — Espacios públicos / áreas verdes
- ZR — Zonas de protección
- GR — Gestión de riesgo

**Regla:** “Denuncia ambiental” ya no se presenta como componente ambiental. Se registra exclusivamente como **Origen de la actuación** cuando corresponda.

### Siete formularios maestros de informe
- DA — Denuncia Ambiental
- TP — Tala y Poda
- RS — Residuos
- CO — Contaminación
- MT — Movimientos de Tierra
- RH — Recursos Hídricos
- GR — Gestión de Riesgo

Los formularios especializados se desarrollarán/ajustarán en la siguiente etapa; el Acta permanece transversal y común.

## Datos comunes del expediente
1. Código automático.
2. Tipo de actuación.
3. Fecha, hora de inicio y finalización.
4. Técnico Ambiental Distrital responsable y participantes.
5. Modalidad de inspección.
6. Origen de la actuación.
7. Referencia externa/oficio.
8. Fecha de recepción/solicitud.
9. Solicitante/denunciante y condición.
10. Contacto, cuando corresponda.
11. Institución solicitante.
12. Titular/propietario/responsable.
13. Denunciado/persona señalada, cuando aplique.
14. Persona que atiende y calidad/representación.
15. Departamento, municipio y distrito.
16. Cantón/caserío/colonia/urbanización.
17. Dirección/domicilio.
18. Referencia del sitio.
19. Lugar específico.
20. Objeto, alcance y limitaciones.
21. Medios de verificación.
22. Hechos constatados.
23. Evidencias, fotografías y documentación.
24. Mediciones/muestreo.
25. Manifestaciones.
26. Observaciones técnicas de campo.
27. Actuaciones técnicas y seguimiento.
28. Cierre y constancias de firma.

## Georreferenciación
Los puntos GPS se almacenan como registros múltiples, con ID, latitud, longitud, WGS84, precisión, altitud opcional, fecha/hora, descripción y hecho relacionado.

## Fotografía
Las fotografías se almacenan como archivos reales asociados al expediente, con código, fecha/hora, descripción, punto GPS y hecho relacionado. Se conserva control de integridad SHA-256 en el servidor.

## Regla de no duplicidad
El Acta es la fuente de los datos de campo comunes. El formulario técnico especializado agrega únicamente las variables propias de la materia. El Informe reutiliza los datos del expediente, Acta, evidencias y formulario especializado.

## Delimitación institucional
El Acta documenta hechos y actuaciones observados durante la diligencia. No constituye por sí misma una resolución sancionadora, no determina responsabilidad y no certifica la validez, vigencia, autenticidad o suficiencia de permisos o documentos emitidos por otras instituciones.

## Estado de desarrollo
Esta entrega es una base funcional para pruebas. Las Actas especializadas y la generación Word/PDF se desarrollarán después de validar este modelo.

## Política de credenciales durante desarrollo V5.5.1

Durante la etapa de desarrollo y pruebas se mantienen las cuentas provisionales estables:

- `tecnico` / `LLE-Tecnico-2026!`
- `gerente` / `LLE-Gerente-2026!`
- `admin` / `LLE-Admin-2026!`

La aplicación no fuerza el cambio de contraseña inicial durante esta etapa. El cambio de nombres de usuario y contraseñas queda reservado para la fase de administración institucional.

## Actualización de código sin reiniciar datos

Las correcciones de código deben conservar `sistema_gestion_ambiental.sqlite3`. No se debe eliminar ni reemplazar la base de datos para instalar una corrección, salvo que una prueba haya sido expresamente definida como instalación limpia.
