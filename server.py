from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import ssl
from urllib.parse import urlparse, quote
from http import cookies
import json, os, sqlite3, datetime, hashlib, hmac, secrets, re, threading, time, mimetypes, io, smtplib, subprocess, tempfile, shutil
from pathlib import Path

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'sistema_gestion_ambiental.sqlite3')
MEDIA_ROOT = os.path.join(ROOT, 'storage', 'fotografias')
os.makedirs(MEDIA_ROOT, exist_ok=True)
MAX_PHOTO_BYTES = 12_000_000
APP_VERSION = 'V5.6.26'
ALLOWED_PHOTO_TYPES = {'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}
DISTRICTS = ['Antiguo Cuscatlán','Huizúcar','Nuevo Cuscatlán','San José Villanueva','Zaragoza']
# Componentes ambientales: se seleccionan una sola vez en la recepción y permanecen inmutables durante la actuación técnica.
ALLOWED_COMPONENTS = {'OI','RS','VH','RH','AU','TP','CO','CR','CS','EP','ZR','MT','GR'}
VALID_STATUSES = {'RECIBIDO_PENDIENTE_ASIGNACION','ASIGNADO_A_INSPECCION','BORRADOR','INFORME_FINALIZADO_PENDIENTE_VB','DEVUELTO','VB_APROBADO','REMITIDO','FINALIZADO'}
ORIGINS = {'Denuncia ambiental','Solicitud de inspección','Requerimiento institucional','Oficio','Inspección de oficio','Seguimiento','Acuerdo del Concejo Municipal','Remisión de dependencia municipal','Solicitud ciudadana','Otro'}
ACTION_TYPES = {'Inspección','Visita técnica','Verificación','Seguimiento','De oficio','A solicitud','Interinstitucional','Otra'}
INSPECTION_MODALITIES = {'INDIVIDUAL','CONJUNTA_TAD','CONJUNTA_MUNICIPAL','INTERINSTITUCIONAL'}
CORRECTION_SCOPE_KEYS = {'tecnicos_participantes','modalidad_inspeccion','titular','lugar','acta_fecha','acta_hora_inicio','acta_hora_fin','acta_objeto','acta_alcance','limitaciones','medios','facts','trees','evidence','evidencias','manifestaciones','observaciones_campo','actuacion','findings','analisis','normativa'}
SESSION_HOURS = 8
PBKDF2_ITERS = 210000
LOGIN_LIMIT={}; LOGIN_LOCK=threading.Lock()
SAFE_STATIC = {'index.html','01_SISTEMA_INSPECCIONES/index.html','01_SISTEMA_INSPECCIONES/escudo_la_libertad_este.png','01_SISTEMA_INSPECCIONES/offline-core.js','01_SISTEMA_INSPECCIONES/sw.js','01_SISTEMA_INSPECCIONES/manifest.json','02_MOTOR_SEGUIMIENTO/index.html','02_MOTOR_SEGUIMIENTO/escudo_la_libertad_este.png'}

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS expedientes (
 id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL UNIQUE, referencia TEXT, anio INTEGER, tipo TEXT,
 origen TEXT, distrito TEXT, tecnico TEXT, status TEXT NOT NULL DEFAULT 'BORRADOR', payload_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS versiones (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id), version INTEGER NOT NULL,
 estado TEXT NOT NULL, payload_json TEXT NOT NULL, creado_por TEXT NOT NULL, creado_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS historial (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id), accion TEXT NOT NULL,
 usuario TEXT NOT NULL, observacion TEXT, documento TEXT, seccion TEXT, correccion_requerida TEXT, fecha TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS evidencias (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id), codigo TEXT, tipo TEXT,
 lat REAL, lng REAL, precision_m REAL, descripcion TEXT, fecha TEXT);
CREATE TABLE IF NOT EXISTS documentos (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id), tipo TEXT NOT NULL,
 ruta TEXT, version INTEGER, hash TEXT, fecha TEXT);
CREATE TABLE IF NOT EXISTS personal (
 id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE, cargo TEXT NOT NULL DEFAULT 'Técnico Ambiental Distrital',
 activo INTEGER NOT NULL DEFAULT 1, creado_at TEXT NOT NULL, actualizado_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS participantes_inspeccion (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id) ON DELETE CASCADE,
 personal_id INTEGER NOT NULL REFERENCES personal(id), rol TEXT NOT NULL DEFAULT 'PARTICIPANTE', UNIQUE(expediente_id, personal_id));
