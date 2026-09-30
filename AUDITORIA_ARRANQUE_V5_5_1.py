import os, sys, time, json, sqlite3, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVER = ROOT / 'server.py'
DB = ROOT / 'sistema_gestion_ambiental.sqlite3'
PORT = int(os.environ.get('LLE_PORT', '8001'))
BASE = f'http://127.0.0.1:{PORT}'
REPORT = ROOT / 'AUDITORIA_ARRANQUE_V5_5_1.txt'

results=[]
def add(name, ok, detail=''):
    results.append((name, bool(ok), detail))

def http(path, method='GET', data=None):
    req=urllib.request.Request(BASE+path, method=method)
    if data is not None:
        raw=json.dumps(data, ensure_ascii=False).encode()
        req.add_header('Content-Type','application/json')
    else: raw=None
    try:
        with urllib.request.urlopen(req, data=raw, timeout=4) as r:
            return r.status, dict(r.headers), r.read(20000)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(20000)
    except Exception as e:
        return None, {}, str(e).encode()

def wait_server():
    for _ in range(20):
        s,_,b=http('/api/health')
        if s==200:
            return True,b
        time.sleep(.5)
    return False,b''

def source_audit():
    try: src=SERVER.read_text(encoding='utf-8')
    except Exception as e:
        add('Núcleo: lectura de server.py',False,str(e)); return
    add('Núcleo: servidor V5.5.1 declarado', 'V5.5.1' in src, 'Busca identificación V5.5.1')
    add('Núcleo: credenciales de prueba sincronizadas', all(x in src for x in ['LLE-Tecnico-2026!','LLE-Gerente-2026!','LLE-Admin-2026!']) and 'debe_cambiar=0' in src and 'password_hash' in src, 'Las tres cuentas provisionales se sincronizan en desarrollo')
    add('Núcleo: recuperación de expediente desde servidor', "def load_expediente(code,user):" in src and "p.startswith('/api/expediente/')" in src, 'SQLite es la fuente de recuperación para expedientes existentes')
    add('Núcleo: relación de evidencia con hecho validada', 'def validate_fact_id(c, expediente_id, hecho_id):' in src and 'El hecho relacionado no existe' in src, 'Evita referencias a hechos inexistentes')
    add('Núcleo: archivos fotográficos eliminados con borrador', 'photo_paths=' in src and "DELETE FROM fotografias" in src and 'os.remove(path)' in src, 'Evita archivos huérfanos al eliminar borradores')
    add('Núcleo: status del cliente eliminado', "o.pop('status', None)" in src, 'El servidor elimina status recibido')
    add('Núcleo: actor del cliente eliminado', "o.pop('_actor', None)" in src, 'El servidor elimina actor recibido')
    add('Núcleo: estado se asigna después de hidratar', "o['status'] = status if not row else newstatus" in src, 'Sincronización final')
    add('Núcleo: columna y payload se guardan juntos', "SET status=?,payload_json=?" in src, 'Persistencia sincronizada')
    add('Núcleo: responsable activo validado', "not r['activo']" in src and 'responsable seleccionado está inactivo' in src, 'Bloqueo de técnico responsable inactivo')
    add('Núcleo: participante activo validado', "not pr['activo']" in src and 'participante está inactivo' in src, 'Bloqueo de participante inactivo')
    add('Núcleo: visibilidad por rol', "if user['rol']=='TECNICO'" in src and "WHERE tecnico=?" in src, 'Técnico filtrado por responsable')
    add('Núcleo: revisión solo Gerente/Admin', "user['rol'] not in ('GERENTE','ADMIN')" in src, 'Control de revisión')
    add('Núcleo: remisión exige VB_APROBADO', "row['status']!='VB_APROBADO'" in src, 'Control de transición de remisión')
    add('Motores: ruta Sistema 1 permitida', '01_SISTEMA_INSPECCIONES/index.html' in src, 'Recurso estático')
    add('Motores: ruta Sistema 2 permitida', '02_MOTOR_SEGUIMIENTO/index.html' in src, 'Recurso estático')
    add('Motores: API de expediente presente', "p=='/api/expediente'" in src, 'Motor de inspecciones')
    add('Motores: API de revisión presente', "p=='/api/revision'" in src, 'Motor de seguimiento')
    add('Motores: API de remisión presente', "p=='/api/remision'" in src, 'Motor de seguimiento')
    add('Seguridad: recursos sensibles bloqueados', 'SAFE_STATIC' in src and "Recurso no disponible." in src, 'Lista blanca estática')
    add('Seguridad: bind local predeterminado', "os.environ.get('LLE_BIND','127.0.0.1')" in src, '127.0.0.1 por defecto')