CREATE TABLE IF NOT EXISTS usuarios (
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, salt TEXT NOT NULL,
 rol TEXT NOT NULL CHECK(rol IN ('TECNICO','GERENTE','ADMIN')), personal_id INTEGER REFERENCES personal(id), activo INTEGER NOT NULL DEFAULT 1,
 debe_cambiar INTEGER NOT NULL DEFAULT 0, email TEXT,
 creado_at TEXT NOT NULL, actualizado_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tokens_recuperacion (
 id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
 token_hash TEXT NOT NULL UNIQUE, creado_at TEXT NOT NULL, expira_at TEXT NOT NULL, usado INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_recup_token ON tokens_recuperacion(token_hash,usado,expira_at);
CREATE TABLE IF NOT EXISTS sesiones (
 id INTEGER PRIMARY KEY AUTOINCREMENT, token_hash TEXT NOT NULL UNIQUE, usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
 creado_at TEXT NOT NULL, expira_at TEXT NOT NULL, revocada INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS notificaciones (
 id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT NOT NULL, expediente_codigo TEXT, tipo TEXT NOT NULL, titulo TEXT NOT NULL, mensaje TEXT NOT NULL, fecha TEXT NOT NULL, leida INTEGER NOT NULL DEFAULT 0, accion TEXT, UNIQUE(usuario, expediente_codigo, tipo, fecha));
CREATE INDEX IF NOT EXISTS idx_notif_usuario ON notificaciones(usuario,leida,fecha);
CREATE INDEX IF NOT EXISTS idx_exp_status ON expedientes(status); CREATE INDEX IF NOT EXISTS idx_exp_tipo ON expedientes(tipo);
CREATE INDEX IF NOT EXISTS idx_exp_distrito ON expedientes(distrito); CREATE INDEX IF NOT EXISTS idx_exp_tecnico ON expedientes(tecnico);
CREATE INDEX IF NOT EXISTS idx_hist_exp ON historial(expediente_id); CREATE INDEX IF NOT EXISTS idx_part_exp ON participantes_inspeccion(expediente_id);
CREATE INDEX IF NOT EXISTS idx_ses_token ON sesiones(token_hash);
CREATE TABLE IF NOT EXISTS auditoria_eliminaciones (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL, tecnico TEXT NOT NULL, usuario TEXT NOT NULL, fecha TEXT NOT NULL, motivo TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS recepciones (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL UNIQUE REFERENCES expedientes(id) ON DELETE CASCADE,
 fecha_recepcion TEXT NOT NULL, origen TEXT NOT NULL, referencia_externa TEXT, institucion_solicitante TEXT, solicitante TEXT, condicion TEXT, contacto TEXT,
 descripcion_inicial TEXT, prioridad TEXT NOT NULL DEFAULT 'Media', recibido_por TEXT NOT NULL, recibido_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS asignaciones (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id) ON DELETE CASCADE,
 tecnico TEXT NOT NULL, gerente_usuario TEXT NOT NULL, fecha_asignacion TEXT NOT NULL, observacion TEXT, activa INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS idx_recep_exp ON recepciones(expediente_id);
CREATE INDEX IF NOT EXISTS idx_asig_exp ON asignaciones(expediente_id);
CREATE INDEX IF NOT EXISTS idx_asig_tecnico ON asignaciones(tecnico,activa);
CREATE TABLE IF NOT EXISTS fotografias (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id) ON DELETE CASCADE,
 codigo TEXT NOT NULL, archivo TEXT NOT NULL, nombre_original TEXT NOT NULL, mime_type TEXT NOT NULL, tamano INTEGER NOT NULL,
 sha256 TEXT NOT NULL, descripcion TEXT, fecha_captura TEXT, subido_at TEXT NOT NULL, subido_por TEXT NOT NULL,
 gps_point_id INTEGER, hecho_id TEXT, UNIQUE(expediente_id,codigo), UNIQUE(archivo));
CREATE TABLE IF NOT EXISTS puntos_gps (
 id INTEGER PRIMARY KEY AUTOINCREMENT, expediente_id INTEGER NOT NULL REFERENCES expedientes(id) ON DELETE CASCADE,
 codigo TEXT NOT NULL, lat REAL NOT NULL, lng REAL NOT NULL, datum TEXT NOT NULL DEFAULT 'WGS84', precision_m REAL, altitud_m REAL,
 fecha_hora TEXT NOT NULL, descripcion TEXT, hecho_id TEXT, UNIQUE(expediente_id,codigo));
CREATE INDEX IF NOT EXISTS idx_fotos_exp ON fotografias(expediente_id);
CREATE INDEX IF NOT EXISTS idx_gps_exp ON puntos_gps(expediente_id);
CREATE TABLE IF NOT EXISTS sync_operations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, operation_id TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, response_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sync_operation ON sync_operations(operation_id);
"""

def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def dtplus(hours): return (datetime.datetime.now()+datetime.timedelta(hours=hours)).isoformat(timespec='seconds')

def conn():
    c=sqlite3.connect(DB, timeout=15)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA busy_timeout=15000')
    c.executescript(SCHEMA)
    cols={r['name'] for r in c.execute('PRAGMA table_info(usuarios)').fetchall()}
    if 'debe_cambiar' not in cols:
        c.execute('ALTER TABLE usuarios ADD COLUMN debe_cambiar INTEGER NOT NULL DEFAULT 0')
        c.commit()
    cols={r['name'] for r in c.execute('PRAGMA table_info(usuarios)').fetchall()}
    if 'email' not in cols:
        c.execute('ALTER TABLE usuarios ADD COLUMN email TEXT')
        c.commit()
    # Durante desarrollo/pruebas las cuentas institucionales provisionales se mantienen
    # sincronizadas con las credenciales publicadas para esta versión. Esto evita que
    # una SQLite reutilizada conserve una contraseña de una prueba anterior.
    defaults = {
        'admin': 'LLE-Admin-2026!',
        'gerente': 'LLE-Gerente-2026!',
        'tecnico': 'LLE-Tecnico-2026!'
    }
    for username, password in defaults.items():
        row = c.execute('SELECT id,salt,password_hash FROM usuarios WHERE username=?', (username,)).fetchone()
        if row:
            salt, ph = hash_password(password)
            c.execute('UPDATE usuarios SET salt=?,password_hash=?,debe_cambiar=0,activo=1,actualizado_at=? WHERE id=?',
                       (salt,ph,now(),row['id']))
    c.commit()
    return c

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), PBKDF2_ITERS)
    return salt, dk.hex()

def verify_password(password, salt, expected):
    _, got=hash_password(password,salt); return hmac.compare_digest(got,expected)

def token_hash(token): return hashlib.sha256(token.encode()).hexdigest()

RECOVERY_MINUTES = 30

def smtp_config():
    host=os.environ.get('LLE_SMTP_HOST','').strip()
    port=int(os.environ.get('LLE_SMTP_PORT','587') or '587')
    user=os.environ.get('LLE_SMTP_USER','').strip()
    password=os.environ.get('LLE_SMTP_PASSWORD','')
    sender=os.environ.get('LLE_SMTP_FROM',user).strip()
    use_tls=os.environ.get('LLE_SMTP_TLS','1').strip().lower() not in ('0','false','no')
    app_base=os.environ.get('LLE_PUBLIC_BASE_URL','').strip().rstrip('/')
    return host,port,user,password,sender,use_tls,app_base

def send_recovery_email(to_email, username, reset_url):
    host,port,user,password,sender,use_tls,_=smtp_config()
    if not host or not sender:
        raise RuntimeError('La recuperación por correo requiere configurar LLE_SMTP_HOST y LLE_SMTP_FROM en el servidor.')
    from email.message import EmailMessage
    msg=EmailMessage()
    msg['Subject']='Recuperación de acceso — Sistema de Gestión Ambiental'
    msg['From']=sender
    msg['To']=to_email
    body=(
        'Solicitud de recuperación de acceso\n\n'
        f'Usuario: {username}\n\n'
        f'Use el siguiente enlace dentro de los próximos {RECOVERY_MINUTES} minutos para establecer una nueva contraseña:\n'
        f'{reset_url}\n\n'
        'Este enlace es de un solo uso. Si usted no realizó esta solicitud, ignore este mensaje.\n\n'
        'Alcaldía Municipal de La Libertad Este — Gerencia Ambiental y Gestión de Riesgo\n'
    )
    msg.set_content(body)
    with smtplib.SMTP(host,port,timeout=20) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls(); smtp.ehlo()
        if user:
            smtp.login(user,password)
        smtp.send_message(msg)

def create_recovery_request(o, handler):
    ident=str(o.get('usuario_o_correo','')).strip()
    generic={'ok':True,'message':'Si existe una cuenta activa asociada a los datos proporcionados y tiene correo registrado, recibirá instrucciones de recuperación.'}
    if not ident or len(ident)>200: return generic
    base=smtp_config()[-1] or f'http://{handler.headers.get("Host","127.0.0.1:8001")}'
    c=conn(); row=c.execute('SELECT * FROM usuarios WHERE activo=1 AND (username=? OR lower(email)=lower(?))',(ident,ident)).fetchone()
    if not row or not row['email']:
        c.close(); return generic
    raw=secrets.token_urlsafe(32); th=token_hash(raw); exp=(datetime.datetime.now()+datetime.timedelta(minutes=RECOVERY_MINUTES)).isoformat(timespec='seconds')
    c.execute('UPDATE tokens_recuperacion SET usado=1 WHERE usuario_id=? AND usado=0',(row['id'],))
    c.execute('INSERT INTO tokens_recuperacion(usuario_id,token_hash,creado_at,expira_at,usado) VALUES(?,?,?,?,0)',(row['id'],th,now(),exp))
    c.commit(); c.close()
    reset_url=base + '/01_SISTEMA_INSPECCIONES/?reset=' + quote(raw,safe='')
    try:
        send_recovery_email(row['email'],row['username'],reset_url)
    except Exception:
        c=conn(); c.execute('UPDATE tokens_recuperacion SET usado=1 WHERE token_hash=?',(th,)); c.commit(); c.close()
        raise
    return generic

def complete_recovery(o):
    token=str(o.get('token','')).strip(); new=str(o.get('password_nueva',''))
    if not token: raise ValueError('Token de recuperación requerido.')
    if len(new)<12 or len(new)>200: raise ValueError('La nueva contraseña debe tener entre 12 y 200 caracteres.')
    c=conn(); row=c.execute('SELECT tr.*,u.id uid FROM tokens_recuperacion tr JOIN usuarios u ON u.id=tr.usuario_id WHERE tr.token_hash=? AND tr.usado=0 AND tr.expira_at>? AND u.activo=1',(token_hash(token),now())).fetchone()
    if not row: c.close(); raise PermissionError('El enlace de recuperación no es válido o ya expiró.')
    ns,nh=hash_password(new)
    c.execute('UPDATE usuarios SET salt=?,password_hash=?,debe_cambiar=0,actualizado_at=? WHERE id=?',(ns,nh,now(),row['uid']))
    c.execute('UPDATE tokens_recuperacion SET usado=1 WHERE id=?',(row['id'],))
    c.execute('UPDATE sesiones SET revocada=1 WHERE usuario_id=?',(row['uid'],))
    c.commit(); c.close(); return {'ok':True}

def set_recovery_email(o,u):
    email=str(o.get('email','')).strip()
    if not email: raise ValueError('Ingrese un correo electrónico de recuperación.')
    if len(email)>254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError('El correo electrónico no tiene un formato válido.')
    c=conn(); c.execute('UPDATE usuarios SET email=?,actualizado_at=? WHERE id=?',(email,now(),u['id'])); c.commit(); c.close()

def ensure_admin():
    c=conn();
    try:
        n=c.execute('SELECT COUNT(*) n FROM usuarios').fetchone()['n']
        if n==0:
            t=now();
            c.execute("INSERT OR IGNORE INTO personal(nombre,cargo,activo,creado_at,actualizado_at) VALUES(?,?,?,?,?)",('Técnico Ambiental Distrital de Prueba','Técnico Ambiental Distrital',1,t,t))
            pid=c.execute('SELECT id FROM personal WHERE nombre=?',('Técnico Ambiental Distrital de Prueba',)).fetchone()['id']
            defaults=[
                ('admin','LLE-Admin-2026!','ADMIN',None),
                ('gerente','LLE-Gerente-2026!','GERENTE',None),
                ('tecnico','LLE-Tecnico-2026!','TECNICO',pid)]
            for u,p,r,pid in defaults:
                s,h=hash_password(p); c.execute('INSERT INTO usuarios(username,password_hash,salt,rol,personal_id,activo,debe_cambiar,creado_at,actualizado_at) VALUES(?,?,?,?,?,?,?,?,?)',(u,h,s,r,pid,1,1,t,t))
            c.commit()
    finally: c.close()

def login_allowed(ip):
    t=time.time()
    with LOGIN_LOCK:
        arr=[x for x in LOGIN_LIMIT.get(ip,[]) if t-x<300]
        LOGIN_LIMIT[ip]=arr
        return len(arr)<10

def note_login(ip):
    with LOGIN_LOCK: LOGIN_LIMIT.setdefault(ip,[]).append(time.time())

def authenticate(c, username, password):
    row=c.execute('SELECT * FROM usuarios WHERE username=? AND activo=1',(username.strip(),)).fetchone()
    if not row or not verify_password(password,row['salt'],row['password_hash']): return None
    return row

def create_session(c,user_id):
    raw=secrets.token_urlsafe(48); c.execute('INSERT INTO sesiones(token_hash,usuario_id,creado_at,expira_at,revocada) VALUES(?,?,?,?,0)',(token_hash(raw),user_id,now(),dtplus(SESSION_HOURS))); c.commit(); return raw

def current_user(handler):
    raw=handler.headers.get('Cookie','')
    jar=cookies.SimpleCookie(); jar.load(raw)
    morsel=jar.get('lle_session')
    if not morsel: return None
    c=conn(); row=c.execute('SELECT u.* FROM sesiones s JOIN usuarios u ON u.id=s.usuario_id WHERE s.token_hash=? AND s.revocada=0 AND s.expira_at>? AND u.activo=1',(token_hash(morsel.value),now())).fetchone(); c.close(); return row

def require(handler, roles=None):
    u=current_user(handler)
    if not u: handler.sendj({'ok':False,'error':'Autenticación requerida.'},401); return None
    if roles and u['rol'] not in roles: handler.sendj({'ok':False,'error':'No tiene permisos para esta operación.'},403); return None
    if u['debe_cambiar'] and urlparse(handler.path).path not in ('/api/me','/api/cambiar-password','/api/logout'): handler.sendj({'ok':False,'error':'Debe cambiar la contraseña inicial antes de continuar.'},403); return None
    return u

def json_load(v, default):
    if isinstance(v,(dict,list)): return v
    try: return json.loads(v) if v else default
    except Exception: return default

def validate_fact_id(c, expediente_id, hecho_id):
    if not hecho_id:
        return
    row=c.execute('SELECT payload_json FROM expedientes WHERE id=?',(expediente_id,)).fetchone()
    if not row:
        raise ValueError('Expediente no encontrado para validar el hecho relacionado.')
    p=json_load(row['payload_json'],{})
    facts=p.get('facts',[]) if isinstance(p,dict) else []
    valid={f'H-{i+1:03d}' for i,x in enumerate(facts) if isinstance(x,dict) and any(str(v or '').strip() for v in x.values())}
    # Compatibilidad con el identificador histórico utilizado por V5.5.1.
    valid |= {f'HECHO-{i+1:03d}' for i,x in enumerate(facts) if isinstance(x,dict) and any(str(v or '').strip() for v in x.values())}
    if hecho_id not in valid:
        raise ValueError('El hecho relacionado no existe en el Acta de este expediente.')

def load_expediente(code,user):
    c=conn(); row=c.execute('SELECT * FROM expedientes WHERE codigo=?',(code,)).fetchone()
    if not row:
        c.close(); raise ValueError('Expediente no encontrado.')
    if user['rol']=='TECNICO':
        pr=c.execute('SELECT nombre FROM personal WHERE id=?',(user['personal_id'],)).fetchone()
        pname=pr['nombre'] if pr else ''
        pdata=json_load(row['payload_json'],{})
        creador_campo=(pdata.get('registrado_por_tecnico') or '').strip()
        if row['tecnico']!=pname and creador_campo!=user['username']:
            c.close(); raise PermissionError('No tiene acceso a este expediente.')
    p=json_load(row['payload_json'],{})
    p['codigo']=row['codigo']; p['status']=row['status']
    p['tipo']=(row['tipo'] or p.get('tipo') or '').strip()
    if p['tipo']:
        p['materia_principal']=p['tipo']; p.update(document_codes(row['codigo'],p['tipo']))
    p=hydrate_payload(p,c,row['id'])
    photos,gps=evidence_summary(c,row['id'])
    p['photos']=photos; p['gps_points']=gps
    c.close(); return p

def next_code(c,prefix='AMB-LLE'):
    year=datetime.datetime.now().year
    c.execute('BEGIN IMMEDIATE')
    row=c.execute("SELECT codigo FROM expedientes WHERE codigo LIKE ? ORDER BY id DESC LIMIT 1",(f'{prefix}-{year}-%',)).fetchone(); n=1
    if row:
        try:n=int(row['codigo'].split('-')[-1])+1
        except Exception:n=1
    while c.execute('SELECT 1 FROM expedientes WHERE codigo=?',(f'{prefix}-{year}-{n:04d}',)).fetchone():n+=1
    return f'{prefix}-{year}-{n:04d}'

def validate_personnel(o,c,row=None):
    responsible=(o.get('tecnico_responsable') or o.get('tec') or o.get('tecnico') or '').strip()
    if not responsible: raise ValueError('Debe seleccionar el Técnico Ambiental Distrital responsable.')
    existing=(row['tecnico'] if row else None); r=c.execute('SELECT id,activo FROM personal WHERE nombre=?',(responsible,)).fetchone()
    if not r: raise ValueError('El técnico responsable no está registrado en el personal institucional.')
    if not r['activo'] and responsible != existing: raise ValueError('El técnico responsable seleccionado está inactivo para nuevas actuaciones.')
    names=o.get('tecnicos_participantes') or o.get('tecnicos_participantes_nombres') or []
    if isinstance(names,str): names=[x.strip() for x in names.split(',') if x.strip()]
    existing_participants=set()
    if row:
        existing_participants={r['nombre'] for r in c.execute(
            'SELECT p.nombre FROM participantes_inspeccion pi JOIN personal p ON p.id=pi.personal_id WHERE pi.expediente_id=?',(row['id'],)
        ).fetchall()}
    for name in names:
        if name==responsible: continue
        pr=c.execute('SELECT id,activo FROM personal WHERE nombre=?',(name,)).fetchone()
        if not pr: raise ValueError('Técnico participante no registrado: '+name)
        # Un participante inactivo no puede incorporarse a una actuación nueva,
        # pero sí debe conservarse al editar una actuación histórica en la que
        # ya estaba registrado antes de quedar inactivo.
        if not pr['activo'] and name not in existing_participants:
            raise ValueError('El técnico participante está inactivo para nuevas actuaciones: '+name)
    return responsible

def sync_participants(o,c,eid):
    names=o.get('tecnicos_participantes') or o.get('tecnicos_participantes_nombres') or []
    if isinstance(names,str): names=[x.strip() for x in names.split(',') if x.strip()]
    responsible=o.get('tecnico_responsable') or o.get('tec') or o.get('tecnico') or ''
    c.execute('DELETE FROM participantes_inspeccion WHERE expediente_id=?',(eid,))
    for name in [n for n in names if n and n!=responsible]:
        row=c.execute('SELECT id FROM personal WHERE nombre=?',(name,)).fetchone()
        if row:c.execute('INSERT OR IGNORE INTO participantes_inspeccion(expediente_id,personal_id,rol) VALUES(?,?,?)',(eid,row['id'],'PARTICIPANTE'))

def hydrate_payload(o,c,eid):
    rows=c.execute('SELECT p.nombre FROM participantes_inspeccion pi JOIN personal p ON p.id=pi.personal_id WHERE pi.expediente_id=? ORDER BY pi.id',(eid,)).fetchall(); o['tecnicos_participantes']=[r['nombre'] for r in rows]; return o

def document_codes(code, tipo=None):
    parts=(code or '').split('-')
    year=parts[2] if len(parts)>2 and parts[2].isdigit() else str(datetime.datetime.now().year)
    corr=parts[3] if len(parts)>3 and parts[3].isdigit() else '0001'
    comp=(tipo or 'OI').strip() or 'OI'
    return {
        'codigo_acta': f'ACTA-{comp}-{year}-{corr}',
        'codigo_informe': f'INF-{comp}-{year}-{corr}'
    }

def upsert(o,c,user,finalize=False):
    t=now()
    # Catálogos maestros: los valores se validan en servidor para que PC, LAN y futuras
    # interfaces móviles no puedan introducir variantes textuales incompatibles.
    tipo_actuacion=(o.get('acta_tipo_actuacion') or o.get('tipo_actuacion') or 'Inspección').strip()
    modalidad=(o.get('modalidad_inspeccion') or 'INDIVIDUAL').strip()
    if tipo_actuacion not in ACTION_TYPES: raise ValueError('Tipo de actuación no válido.')
    if modalidad not in INSPECTION_MODALITIES: raise ValueError('Modalidad de inspección no válida.')
    o['acta_tipo_actuacion']=tipo_actuacion
    o['tipo_actuacion']=tipo_actuacion
    o['modalidad_inspeccion']=modalidad
    # Catálogo maestro: un componente principal determina la plantilla del Acta/Informe.
    allowed_types=ALLOWED_COMPONENTS
    if (o.get('tipo') or '').strip() not in allowed_types:
        raise ValueError('Componente ambiental principal no válido. Seleccione un componente ambiental del catálogo institucional.')
    additional=o.get('materias_adicionales') or []
    if isinstance(additional,str): additional=[x.strip() for x in additional.split(',') if x.strip()]
    if not isinstance(additional,list) or any(x not in allowed_types for x in additional):
        raise ValueError('Componentes ambientales relacionados no válidos.')
    o['materia_principal']=o.get('tipo')
    o['materias_adicionales']=list(dict.fromkeys([x for x in additional if x != o.get('tipo')]))
    o['materias']=list(dict.fromkeys([o.get('tipo')]+o['materias_adicionales']))
    o['acta_schema_version']='V5.5.1-MAESTRO-1'
    # El cliente nunca determina el estado. El servidor controla toda transición.
    o.pop('status', None); o.pop('_actor', None)
    code=o.get('codigo')
    if not code: code=next_code(c); o['codigo']=code
    row=c.execute('SELECT * FROM expedientes WHERE codigo=?',(code,)).fetchone()
    if row:
        # Fuente única: el componente/origen/distrito se fijan en la recepción y no pueden cambiar en el módulo técnico.
        source=json_load(row['payload_json'],{})
        source_type=(row['tipo'] or source.get('tipo') or '').strip()
        source_origin=(row['origen'] or source.get('origen') or '').strip()
        source_district=(row['distrito'] or source.get('distrito') or '').strip()
        source_action=(source.get('tipo_actuacion') or source.get('acta_tipo_actuacion') or 'Inspección').strip()
        source_modality=(source.get('modalidad_inspeccion') or 'INDIVIDUAL').strip()
        if not source_type: raise ValueError('El expediente no tiene componente ambiental principal registrado en la recepción.')
        if (o.get('tipo') or '').strip()!=source_type: raise ValueError(f'El componente ambiental no coincide con el registrado en la recepción: {source_type}.')
        if (o.get('origen') or '').strip()!=source_origin: raise ValueError(f'El origen no coincide con el registrado en la recepción: {source_origin}.')
        if (o.get('distrito') or '').strip()!=source_district: raise ValueError(f'El distrito de la actuación no coincide con el registrado en la recepción: {source_district}.')
        if tipo_actuacion!=source_action: raise ValueError(f'El tipo de actuación no coincide con el registrado en la recepción: {source_action}.')
        if modalidad!=source_modality: raise ValueError(f'La modalidad de inspección no coincide con la registrada en la recepción: {source_modality}.')
        o['tipo']=source_type; o['materia_principal']=source_type
        o['materias_adicionales']=[]
        o['materias']=[source_type]
        o['origen']=source_origin; o['distrito']=source_district
        o['acta_tipo_actuacion']=source_action; o['tipo_actuacion']=source_action
        o['modalidad_inspeccion']=source_modality
    if o.get('distrito') not in DISTRICTS: raise ValueError('Distrito de la actuación no válido.')
    o.update(document_codes(code, o.get('tipo')))
    responsible=validate_personnel(o,c,row)
    if user['rol']!='TECNICO': raise PermissionError('Solo el Técnico Ambiental Distrital puede crear o editar expedientes técnicos.')
    if row:
        current=row['status']
        created_from_acta = bool(json_load(row['payload_json'],{}).get('registrado_por_tecnico'))
        if current not in ('ASIGNADO_A_INSPECCION','BORRADOR','DEVUELTO','RECIBIDO_PENDIENTE_ASIGNACION'): raise PermissionError('El expediente está bloqueado para edición en su estado actual.')
        if current=='RECIBIDO_PENDIENTE_ASIGNACION' and not created_from_acta:
            raise PermissionError('La actuación está pendiente de asignación y no puede ser editada desde el módulo técnico.')
        if row['tecnico'] != responsible and not (current=='RECIBIDO_PENDIENTE_ASIGNACION' and created_from_acta and json_load(row['payload_json'],{}).get('registrado_por_tecnico')==user.get('username')):
            raise PermissionError('Solo el técnico responsable o el técnico que registró esta actuación en campo puede modificar este borrador técnico.')
        if current=='RECIBIDO_PENDIENTE_ASIGNACION' and created_from_acta:
            # Se permite guardar el borrador del Acta por el Técnico que registró la actuación en campo,
            # pero el caso permanece pendiente de revisión/asignación y NO puede finalizarse ni enviarse a revisión todavía.
            if finalize:
                raise PermissionError('La actuación registrada desde el Acta debe ser revisada y asignada por el Gerente Ambiental antes de finalizar el Informe Técnico.')
            newstatus='RECIBIDO_PENDIENTE_ASIGNACION'
            responsible = responsible or row['tecnico']
        old=json_load(row['payload_json'],{})
        if current=='DEVUELTO':
            scope=json_load(old.get('_correction_scope','[]'),[])
            if not scope: raise PermissionError('La devolución no tiene campos autorizados de corrección registrados.')
            ignored={'status','_actor','_finalize','_correction_scope','history','photos','gps_points','fotografias','puntos_gps'}
            # Algunos campos derivados del servidor pueden no venir en el POST del formulario
            # aunque sigan existiendo en el expediente. Su ausencia no constituye una modificación.
            # Si el cliente sí envía tecnicos_participantes, entonces se compara normalmente para
            # impedir agregar/quitar participantes fuera del alcance autorizado.
            changed={k for k in set(old)|set(o) if k not in ignored and not k.startswith('_')
                     and not (k=='tecnicos_participantes' and k not in o)
                     and old.get(k)!=o.get(k)}
            if not changed.issubset(set(scope)): raise PermissionError('La devolución limita la edición. Campos no autorizados: '+', '.join(sorted(changed-set(scope))))
            o['_correction_scope']=scope
        if old.get('history') and not o.get('history'):o['history']=old['history']
        if old.get('_correction_scope') and not o.get('_correction_scope'):o['_correction_scope']=old['_correction_scope']
        if current!='RECIBIDO_PENDIENTE_ASIGNACION':
            newstatus='INFORME_FINALIZADO_PENDIENTE_VB' if finalize else ('BORRADOR' if current=='ASIGNADO_A_INSPECCION' else current)
        # Fuente única de verdad: estado de servidor y payload siempre sincronizados.
        o['status']=newstatus
        if finalize:o.pop('_correction_scope',None)
        ver=c.execute('SELECT COALESCE(MAX(version),0)+1 v FROM versiones WHERE expediente_id=?',(row['id'],)).fetchone()['v']
        db_tecnico = row['tecnico'] if current=='RECIBIDO_PENDIENTE_ASIGNACION' else responsible
        c.execute('UPDATE expedientes SET referencia=?,anio=?,tipo=?,origen=?,distrito=?,tecnico=?,status=?,payload_json=?,updated_at=? WHERE id=?',(o.get('referencia') or o.get('referencia_expediente'),int(o.get('anio') or t[:4]),o.get('tipo'),o.get('origen'),o.get('distrito'),db_tecnico,newstatus,json.dumps(o,ensure_ascii=False),t,row['id'])); eid=row['id']
    else:
        if user['rol']=='TECNICO': raise PermissionError('El expediente debe existir como actuación recibida y asignada por el Gerente antes de iniciar la actuación técnica.')
        status='INFORME_FINALIZADO_PENDIENTE_VB' if finalize else 'BORRADOR'; o['status']=status; ver=1
        c.execute('INSERT INTO expedientes(codigo,referencia,anio,tipo,origen,distrito,tecnico,status,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(code,o.get('referencia') or o.get('referencia_expediente'),int(o.get('anio') or t[:4]),o.get('tipo'),o.get('origen'),o.get('distrito'),responsible,status,json.dumps(o,ensure_ascii=False),t,t)); eid=c.execute('SELECT last_insert_rowid()').fetchone()[0]
    sync_participants(o,c,eid)
    c.execute('DELETE FROM evidencias WHERE expediente_id=?',(eid,))
    for e in o.get('evidence',[]) or []:
        try:lat=float(e['lat']) if e.get('lat') not in (None,'') else None
        except:lat=None
        try:lng=float(e['lng']) if e.get('lng') not in (None,'') else None
        except:lng=None
        try:acc=float(e['accuracy']) if e.get('accuracy') not in (None,'') else None
        except:acc=None
        c.execute('INSERT INTO evidencias(expediente_id,codigo,tipo,lat,lng,precision_m,descripcion,fecha) VALUES(?,?,?,?,?,?,?,?)',(eid,e.get('id'),e.get('type'),lat,lng,acc,e.get('description'),e.get('time')))
    o=hydrate_payload(o,c,eid)
    # Reforzar la fuente única de verdad después de hidratar participantes/evidencias.
    o['status'] = status if not row else newstatus
    c.execute('UPDATE expedientes SET status=?,payload_json=?,updated_at=? WHERE id=?',(o['status'],json.dumps(o,ensure_ascii=False),now(),eid))
    c.execute('INSERT INTO versiones(expediente_id,version,estado,payload_json,creado_por,creado_at) VALUES(?,?,?,?,?,?)',(eid,ver,o['status'],json.dumps(o,ensure_ascii=False),user['username'],t))
    if finalize:
        c.execute('INSERT INTO historial(expediente_id,accion,usuario,observacion,fecha) VALUES(?,?,?,?,?)',(eid,'INFORME FINALIZADO Y ENVIADO A SEGUIMIENTO',user['username'],'',t))
        notify(c,'gerente','INFORME_RECIBIDO','Nuevo informe técnico recibido para revisión',f"{code} · {o.get('tipo','')} · Distrito: {o.get('distrito','No indicado')}",code,'REVISAR_INFORME')
        for admin in admin_usernames(c):
            notify(c,admin,'INFORME_RECIBIDO','Nuevo informe técnico recibido',f"{code} · {o.get('tipo','')}",code,'REVISAR_INFORME')
    return eid,ver,o.get('status')


def notify(c, usuario, tipo, titulo, mensaje, expediente_codigo=None, accion=None):
    if not usuario: return
    c.execute('INSERT INTO notificaciones(usuario,expediente_codigo,tipo,titulo,mensaje,fecha,leida,accion) VALUES(?,?,?,?,?,?,0,?)',
              (usuario, expediente_codigo, tipo, titulo, mensaje, now(), accion))

def tecnico_username_for_name(c, nombre):
    if not nombre: return None
    r=c.execute("SELECT u.username FROM usuarios u JOIN personal p ON p.id=u.personal_id WHERE p.nombre=? AND u.rol='TECNICO' AND u.activo=1",(nombre,)).fetchone()
    return r['username'] if r else None

def admin_usernames(c):
    return [r['username'] for r in c.execute("SELECT username FROM usuarios WHERE rol='ADMIN' AND activo=1").fetchall()]

def create_reception(o,user):
    if user['rol'] not in ('GERENTE','ADMIN'):
        raise PermissionError('Solo el Gerente Ambiental o Administrador puede registrar la recepción de una actuación.')
    origen=(o.get('origen') or '').strip()
    fecha=(o.get('fecha_recepcion') or '').strip()
    tipo=(o.get('tipo') or '').strip()
    distrito=(o.get('distrito') or '').strip()
    tipo_actuacion=(o.get('tipo_actuacion') or 'Inspección').strip()
    modalidad=(o.get('modalidad_inspeccion') or 'INDIVIDUAL').strip()
    allowed_types=ALLOWED_COMPONENTS
    if not origen or not fecha or not tipo: raise ValueError('Origen, componente ambiental principal y fecha de recepción son obligatorios.')
    if origen not in ORIGINS: raise ValueError('Origen de actuación no válido.')
    if tipo not in allowed_types: raise ValueError('Componente ambiental principal no válido.')
    if distrito and distrito not in DISTRICTS: raise ValueError('Distrito de la actuación no válido.')
    if tipo_actuacion not in ACTION_TYPES: raise ValueError('Tipo de actuación no válido.')
    if modalidad not in INSPECTION_MODALITIES: raise ValueError('Modalidad de inspección no válida.')
    additional=[]
    if origen=='Denuncia ambiental' and not (o.get('solicitante') or '').strip() and not (o.get('descripcion_inicial') or '').strip():
        raise ValueError('En una denuncia debe registrarse al menos el denunciante o una descripción inicial.')
    c=conn(); t=now()
    try:
        c.execute('BEGIN IMMEDIATE')
        year=int(fecha[:4]) if re.match(r'^\d{4}-',fecha) else datetime.datetime.now().year
        prefix=f'AMB-LLE-{year}'
        row=c.execute("SELECT codigo FROM expedientes WHERE codigo LIKE ? ORDER BY id DESC LIMIT 1",(prefix+'-%',)).fetchone()
        n=1
        if row:
            try:n=int(row['codigo'].rsplit('-',1)[1])+1
            except:pass
        while c.execute('SELECT 1 FROM expedientes WHERE codigo=?',(f'{prefix}-{n:04d}',)).fetchone(): n+=1
        code=f'{prefix}-{n:04d}'
        payload={
            'codigo':code,'anio':year,'status':'RECIBIDO_PENDIENTE_ASIGNACION',
            'tipo':tipo,'materia_principal':tipo,'materias_adicionales':[],'materias':[tipo],
            'origen':origen,'fecha_recepcion':fecha,'distrito':distrito,'tipo_actuacion':tipo_actuacion,'modalidad_inspeccion':modalidad,'referencia_externa':(o.get('referencia_externa') or '').strip(),
            'institucion_solicitante':(o.get('institucion_solicitante') or '').strip(),'solicitante':(o.get('solicitante') or '').strip(),
            'condicion':(o.get('condicion') or '').strip(),'contacto_solicitante':(o.get('contacto') or '').strip(),
            'descripcion_inicial':(o.get('descripcion_inicial') or '').strip(),'prioridad':(o.get('prioridad') or 'Media').strip(),
            'recepcion':{'recibido_por':user['username'],'recibido_at':t}
        }
        c.execute('INSERT INTO expedientes(codigo,referencia,anio,tipo,origen,distrito,tecnico,status,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                  (code,payload['referencia_externa'],year,tipo,origen,payload['distrito'] or None,None,'RECIBIDO_PENDIENTE_ASIGNACION',json.dumps(payload,ensure_ascii=False),t,t))
        eid=c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute('INSERT INTO recepciones(expediente_id,fecha_recepcion,origen,referencia_externa,institucion_solicitante,solicitante,condicion,contacto,descripcion_inicial,prioridad,recibido_por,recibido_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                  (eid,fecha,origen,payload['referencia_externa'],payload['institucion_solicitante'],payload['solicitante'],payload['condicion'],payload['contacto_solicitante'],payload['descripcion_inicial'],payload['prioridad'],user['username'],t))
        c.execute('INSERT INTO historial(expediente_id,accion,usuario,observacion,fecha) VALUES(?,?,?,?,?)',(eid,'ACTUACIÓN RECIBIDA',''+user['username'],payload['descripcion_inicial'],t))
        if user['rol']!='GERENTE':
            notify(c,'gerente','NUEVA_ACTUACION','Nueva actuación recibida',f"{code} · {tipo} · {origen} · Distrito: {payload['distrito'] or 'No indicado'}",code,'REVISAR_RECEPCION')
        for admin in admin_usernames(c):
            notify(c,admin,'NUEVA_ACTUACION','Nueva actuación registrada',f"{code} · {tipo} · {origen}",code,'REVISAR_RECEPCION')
        c.execute('INSERT INTO versiones(expediente_id,version,estado,payload_json,creado_por,creado_at) VALUES(?,?,?,?,?,?)',(eid,1,'RECIBIDO_PENDIENTE_ASIGNACION',json.dumps(payload,ensure_ascii=False),user['username'],t))
        c.commit(); return code
    finally:c.close()



def create_reception_from_technician(o,user):
    """Registra una nueva denuncia/solicitud detectada por el Técnico desde el Acta,
    sin otorgarle facultad de asignación. La actuación queda en cola del Gerente.
    """
    if user['rol']!='TECNICO':
        raise PermissionError('Esta operación está disponible únicamente para el Técnico Ambiental Distrital.')
    operation_id=sync_operation_id(o)
    if operation_id:
        c0=conn()
        try:
            replay=replay_sync_operation(c0,operation_id)
            if replay is not None:return replay
        finally:c0.close()
    origen=(o.get('origen') or '').strip()
    fecha=(o.get('fecha_recepcion') or '').strip()
    tipo=(o.get('tipo') or '').strip()
    distrito=(o.get('distrito') or '').strip()
    if not origen or not fecha or not tipo or not distrito:
        raise ValueError('Origen, fecha, componente ambiental y distrito son obligatorios.')
    if origen not in ORIGINS:
        raise ValueError('Origen de actuación no válido.')
    if tipo not in ALLOWED_COMPONENTS:
        raise ValueError('Componente ambiental principal no válido.')
    if distrito not in DISTRICTS:
        raise ValueError('Distrito de la actuación no válido.')
    additional=[]
    descripcion=(o.get('descripcion_inicial') or '').strip()
    solicitante=(o.get('solicitante') or '').strip()
    if not descripcion and not solicitante:
        raise ValueError('Debe registrar al menos el denunciante/solicitante o una descripción inicial.')
    c=conn(); t=now()
    try:
        c.execute('BEGIN IMMEDIATE')
        year=int(fecha[:4]) if re.match(r'^\d{4}-',fecha) else datetime.datetime.now().year
        prefix=f'AMB-LLE-{year}'
        row=c.execute("SELECT codigo FROM expedientes WHERE codigo LIKE ? ORDER BY id DESC LIMIT 1",(prefix+'-%',)).fetchone()
        n=1
        if row:
            try:n=int(row['codigo'].rsplit('-',1)[1])+1
            except:pass
        while c.execute('SELECT 1 FROM expedientes WHERE codigo=?',(f'{prefix}-{n:04d}',)).fetchone(): n+=1
        code=f'{prefix}-{n:04d}'
        payload={
            'codigo':code,'anio':year,'status':'RECIBIDO_PENDIENTE_ASIGNACION',
            'tipo':tipo,'materia_principal':tipo,'materias_adicionales':[],'materias':[tipo],
            'origen':origen,'fecha_recepcion':fecha,'distrito':distrito,
            'referencia_externa':(o.get('referencia_externa') or '').strip(),
            'institucion_solicitante':(o.get('institucion_solicitante') or '').strip(),
            'solicitante':solicitante,'condicion':(o.get('condicion') or '').strip(),
            'contacto_solicitante':(o.get('contacto') or '').strip(),
            'descripcion_inicial':descripcion,'prioridad':(o.get('prioridad') or 'Media').strip(),
            'origen_registro':'REGISTRO DESDE ACTA POR TÉCNICO','registrado_por_tecnico':user['username'],
            'recepcion':{'recibido_por':user['username'],'recibido_at':t,'modalidad':'Registro inicial desde Acta; pendiente de revisión y asignación por Gerente Ambiental'}
        }
        c.execute('INSERT INTO expedientes(codigo,referencia,anio,tipo,origen,distrito,tecnico,status,payload_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                  (code,payload['referencia_externa'],year,tipo,origen,distrito,None,'RECIBIDO_PENDIENTE_ASIGNACION',json.dumps(payload,ensure_ascii=False),t,t))
        eid=c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute('INSERT INTO recepciones(expediente_id,fecha_recepcion,origen,referencia_externa,institucion_solicitante,solicitante,condicion,contacto,descripcion_inicial,prioridad,recibido_por,recibido_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                  (eid,fecha,origen,payload['referencia_externa'],payload['institucion_solicitante'],solicitante,payload['condicion'],payload['contacto_solicitante'],descripcion,payload['prioridad'],user['username'],t))
        c.execute('INSERT INTO historial(expediente_id,accion,usuario,observacion,fecha) VALUES(?,?,?,?,?)',(eid,'ACTUACIÓN RECIBIDA DESDE ACTA POR TÉCNICO',''+user['username'],descripcion,t))
        notify(c,'gerente','NUEVA_ACTUACION_TECNICO','Nueva actuación registrada por Técnico',f"{code} · {tipo} · pendiente de revisión y asignación",code,'REVISAR_RECEPCION')
        for admin in admin_usernames(c):
            notify(c,admin,'NUEVA_ACTUACION_TECNICO','Nueva actuación registrada por Técnico',f"{code} · {tipo}",code,'REVISAR_RECEPCION')
        c.execute('INSERT INTO versiones(expediente_id,version,estado,payload_json,creado_por,creado_at) VALUES(?,?,?,?,?,?)',(eid,1,'RECIBIDO_PENDIENTE_ASIGNACION',json.dumps(payload,ensure_ascii=False),user['username'],t))
        response={'ok':True,'codigo':code}
        remember_sync_operation(c,operation_id,'reception',response)
        c.commit(); return response
    finally:c.close()

def assign_reception(o,user):
    if user['rol']!='GERENTE': raise PermissionError('Solo el Gerente Ambiental puede asignar actuaciones a técnicos.')
    code=(o.get('codigo') or '').strip(); tecnico=(o.get('tecnico') or '').strip()
    if not code or not tecnico: raise ValueError('Expediente y técnico son obligatorios.')
    c=conn()
    try:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT * FROM expedientes WHERE codigo=?',(code,)).fetchone()
        if not row: raise ValueError('Expediente no encontrado.')
        if row['status']!='RECIBIDO_PENDIENTE_ASIGNACION': raise PermissionError('Solo pueden asignarse actuaciones pendientes de asignación.')
        pr=c.execute('SELECT id,activo FROM personal WHERE nombre=?',(tecnico,)).fetchone()
        if not pr or not pr['activo']: raise PermissionError('El técnico seleccionado no está activo y no puede recibir nuevas actuaciones.')
        t=now(); obs=(o.get('observacion') or '').strip(); data=json_load(row['payload_json'],{})
        data['tipo']=(row['tipo'] or data.get('tipo') or '').strip()
        if not data['tipo']:
            raise ValueError('El expediente no tiene componente ambiental principal registrado en la recepción.')
        data['materia_principal']=data['tipo']
        data['materias_adicionales']=[]
        data['materias']=[data['tipo']] if data.get('tipo') else []
        data.update(document_codes(code, data['tipo']))
        data['tecnico_responsable']=tecnico; data['tecnico_asignado']=tecnico; data['asignacion']={'tecnico':tecnico,'gerente':user['username'],'fecha':t,'observacion':obs}
        data['status']='ASIGNADO_A_INSPECCION'
        c.execute('UPDATE expedientes SET tecnico=?,status=?,payload_json=?,updated_at=? WHERE id=?',(tecnico,'ASIGNADO_A_INSPECCION',json.dumps(data,ensure_ascii=False),t,row['id']))
        c.execute('UPDATE asignaciones SET activa=0 WHERE expediente_id=?',(row['id'],))
        c.execute('INSERT INTO asignaciones(expediente_id,tecnico,gerente_usuario,fecha_asignacion,observacion,activa) VALUES(?,?,?,?,?,1)',(row['id'],tecnico,user['username'],t,obs))
        c.execute('INSERT INTO historial(expediente_id,accion,usuario,observacion,fecha) VALUES(?,?,?,?,?)',(row['id'],'ACTUACIÓN ASIGNADA A TÉCNICO AMBIENTAL DISTRITAL',user['username'],f'Técnico asignado: {tecnico}. {obs}'.strip(),t))
        tuser=tecnico_username_for_name(c,tecnico)
        notify(c,tuser,'ACTUACION_ASIGNADA','Nueva actuación asignada',f"{code} · {tipo if (tipo:=data.get('tipo')) else ''} · Distrito: {data.get('distrito') or 'No indicado'}",code,'ABRIR_ACTUACION')
        ver=c.execute('SELECT COALESCE(MAX(version),0)+1 v FROM versiones WHERE expediente_id=?',(row['id'],)).fetchone()['v']; c.execute('INSERT INTO versiones(expediente_id,version,estado,payload_json,creado_por,creado_at) VALUES(?,?,?,?,?,?)',(row['id'],ver,'ASIGNADO_A_INSPECCION',json.dumps(data,ensure_ascii=False),user['username'],t)); c.commit(); return data
    finally:c.close()

def assignment_history(code,user):
    c=conn(); row=c.execute('SELECT id FROM expedientes WHERE codigo=?',(code,)).fetchone()
    if not row: c.close(); raise ValueError('Expediente no encontrado.')
    if user['rol']=='TECNICO':
        pr=c.execute('SELECT nombre FROM personal WHERE id=?',(user['personal_id'],)).fetchone()
        if not pr: c.close(); raise PermissionError('Usuario técnico sin personal asociado.')
        ok=c.execute('SELECT 1 FROM expedientes WHERE id=? AND tecnico=?',(row['id'],pr['nombre'])).fetchone()
        if not ok: c.close(); raise PermissionError('No tiene acceso a este expediente.')
    rows=[dict(r) for r in c.execute('SELECT tecnico,gerente_usuario,fecha_asignacion,observacion,activa FROM asignaciones WHERE expediente_id=? ORDER BY id',(row['id'],)).fetchall()]; c.close(); return rows

def all_exps(user):
    c=conn()
    if user['rol']=='TECNICO':
        pr=c.execute('SELECT nombre FROM personal WHERE id=?',(user['personal_id'],)).fetchone()
        pname=pr['nombre'] if pr else ''
        rows=c.execute("SELECT id,codigo,payload_json FROM expedientes WHERE tecnico=? OR json_extract(payload_json,'$.registrado_por_tecnico')=? ORDER BY id DESC",(pname,user['username'])).fetchall()
    else:
        rows=c.execute('SELECT id,codigo,payload_json FROM expedientes ORDER BY id DESC').fetchall()
    out=[]
    for r in rows:
        item=hydrate_payload(json_load(r['payload_json'],{}),c,r['id'])
        item['codigo']=r['codigo']
        if item.get('tipo'):
            item.update(document_codes(r['codigo'], item.get('tipo')))
        out.append(item)
    c.close(); return out

def notifications_for(user):
    c=conn(); rows=[dict(r) for r in c.execute('SELECT id,expediente_codigo,tipo,titulo,mensaje,fecha,leida,accion FROM notificaciones WHERE usuario=? ORDER BY id DESC LIMIT 100',(user['username'],)).fetchall()]; c.close(); return rows

def mark_notification(o,user):
    nid=int(o.get('id')); c=conn(); c.execute('UPDATE notificaciones SET leida=1 WHERE id=? AND usuario=?',(nid,user['username'])); c.commit(); c.close(); return True

def personnel(active_only=False):
    c=conn(); q='SELECT id,nombre,cargo,activo FROM personal'+(' WHERE activo=1' if active_only else '')+' ORDER BY nombre'; rows=[dict(r) for r in c.execute(q).fetchall()]; c.close(); return rows

def revision(o,user):
    code=o.get('codigo'); action=o.get('action'); obs=o.get('obs','').strip()
    if user['rol'] not in ('GERENTE','ADMIN'): raise PermissionError('Solo Gerente Ambiental o Administrador puede revisar expedientes.')
    if action not in ('VALIDAR','DEVOLVER'): raise ValueError('Acción de revisión no válida.')
    if action=='DEVOLVER' and not obs: raise ValueError('La devolución requiere observaciones.')
    c=conn(); row=c.execute('SELECT * FROM expedientes WHERE codigo=?',(code,)).fetchone()
    if not row: c.close(); raise ValueError('Expediente no encontrado.')
    if row['status']!='INFORME_FINALIZADO_PENDIENTE_VB': c.close(); raise PermissionError('Solo pueden revisarse expedientes enviados a seguimiento.')
    p=json_load(row['payload_json'],{}); hist=p.get('history',[]) if isinstance(p.get('history',[]),list) else []
    if action=='DEVOLVER':
        scope=o.get('scope') or []
        if not isinstance(scope,list): raise ValueError('El alcance de corrección debe ser una lista.')
        scope=[str(x).strip() for x in scope if str(x).strip()]
        if not scope: c.close(); raise ValueError('Debe seleccionar al menos un campo o sección para corregir.')
        invalid=sorted(set(scope)-CORRECTION_SCOPE_KEYS)
        if invalid: c.close(); raise ValueError('El alcance de corrección contiene campos no autorizados: '+', '.join(invalid))
        scope=list(dict.fromkeys(scope))
        p['_correction_scope']=scope; p['status']='DEVUELTO'; h={'action':'DEVUELTO CON OBSERVACIONES','date':now(),'user':user['username'],'obs':obs,'documento':o.get('documento',''),'seccion':o.get('seccion',''),'correccion_requerida':obs,'scope':scope}; newstatus='DEVUELTO'
    else:p['status']='VB_APROBADO';p.pop('_correction_scope',None);h={'action':'VALIDACIÓN INSTITUCIONAL APROBADA','date':now(),'user':user['username'],'obs':obs};newstatus='VB_APROBADO'
    hist.append(h);p['history']=hist
    # El estado enviado por el cliente nunca se acepta como autoridad; se fija en servidor.
    p['status']=newstatus
    t=now();c.execute('UPDATE expedientes SET status=?,payload_json=?,updated_at=? WHERE id=?',(newstatus,json.dumps(p,ensure_ascii=False),t,row['id']))
    c.execute('INSERT INTO historial(expediente_id,accion,usuario,observacion,documento,seccion,correccion_requerida,fecha) VALUES(?,?,?,?,?,?,?,?)',(row['id'],h['action'],user['username'],obs,o.get('documento'),o.get('seccion'),obs if action=='DEVOLVER' else None,t))
    tuser=tecnico_username_for_name(c, p.get('tecnico_responsable') or p.get('tecnico_asignado') or row['tecnico'])
    if action=='DEVOLVER':
        notify(c,tuser,'INFORME_DEVUELTO','Informe devuelto para corrección',f"{code} · Corrección: {obs}",code,'CORREGIR_INFORME')
    else:
        notify(c,tuser,'INFORME_VALIDADO','Informe validado por Gerencia',f"{code} · Validación registrada por {user['username']}",code,'VER_EXPEDIENTE')
    ver=c.execute('SELECT COALESCE(MAX(version),0)+1 v FROM versiones WHERE expediente_id=?',(row['id'],)).fetchone()['v'];c.execute('INSERT INTO versiones(expediente_id,version,estado,payload_json,creado_por,creado_at) VALUES(?,?,?,?,?,?)',(row['id'],ver,newstatus,json.dumps(p,ensure_ascii=False),user['username'],t));c.commit();c.close();return p

def remit_case(o,user):
    if user['rol'] not in ('GERENTE','ADMIN'):
        raise PermissionError('Solo Gerente Ambiental o Administrador puede remitir expedientes.')
    code=(o.get('codigo') or '').strip()
    destino=(o.get('destino') or '').strip()
    motivo=(o.get('motivo') or '').strip()
    if not destino: raise ValueError('La institución o unidad destinataria es obligatoria para la remisión.')
    if not motivo: raise ValueError('El motivo de la remisión es obligatorio.')
    c=conn()
    try:
        row=c.execute('SELECT * FROM expedientes WHERE codigo=?',(code,)).fetchone()
        if not row: raise ValueError('Expediente no encontrado.')
        if row['status']!='VB_APROBADO': raise PermissionError('La remisión requiere validación institucional previa.')
        data=json_load(row['payload_json'],{})
        rem={
            'destino':destino, 'motivo':motivo, 'docs':(o.get('docs') or '').strip(),
            'date':now(), 'remitido_por':user['username']
        }
        data['status']='REMITIDO'; data['remision']=rem
        hist=data.get('history',[]) if isinstance(data.get('history',[]),list) else []
        hist.append({'action':'EXPEDIENTE REMITIDO','date':rem['date'],'user':user['username'],'obs':motivo,'destino':destino})
        data['history']=hist
        t=now()
        c.execute('UPDATE expedientes SET status=?,payload_json=?,updated_at=? WHERE id=?',('REMITIDO',json.dumps(data,ensure_ascii=False),t,row['id']))
        c.execute('INSERT INTO historial(expediente_id,accion,usuario,observacion,fecha) VALUES(?,?,?,?,?)',(row['id'],'EXPEDIENTE REMITIDO',user['username'],f'Destino: {destino}. {motivo}',t))
        tuser=tecnico_username_for_name(c, data.get('tecnico_responsable') or data.get('tecnico_asignado') or row['tecnico'])
        notify(c,tuser,'EXPEDIENTE_REMITIDO','Actuación remitida',f"{code} · Destino: {destino}",code,'VER_EXPEDIENTE')
        ver=c.execute('SELECT COALESCE(MAX(version),0)+1 v FROM versiones WHERE expediente_id=?',(row['id'],)).fetchone()['v']
        c.execute('INSERT INTO versiones(expediente_id,version,estado,payload_json,creado_por,creado_at) VALUES(?,?,?,?,?,?)',(row['id'],ver,'REMITIDO',json.dumps(data,ensure_ascii=False),user['username'],t))
        c.commit(); return data
    finally:c.close()

def close_case(o,user):
    if user['rol'] not in ('GERENTE','ADMIN'):
        raise PermissionError('Solo Gerente Ambiental o Administrador puede finalizar expedientes.')
    code=(o.get('codigo') or '').strip(); motivo=(o.get('motivo') or '').strip()
    if not motivo: raise ValueError('Debe indicar el resultado o motivo de cierre.')
    c=conn()
    try:
        row=c.execute('SELECT * FROM expedientes WHERE codigo=?',(code,)).fetchone()
        if not row: raise ValueError('Expediente no encontrado.')
        if row['status'] not in ('VB_APROBADO','REMITIDO'): raise PermissionError('El cierre requiere una validación institucional previa.')
        data=json_load(row['payload_json'],{}); data['status']='FINALIZADO'; data['cierre']={'fecha':now(),'usuario':user['username'],'motivo':motivo}
        hist=data.get('history',[]) if isinstance(data.get('history',[]),list) else []
        hist.append({'action':'EXPEDIENTE FINALIZADO','date':data['cierre']['fecha'],'user':user['username'],'obs':motivo})
        data['history']=hist; t=now()
        c.execute('UPDATE expedientes SET status=?,payload_json=?,updated_at=? WHERE id=?',('FINALIZADO',json.dumps(data,ensure_ascii=False),t,row['id']))
        c.execute('INSERT INTO historial(expediente_id,accion,usuario,observacion,fecha) VALUES(?,?,?,?,?)',(row['id'],'EXPEDIENTE FINALIZADO',user['username'],motivo,t))
        tuser=tecnico_username_for_name(c, data.get('tecnico_responsable') or data.get('tecnico_asignado') or row['tecnico'])
        notify(c,tuser,'EXPEDIENTE_FINALIZADO','Expediente finalizado',f"{code} · {motivo}",code,'VER_EXPEDIENTE')
        ver=c.execute('SELECT COALESCE(MAX(version),0)+1 v FROM versiones WHERE expediente_id=?',(row['id'],)).fetchone()['v']
        c.execute('INSERT INTO versiones(expediente_id,version,estado,payload_json,creado_por,creado_at) VALUES(?,?,?,?,?,?)',(row['id'],ver,'FINALIZADO',json.dumps(data,ensure_ascii=False),user['username'],t))
        c.commit(); return data
    finally:c.close()

def add_person(o):
    name=' '.join(str(o.get('nombre') or '').split())
    cargo=' '.join(str(o.get('cargo') or 'Técnico Ambiental Distrital').split())
    if not name: raise ValueError('El nombre del técnico es obligatorio.')
    if len(name)>150: raise ValueError('El nombre del técnico no puede superar 150 caracteres.')
    if not cargo: raise ValueError('El cargo del técnico es obligatorio.')
    if len(cargo)>150: raise ValueError('El cargo no puede superar 150 caracteres.')
    c=conn()
    try:
        dup=c.execute('SELECT id FROM personal WHERE LOWER(TRIM(nombre))=LOWER(TRIM(?))',(name,)).fetchone()
        if dup: raise ValueError('El técnico ya está registrado en el personal institucional.')
        t=now();c.execute('INSERT INTO personal(nombre,cargo,activo,creado_at,actualizado_at) VALUES(?,?,?,?,?)',(name,cargo,1,t,t));c.commit()
    finally:c.close()

def set_person_status(o):
    try: pid=int(o.get('id'))
    except Exception: raise ValueError('Identificador de personal no válido.')
    active=1 if o.get('activo') else 0
    c=conn()
    try:
        row=c.execute('SELECT id,nombre FROM personal WHERE id=?',(pid,)).fetchone()
        if not row: raise ValueError('El registro de personal no existe.')
        c.execute('UPDATE personal SET activo=?,actualizado_at=? WHERE id=?',(active,now(),pid));c.commit()
    finally:c.close()

def delete_draft(o,user):
    if user['rol']!='TECNICO':raise PermissionError('Solo el técnico responsable puede eliminar borradores.')
    code=o.get('codigo');c=conn()
    try:
        row=c.execute('SELECT id,status,tecnico FROM expedientes WHERE codigo=?',(code,)).fetchone()
        if not row:raise ValueError('Expediente no encontrado.')
        if row['status']!='BORRADOR':raise PermissionError('Solo se puede eliminar un expediente en estado BORRADOR.')
        if row['tecnico'] != user['personal_name']:raise PermissionError('Solo el técnico responsable puede eliminar este borrador.')
        eid=row['id']
        c.execute('INSERT INTO auditoria_eliminaciones(codigo,tecnico,usuario,fecha,motivo) VALUES(?,?,?,?,?)',(code,user['personal_name'],user['username'],now(),'Borrador eliminado por el Técnico Ambiental Distrital responsable.'))
        photo_paths=[r['archivo'] for r in c.execute('SELECT archivo FROM fotografias WHERE expediente_id=?',(eid,)).fetchall()]
        c.execute('DELETE FROM fotografias WHERE expediente_id=?',(eid,))
        c.execute('DELETE FROM puntos_gps WHERE expediente_id=?',(eid,))
        for table in ('participantes_inspeccion','evidencias','documentos','historial','versiones'):c.execute(f'DELETE FROM {table} WHERE expediente_id=?',(eid,))
        c.execute('DELETE FROM expedientes WHERE id=?',(eid,));c.commit()
        for rel in photo_paths:
            try:
                path=os.path.join(ROOT,rel)
                if os.path.isfile(path): os.remove(path)
            except Exception: pass
        # Elimina carpetas vacías del expediente, sin tocar otros expedientes.
        try:
            folder=os.path.join(MEDIA_ROOT,code)
            if os.path.isdir(folder) and not os.listdir(folder): os.rmdir(folder)
        except Exception: pass
        return True
    finally:c.close()


def get_exp_for_edit(code, user, allow_scope_key):
    c=conn(); row=c.execute('SELECT * FROM expedientes WHERE codigo=?',(code,)).fetchone()
    if not row:
        c.close(); raise ValueError('Expediente no encontrado.')
    if row['status'] not in ('BORRADOR','DEVUELTO'):
        c.close(); raise PermissionError('El expediente está bloqueado para modificar evidencias en su estado actual.')
    if user['rol']!='TECNICO':
        c.close(); raise PermissionError('Solo el Técnico Ambiental Distrital puede registrar evidencias de campo.')
    pr=c.execute('SELECT nombre FROM personal WHERE id=?',(user['personal_id'],)).fetchone()
    pname=pr['nombre'] if pr else ''
    if row['tecnico']!=pname:
        c.close(); raise PermissionError('Solo el técnico responsable registrado puede modificar las evidencias de este expediente.')
    if row['status']=='DEVUELTO':
        p=json_load(row['payload_json'],{})
        scope=p.get('_correction_scope',[])
        if allow_scope_key not in scope and 'evidence' not in scope and 'evidencias' not in scope:
            c.close(); raise PermissionError('La devolución no autoriza modificaciones en esta sección de evidencias.')
    return c,row

def evidence_summary(c,eid):
    photos=[dict(r) for r in c.execute('SELECT id,codigo,nombre_original,mime_type,tamano,sha256,descripcion,fecha_captura,subido_at,gps_point_id,hecho_id FROM fotografias WHERE expediente_id=? ORDER BY id',(eid,)).fetchall()]
    gps=[dict(r) for r in c.execute('SELECT id,codigo,lat,lng,datum,precision_m,altitud_m,fecha_hora,descripcion,hecho_id FROM puntos_gps WHERE expediente_id=? ORDER BY id',(eid,)).fetchall()]
    return photos,gps

def next_child_code(c,eid,prefix,table):
    row=c.execute(f"SELECT codigo FROM {table} WHERE expediente_id=? ORDER BY id DESC LIMIT 1",(eid,)).fetchone()
    n=1
    if row:
        m=re.search(r'(\d+)$',row['codigo'] or '')
        if m:n=int(m.group(1))+1
    return f'{prefix}-{n:03d}'

def list_evidence(code,user):
    c=conn();row=c.execute('SELECT id FROM expedientes WHERE codigo=?',(code,)).fetchone()
    if not row:c.close();raise ValueError('Expediente no encontrado.')
    if user['rol']=='TECNICO':
        pr=c.execute('SELECT nombre FROM personal WHERE id=?',(user['personal_id'],)).fetchone()
        pname=pr['nombre'] if pr else ''
        own=c.execute('SELECT tecnico FROM expedientes WHERE id=?',(row['id'],)).fetchone()['tecnico']
        if own!=pname:c.close();raise PermissionError('No tiene acceso a este expediente.')
    photos,gps=evidence_summary(c,row['id']);c.close();return {'ok':True,'fotografias':photos,'puntos_gps':gps}

def sync_operation_id(o):
    return str(o.get('_operation_id') or o.get('operation_id') or '').strip()

def replay_sync_operation(c, operation_id):
    if not operation_id:
        return None
    row=c.execute('SELECT response_json FROM sync_operations WHERE operation_id=?',(operation_id,)).fetchone()
    return json_load(row['response_json'],None) if row else None

def remember_sync_operation(c, operation_id, kind, response):
    if not operation_id:
        return
    c.execute('INSERT OR IGNORE INTO sync_operations(operation_id,kind,response_json,created_at) VALUES(?,?,?,?)',
              (operation_id,kind,json.dumps(response,ensure_ascii=False),now()))

def store_photo(handler,user):
    # Multipart parser is used only for actual image files; JSON API remains capped at 2 MB.
    from email.parser import BytesParser
    from email.policy import default
    ctype=handler.headers.get('Content-Type','')
    if not ctype.lower().startswith('multipart/form-data'):
        raise ValueError('La captura fotográfica requiere multipart/form-data.')
    length=int(handler.headers.get('Content-Length','0'))
    if length<=0 or length>MAX_PHOTO_BYTES+200_000: raise ValueError('La fotografía supera el tamaño máximo permitido.')
    body=handler.rfile.read(length)
    msg=BytesParser(policy=default).parsebytes((f'Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n').encode()+body)
    fields={}
    photo_part=None
    for part in msg.iter_parts():
        disp=part.get_content_disposition()
        name=part.get_param('name', header='content-disposition')
        if disp=='form-data' and name=='foto': photo_part=part
        elif disp=='form-data' and name: fields[name]=part.get_content()
    code=str(fields.get('codigo','')).strip()
    operation_id=str(fields.get('_operation_id') or fields.get('operation_id') or '').strip()
    if operation_id:
        c0=conn()
        try:
            replay=replay_sync_operation(c0,operation_id)
            if replay is not None:return replay
        finally:c0.close()
    desc=str(fields.get('descripcion','')).strip()[:1000]
    fecha=str(fields.get('fecha_captura','')).strip()[:40] or now()
    gps_id=str(fields.get('gps_point_id','')).strip() or None
    hecho_id=str(fields.get('hecho_id','')).strip() or None
    if not code: raise ValueError('Debe indicar el código del expediente.')
    if photo_part is None: raise ValueError('No se recibió el archivo fotográfico.')
    data=photo_part.get_payload(decode=True) or b''
    mime=(photo_part.get_content_type() or '').lower()
    if mime not in ALLOWED_PHOTO_TYPES: raise ValueError('Tipo de imagen no permitido. Use JPG, PNG o WEBP.')
    if not data or len(data)>MAX_PHOTO_BYTES: raise ValueError('Archivo fotográfico vacío o demasiado grande.')
    # Basic magic-byte validation avoids trusting only the browser MIME declaration.
    magic={'image/jpeg':(b'\xff\xd8\xff',),'image/png':(b'\x89PNG\r\n\x1a\n',),'image/webp':(b'RIFF',)}
    if not any(data.startswith(sig) for sig in magic[mime]): raise ValueError('El contenido del archivo no corresponde al tipo de imagen declarado.')
    c,row=get_exp_for_edit(code,user,'fotografias')
    try:
        if gps_id and not c.execute('SELECT 1 FROM puntos_gps WHERE id=? AND expediente_id=?',(int(gps_id),row['id'])).fetchone(): raise ValueError('Punto GPS asociado no pertenece al expediente.')
        if hecho_id: validate_fact_id(c,row['id'],hecho_id)
        codigo=next_child_code(c,row['id'],'FOT', 'fotografias')
        digest=hashlib.sha256(data).hexdigest(); ext=ALLOWED_PHOTO_TYPES[mime]; filename=secrets.token_hex(20)+'.'+ext
        folder=os.path.join(MEDIA_ROOT,row['codigo']);os.makedirs(folder,exist_ok=True)
        path=os.path.join(folder,filename)
        with open(path,'wb') as f:f.write(data)
        c.execute('INSERT INTO fotografias(expediente_id,codigo,archivo,nombre_original,mime_type,tamano,sha256,descripcion,fecha_captura,subido_at,subido_por,gps_point_id,hecho_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (row['id'],codigo,os.path.relpath(path,ROOT),os.path.basename(photo_part.get_filename() or codigo),mime,len(data),digest,desc,fecha,now(),user['username'],int(gps_id) if gps_id else None,hecho_id))
        response={'ok':True,'fotografia':dict(c.execute('SELECT id,codigo,nombre_original,mime_type,tamano,sha256,descripcion,fecha_captura,subido_at,gps_point_id,hecho_id FROM fotografias WHERE id=?',(c.execute('SELECT last_insert_rowid()').fetchone()[0],)).fetchone())}
        remember_sync_operation(c,operation_id,'photo',response)
        c.commit();return response
    except Exception:
        c.rollback();
        try:
            if 'path' in locals() and os.path.exists(path):os.remove(path)
        except Exception:pass
        raise
    finally:c.close()

def add_gps(o,user):
    code=(o.get('codigo') or '').strip();lat=o.get('lat');lng=o.get('lng')
    try:lat=float(lat);lng=float(lng)
    except:raise ValueError('Latitud y longitud son obligatorias y deben ser numéricas.')
    if not (-90<=lat<=90 and -180<=lng<=180):raise ValueError('Coordenadas fuera de rango.')
    datum=(o.get('datum') or 'WGS84').strip().upper()
    if datum!='WGS84':raise ValueError('La captura GPS institucional utiliza DATUM WGS84.')
    precision=o.get('precision_m');alt=o.get('altitud_m')
    try:precision=float(precision) if precision not in (None,'') else None
    except:raise ValueError('La precisión GPS no es válida.')
    try:alt=float(alt) if alt not in (None,'') else None
    except:raise ValueError('La altitud no es válida.')
    c,row=get_exp_for_edit(code,user,'gps')
    try:
        if (o.get('hecho_id') or '').strip(): validate_fact_id(c,row['id'],(o.get('hecho_id') or '').strip())
        codigo=next_child_code(c,row['id'],'P', 'puntos_gps')
        fecha=(o.get('fecha_hora') or now()).strip()[:40]
        c.execute('INSERT INTO puntos_gps(expediente_id,codigo,lat,lng,datum,precision_m,altitud_m,fecha_hora,descripcion,hecho_id) VALUES(?,?,?,?,?,?,?,?,?,?)',(row['id'],codigo,lat,lng,datum,precision,alt,fecha,(o.get('descripcion') or '').strip()[:1000],(o.get('hecho_id') or '').strip() or None));c.commit()
        return {'ok':True,'punto_gps':dict(c.execute('SELECT id,codigo,lat,lng,datum,precision_m,altitud_m,fecha_hora,descripcion,hecho_id FROM puntos_gps WHERE id=?',(c.execute('SELECT last_insert_rowid()').fetchone()[0],)).fetchone())}
    finally:c.close()

def delete_gps(o,user):
    code=(o.get('codigo') or '').strip();pid=int(o.get('id'));c,row=get_exp_for_edit(code,user,'gps')
    try:
        r=c.execute('SELECT * FROM puntos_gps WHERE id=? AND expediente_id=?',(pid,row['id'])).fetchone()
        if not r:raise ValueError('Punto GPS no encontrado.')
        c.execute('UPDATE fotografias SET gps_point_id=NULL WHERE gps_point_id=?',(pid,));c.execute('DELETE FROM puntos_gps WHERE id=?',(pid,));c.commit();return {'ok':True}
    finally:c.close()

def delete_photo(o,user):
    code=(o.get('codigo') or '').strip();pid=int(o.get('id'));c,row=get_exp_for_edit(code,user,'fotografias')
    try:
        r=c.execute('SELECT archivo FROM fotografias WHERE id=? AND expediente_id=?',(pid,row['id'])).fetchone()
        if not r:raise ValueError('Fotografía no encontrada.')
        c.execute('DELETE FROM fotografias WHERE id=?',(pid,));c.commit()
        path=os.path.join(ROOT,r['archivo'])
        try:
            if os.path.exists(path):os.remove(path)
        except Exception:pass
        return {'ok':True}
    finally:c.close()

class H(SimpleHTTPRequestHandler):
    server_version='LLE-Servidor/5.6.26'
    def __init__(self,*a,**kw):super().__init__(*a,directory=ROOT,**kw)
    def log_message(self,fmt,*args):return
    def send_pdf(self, pdf_bytes, filename):
        safe=re.sub(r'[^A-Za-z0-9._-]+','_',filename or 'documento.pdf').strip('._') or 'documento.pdf'
        if not safe.lower().endswith('.pdf'): safe += '.pdf'
        self.send_response(200)
        self.send_header('Content-Type','application/pdf')
        self.send_header('Content-Disposition',f'attachment; filename="{safe}"')
        self.send_header('Content-Length',str(len(pdf_bytes)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers(); self.wfile.write(pdf_bytes)
    def render_html_to_pdf(self, html, filename):
        if not isinstance(html,str) or not html.strip(): raise ValueError('No se recibió contenido para generar el PDF.')
        if len(html.encode('utf-8')) > 1_900_000: raise ValueError('El documento supera el tamaño máximo permitido para PDF.')
        safe=re.sub(r'[^A-Za-z0-9._-]+','_',filename or 'documento.pdf').strip('._') or 'documento.pdf'
        if not safe.lower().endswith('.pdf'): safe += '.pdf'
        with tempfile.TemporaryDirectory(prefix='lle_pdf_',dir=ROOT) as td:
            html_path=os.path.join(td,'documento.html'); pdf_path=os.path.join(td,safe)
            crest=os.path.join(ROOT,'01_SISTEMA_INSPECCIONES','escudo_la_libertad_este.png').replace('\\','/')
            html=html.replace('src="escudo_la_libertad_este.png"', 'src="file:///' + crest.lstrip('/') + '"')
            Path(html_path).write_text(html,encoding='utf-8')

            # Prefer WeasyPrint where it is already available (useful for Linux test environments).
            try:
                from weasyprint import HTML as WeasyHTML
                WeasyHTML(filename=html_path, base_url=ROOT).write_pdf(pdf_path)
                return Path(pdf_path).read_bytes(),safe
            except Exception:
                pass

            # Windows installations normally have Edge or Chrome; use their headless PDF engine so
            # “Guardar PDF” is a real download and does not require a print dialog.
            candidates=[
                os.environ.get('LLE_PDF_BROWSER',''),
                shutil.which('msedge'), shutil.which('microsoft-edge'), shutil.which('google-chrome'),
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            ]
            browser=next((x for x in candidates if x and ((os.path.isabs(x) and os.path.isfile(x)) or shutil.which(x))),None)
            if not browser: raise RuntimeError('No se encontró un motor PDF (WeasyPrint, Microsoft Edge o Google Chrome). Puede usar “Imprimir” y elegir “Guardar como PDF”.')
            cmd=[browser,'--headless=new','--disable-gpu','--disable-extensions','--allow-file-access-from-files',f'--print-to-pdf={pdf_path}',Path(html_path).as_uri()]
            proc=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45,text=True)
            if proc.returncode!=0 or not os.path.isfile(pdf_path):
                msg=(proc.stderr or proc.stdout or '').strip().replace('\n',' ')
                raise RuntimeError('No fue posible generar el PDF.'+(f' Detalle: {msg[:260]}' if msg else ''))
            return Path(pdf_path).read_bytes(),safe
    def sendj(self,o,status=200):
        b=json.dumps(o,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'");self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','same-origin');self.end_headers();self.wfile.write(b)
    def readj(self):
        n=int(self.headers.get('Content-Length',0));
        if n>2_000_000:raise ValueError('Solicitud demasiado grande.')
        return json.loads(self.rfile.read(n) or '{}')
    def do_OPTIONS(self):self.send_response(405);self.end_headers()
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/login':return self.sendj({'ok':False,'error':'Use POST para iniciar sesión.'},405)
        if p=='/api/health':return self.sendj({'ok':True,'version':APP_VERSION,'database':'SQLite','auth':'enabled'})
        if p.startswith('/api/'):
            u=require(self)
            if not u:return
            if p=='/api/me':
                pname=None
                if u['personal_id']:
                    c=conn(); pr=c.execute('SELECT nombre FROM personal WHERE id=?',(u['personal_id'],)).fetchone(); c.close(); pname=pr['nombre'] if pr else None
                return self.sendj({'ok':True,'username':u['username'],'rol':u['rol'],'personal_id':u['personal_id'],'personal_name':pname,'debe_cambiar':bool(u['debe_cambiar']),'email':u['email'] or ''})
            if p=='/api/expedientes':return self.sendj(all_exps(u))
            if p=='/api/notificaciones':
                rows=notifications_for(u)
                return self.sendj({'ok':True,'notificaciones':rows})
            if p.startswith('/api/notificaciones/contar'):
                rows=notifications_for(u)
                return self.sendj({'ok':True,'no_leidas':sum(1 for x in rows if not x['leida'])})
            if p.startswith('/api/asignaciones/'):
                code=p.split('/',3)[3] if len(p.split('/',3))>3 else ''
                return self.sendj({'ok':True,'asignaciones':assignment_history(code,u)})
            if p.startswith('/api/expediente/'):
                code=p.split('/',3)[3] if len(p.split('/',3))>3 else ''
                return self.sendj({'ok':True,'expediente':load_expediente(code,u)})
            if p.startswith('/api/evidencias/'):
                code=p.split('/',3)[3] if len(p.split('/',3))>3 else ''
                return self.sendj(list_evidence(code,u))
            if p.startswith('/api/fotografia/'):
                try: fid=int(p.rsplit('/',1)[1])
                except: return self.sendj({'ok':False,'error':'Identificador inválido.'},400)
                c=conn();r=c.execute('SELECT f.*,e.tecnico FROM fotografias f JOIN expedientes e ON e.id=f.expediente_id WHERE f.id=?',(fid,)).fetchone()
                if not r:c.close();return self.sendj({'ok':False,'error':'Fotografía no encontrada.'},404)
                if u['rol']=='TECNICO':
                    pr=c.execute('SELECT nombre FROM personal WHERE id=?',(u['personal_id'],)).fetchone();
                    if not pr or r['tecnico']!=pr['nombre']:c.close();return self.sendj({'ok':False,'error':'No tiene acceso a esta fotografía.'},403)
                path=os.path.join(ROOT,r['archivo']); mime=r['mime_type'];c.close()
                if not os.path.isfile(path):return self.sendj({'ok':False,'error':'Archivo fotográfico no disponible.'},404)
                b=open(path,'rb').read();self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.end_headers();self.wfile.write(b);return
            if p=='/api/personal':return self.sendj(personnel(False))
            if p=='/api/personal/activos':return self.sendj(personnel(True))
            return self.sendj({'ok':False,'error':'Recurso no encontrado.'},404)
        # Never expose source, database, bytecode, logs or hidden files.
        rel=os.path.relpath(os.path.abspath(os.path.join(ROOT,p.lstrip('/'))),ROOT)
        if rel in ('.','01_SISTEMA_INSPECCIONES','02_MOTOR_SEGUIMIENTO'):
            rel = 'index.html' if rel=='.' else rel + '/index.html'
        if rel.startswith('..') or os.path.basename(rel).startswith('.') or os.path.splitext(rel)[1].lower() in {'.py','.pyc','.sqlite','.sqlite3','.db'} or '__pycache__' in rel:
            return self.sendj({'ok':False,'error':'Recurso no disponible.'},404)
        if rel not in SAFE_STATIC:return self.sendj({'ok':False,'error':'Recurso no disponible.'},404)
        # The HTML shell is public only to present the login screen; all data/API operations remain protected.
        u=current_user(self)
        if rel in {'index.html','01_SISTEMA_INSPECCIONES/index.html','01_SISTEMA_INSPECCIONES/offline-core.js','01_SISTEMA_INSPECCIONES/sw.js','01_SISTEMA_INSPECCIONES/manifest.json','01_SISTEMA_INSPECCIONES/escudo_la_libertad_este.png','02_MOTOR_SEGUIMIENTO/index.html','02_MOTOR_SEGUIMIENTO/escudo_la_libertad_este.png'}: pass
        elif not u:return self.sendj({'ok':False,'error':'Autenticación requerida.'},401)
        self.send_response(200);self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'");ctype='text/html; charset=utf-8' if rel.endswith('.html') else ('application/javascript; charset=utf-8' if rel.endswith('.js') else ('application/manifest+json' if rel.endswith('.json') else 'image/png'));self.send_header('Content-Type',ctype);self.send_header('Service-Worker-Allowed','/01_SISTEMA_INSPECCIONES/' if rel.endswith('sw.js') else '');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','same-origin');
        try:
            with open(os.path.join(ROOT,rel),'rb') as f:b=f.read()
            self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        except: self.send_error(404)
    def do_POST(self):
        p=urlparse(self.path).path
        try:
            o={}
            if p not in ('/api/fotografia',):
                o=self.readj()
            u=current_user(self)
            if p=='/api/recuperar-acceso':
                return self.sendj(create_recovery_request(o,self))
            if p=='/api/cuenta/email':
                if not u: raise PermissionError('Debe iniciar sesión para registrar el correo de recuperación.')
                set_recovery_email(o,u); return self.sendj({'ok':True})
            if p=='/api/restablecer-password':
                return self.sendj(complete_recovery(o))
            if p=='/api/login':
                ip=self.client_address[0]
                if not login_allowed(ip): return self.sendj({'ok':False,'error':'Demasiados intentos de inicio de sesión. Espere unos minutos.'},429)
                note_login(ip)
                c=conn();u=authenticate(c,o.get('username',''),o.get('password',''))
                if not u:c.close();return self.sendj({'ok':False,'error':'Usuario o contraseña incorrectos.'},401)
                token=create_session(c,u['id']);c.close();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Set-Cookie',f'lle_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_HOURS*3600}');self.end_headers();self.wfile.write(json.dumps({'ok':True,'username':u['username'],'rol':u['rol'],'debe_cambiar':bool(u['debe_cambiar'])}).encode());return
            if p=='/api/documento/pdf':
                # HTML to PDF is restricted to authenticated users and uses a local browser engine on the server PC.
                html=o.get('html',''); filename=o.get('filename','documento.pdf')
                pdf_bytes,safe=self.render_html_to_pdf(html,filename); return self.send_pdf(pdf_bytes,safe)
            if p=='/api/logout':
                raw=self.headers.get('Cookie','');jar=cookies.SimpleCookie();jar.load(raw);m=jar.get('lle_session');
                if m:
                    c=conn();c.execute('UPDATE sesiones SET revocada=1 WHERE token_hash=?',(token_hash(m.value),));c.commit();c.close()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Set-Cookie','lle_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');self.end_headers();self.wfile.write(b'{"ok":true}');return
            if p=='/api/cambiar-password':
                u=require(self)
                if not u:return
                old=o.get('password_actual',''); new=o.get('password_nueva','')
                if len(new)<12 or len(new)>200: raise ValueError('La nueva contraseña debe tener entre 12 y 200 caracteres.')
                if not verify_password(old,u['salt'],u['password_hash']): return self.sendj({'ok':False,'error':'La contraseña actual es incorrecta.'},401)
                ns,nh=hash_password(new); c=conn();c.execute('UPDATE usuarios SET salt=?,password_hash=?,debe_cambiar=0,actualizado_at=? WHERE id=?',(ns,nh,now(),u['id']));c.commit();c.close();return self.sendj({'ok':True})
            u=require(self)
            if not u:return
            if p=='/api/fotografia':
                # Multipart: no readj() because photographs are binary files.
                return self.sendj(store_photo(self,u))
            if p in ('/api/gps','/api/gps/eliminar','/api/fotografia/eliminar'):
                operation_id=sync_operation_id(o)
                c0=conn()
                try: replay=replay_sync_operation(c0,operation_id)
                finally:c0.close()
                if replay is not None:return self.sendj(replay)
                if p=='/api/gps': response=add_gps(o,u); kind='gps'
                elif p=='/api/gps/eliminar': response=delete_gps(o,u); kind='delete-gps'
                else: response=delete_photo(o,u); kind='delete-photo'
                c1=conn();
                try: remember_sync_operation(c1,operation_id,kind,response);c1.commit()
                finally:c1.close()
                return self.sendj(response)
            if p=='/api/recepcion':
                return self.sendj({'ok':True,'codigo':create_reception(o,u)})
            if p=='/api/recepcion-desde-acta':
                return self.sendj(create_reception_from_technician(o,u))
            if p=='/api/asignar':
                return self.sendj({'ok':True,'expediente':assign_reception(o,u)})
            if p=='/api/expediente':
                # Actor/status supplied by browser are ignored; identity and permissions come from session.
                operation_id=sync_operation_id(o)
                c0=conn()
                try:
                    replay=replay_sync_operation(c0,operation_id)
                finally:c0.close()
                if replay is not None:return self.sendj(replay)
                o.pop('_actor',None);o.pop('_finalize',None);finalize=bool(o.pop('_client_finalize',False))
                c=conn()
                try:
                    if u['rol']=='TECNICO':
                        pr=c.execute('SELECT nombre FROM personal WHERE id=?',(u['personal_id'],)).fetchone();u2=dict(u);u2['personal_name']=pr['nombre'] if pr else ''
                        eid,ver,status=upsert(o,c,u2,finalize=finalize);response={'ok':True,'id':eid,'version':ver,'status':status,'codigo':o.get('codigo')};remember_sync_operation(c,operation_id,'expediente',response);c.commit();return self.sendj(response)
                    raise PermissionError('Solo un Técnico Ambiental Distrital puede guardar actuaciones técnicas.')
                finally:c.close()
            if p=='/api/revision':return self.sendj({'ok':True,'expediente':revision(o,u)})
            if p=='/api/notificaciones/leida':
                mark_notification(o,u);return self.sendj({'ok':True})
            if p=='/api/notificaciones/marcar-todas-leidas':
                c=conn();c.execute('UPDATE notificaciones SET leida=1 WHERE usuario=?',(u['username'],));c.commit();c.close();return self.sendj({'ok':True})
            if p=='/api/personal':
                if u['rol']!='GERENTE':raise PermissionError('Solo el Gerente Ambiental puede gestionar el personal técnico.')
                add_person(o);return self.sendj({'ok':True})
            if p=='/api/personal/status':
                if u['rol']!='GERENTE':raise PermissionError('Solo el Gerente Ambiental puede activar o desactivar personal técnico.')
                set_person_status(o);return self.sendj({'ok':True})
            if p=='/api/eliminar':
                pr=conn().execute('SELECT nombre FROM personal WHERE id=?',(u['personal_id'],)).fetchone();u2=dict(u);u2['personal_name']=pr['nombre'] if pr else '';delete_draft(o,u2);return self.sendj({'ok':True})
            if p=='/api/remision':
                return self.sendj({'ok':True,'expediente':remit_case(o,u)})
            if p=='/api/cierre':
                return self.sendj({'ok':True,'expediente':close_case(o,u)})
            return self.sendj({'ok':False,'error':'Recurso no encontrado.'},404)
        except PermissionError as e:return self.sendj({'ok':False,'error':str(e)},403)
        except sqlite3.IntegrityError:return self.sendj({'ok':False,'error':'Registro duplicado o referencia inválida.'},409)
        except Exception as e:return self.sendj({'ok':False,'error':str(e)},400)

conn().close();ensure_admin()
BIND=os.environ.get('LLE_BIND','127.0.0.1')
PORT=int(os.environ.get('LLE_PORT','8001'))
HTTPS=os.environ.get('LLE_HTTPS','0')=='1'
CERT=os.environ.get('LLE_TLS_CERT',os.path.join(ROOT,'tls','cert.pem'))
KEY=os.environ.get('LLE_TLS_KEY',os.path.join(ROOT,'tls','key.pem'))
server=ThreadingHTTPServer((BIND,PORT),H)
if HTTPS:
    if not (os.path.isfile(CERT) and os.path.isfile(KEY)):
        raise SystemExit(f'HTTPS habilitado pero faltan certificado/clave: {CERT} / {KEY}')
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(CERT,KEY)
    server.socket=ctx.wrap_socket(server.socket,server_side=True)
    print(f'Servidor LLE {APP_VERSION} HTTPS iniciado en https://{BIND}:{PORT}/')
else:
    print(f'Servidor LLE {APP_VERSION} HTTP iniciado en http://{BIND}:{PORT}/')
server.serve_forever()