def runtime_audit():
    ok,b=wait_server(); add('Arranque: /api/health responde',ok,b.decode(errors='replace')[:300]);
    if not ok: return
    s,h,b=http('/api/health'); add('Arranque: versión reportada V5.5.1', s==200 and b'V5.5.1' in b, b.decode(errors='replace')[:300])
    s,_,b=http('/api/expedientes'); add('Seguridad: /api/expedientes sin sesión = 401',s==401,f'HTTP {s}')
    s,_,b=http('/api/personal'); add('Seguridad: /api/personal sin sesión = 401',s==401,f'HTTP {s}')
    for path in ('/server.py','/sistema_gestion_ambiental.sqlite3','/data.json','/__pycache__/server.cpython-311.pyc'):
        s,_,_=http(path); add(f'Seguridad: {path} bloqueado',s==404,f'HTTP {s}')
    for path in ('/01_SISTEMA_INSPECCIONES/','/02_MOTOR_SEGUIMIENTO/'):
        s,_,_=http(path); add(f'Motor: {path} accesible',s==200,f'HTTP {s}')
    s,h,_=http('/api/expedientes',method='OPTIONS'); add('Seguridad: CORS no habilitado', 'Access-Control-Allow-Origin' not in h,f'HTTP {s}; ACAO={h.get("Access-Control-Allow-Origin")}')
    # Prueba explícita de las tres credenciales provisionales publicadas.
    creds=[('tecnico','LLE-Tecnico-2026!','TECNICO'),('gerente','LLE-Gerente-2026!','GERENTE'),('admin','LLE-Admin-2026!','ADMIN')]
    for username,password,rol in creds:
        s,_,b=http('/api/login',method='POST',data={'username':username,'password':password})
        try: obj=json.loads(b.decode('utf-8'))
        except: obj={}
        add(f'Autenticación explícita: {username}', s==200 and obj.get('ok') is True and obj.get('rol')==rol and obj.get('debe_cambiar') is False, f'HTTP {s}; respuesta={obj}')

def db_audit():
    if not DB.exists():
        add('BD: archivo SQLite existe tras arranque',False,'No se encontró la base en la carpeta del sistema'); return
    try:
        c=sqlite3.connect(f'file:{DB.as_posix()}?mode=ro',uri=True); c.row_factory=sqlite3.Row
        ic=c.execute('PRAGMA integrity_check').fetchone()[0]; fk=c.execute('PRAGMA foreign_key_check').fetchall()
        add('BD: PRAGMA integrity_check = OK',ic=='ok',str(ic))
        add('BD: PRAGMA foreign_key_check = 0',len(fk)==0,f'{len(fk)} errores')
        tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        expected={'expedientes','versiones','historial','evidencias','documentos','personal','participantes_inspeccion','usuarios','sesiones','fotografias','puntos_gps'}
        add('BD: tablas núcleo presentes',expected.issubset(tables),', '.join(sorted(tables)))
        dup=c.execute('SELECT codigo,COUNT(*) n FROM expedientes GROUP BY codigo HAVING n>1').fetchall()
        add('BD: códigos de expediente únicos',len(dup)==0,f'{len(dup)} duplicados')
        mismatch=0
        for r in c.execute('SELECT status,payload_json FROM expedientes'):
            try: p=json.loads(r['payload_json'] or '{}')
            except: p={}
            if p.get('status')!=r['status']: mismatch+=1
        add('BD: status = payload_json.status',mismatch==0,f'{mismatch} inconsistencias')
        inactive_new=[]
        q="""SELECT e.codigo,p.nombre,p.activo FROM participantes_inspeccion pi JOIN expedientes e ON e.id=pi.expediente_id JOIN personal p ON p.id=pi.personal_id WHERE p.activo=0 AND e.status='BORRADOR'"""
        inactive_new=c.execute(q).fetchall()
        add('BD: no hay participantes inactivos en borradores',len(inactive_new)==0,f'{len(inactive_new)} encontrados')
        c.close()
    except Exception as e:
        add('BD: lectura de integridad',False,str(e))

def main():
    print('=== AUDITORÍA ESPECIAL DE ARRANQUE V5.5.1 ===')
    print('Núcleo + Motores + Seguridad básica + BD')
    source_audit(); runtime_audit(); db_audit()
    for n,ok,d in results: print(('PASS' if ok else 'FAIL').ljust(5), n, '-', d)
    p=sum(x[1] for x in results); f=len(results)-p
    text=['AUDITORÍA ESPECIAL DE ARRANQUE V5.5.1','='*55,f'Fecha/hora: {time.strftime("%Y-%m-%d %H:%M:%S")}',f'URL: {BASE}','',f'PASS: {p}',f'FAIL: {f}','']
    text += [('[PASS]' if ok else '[FAIL]') + f' {n} | {d}' for n,ok,d in results]
    text += ['', 'DICTAMEN: APROBADA' if f==0 else 'DICTAMEN: NO APROBADA — revisar fallas antes de release']
    REPORT.write_text('\n'.join(text),encoding='utf-8')
    return 0 if f==0 else 1

if __name__=='__main__': sys.exit(main())
