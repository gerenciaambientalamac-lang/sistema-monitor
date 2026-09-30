from pathlib import Path
import re, subprocess, sqlite3, json, urllib.request, urllib.error, http.cookiejar
ROOT=Path(__file__).parent
R=[]
def C(n,ok,d=''):
 R.append(ok);print(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else ''))
server=(ROOT/'server.py').read_text(encoding='utf-8'); off=(ROOT/'01_SISTEMA_INSPECCIONES/offline-core.js').read_text(encoding='utf-8'); sw=(ROOT/'01_SISTEMA_INSPECCIONES/sw.js').read_text(encoding='utf-8'); ui=(ROOT/'01_SISTEMA_INSPECCIONES/index.html').read_text(encoding='utf-8'); mf=(ROOT/'01_SISTEMA_INSPECCIONES/manifest.json').read_text(encoding='utf-8')
r=subprocess.run(['python','-m','py_compile',str(ROOT/'server.py')],capture_output=True,text=True);C('Python syntax',r.returncode==0,r.stderr.strip())
r=subprocess.run(['node','--check',str(ROOT/'01_SISTEMA_INSPECCIONES/offline-core.js')],capture_output=True,text=True);C('offline-core syntax',r.returncode==0,r.stderr.strip())
r=subprocess.run(['node','--check',str(ROOT/'01_SISTEMA_INSPECCIONES/sw.js')],capture_output=True,text=True);C('Service Worker syntax',r.returncode==0,r.stderr.strip())
for name,path in [('Sistema1',ROOT/'01_SISTEMA_INSPECCIONES/index.html'),('Sistema2',ROOT/'02_MOTOR_SEGUIMIENTO/index.html')]:
 js='\n'.join(re.findall(r'<script>(.*?)</script>',path.read_text(encoding='utf-8'),re.S));tmp=Path('/tmp/'+name+'_D06R1.js');tmp.write_text(js,encoding='utf-8');r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True);C(name+' JS syntax',r.returncode==0,r.stderr.strip())
checks=[
('R1 IndexedDB version',"LLE_D06_OFFLINE_R1" in off and "VER=2" in off),
('Required local stores',all("'"+x+"'" in off for x in ['meta','expedientes','queue','photos','gps','cache','maps'])),
('Operation identity',"operation_id" in off and "_operation_id" in off),
('Queue state machine',all(x in off for x in ['PENDIENTE','ENVIANDO','ERROR_REINTENTABLE'])),
('Server idempotency table','sync_operations' in server and 'UNIQUE' in server),
('Reception idempotency hook','create_reception_from_technician' in server and 'remember_sync_operation' in server),
('Expediente idempotency hook',"remember_sync_operation(c,operation_id,'expediente'" in server),
('GPS idempotency endpoint',"p in ('/api/gps','/api/gps/eliminar','/api/fotografia/eliminar')" in server),
('Photo idempotency multipart','fields.get(\'_operation_id\')' in server and "remember_sync_operation(c,operation_id,'photo'" in server),
('Offline assigned cache','cacheAssigned' in off and "get('cache','assignedQueue')" in off),
('Startup loads assigned queue offline',"if(u.rol==='TECNICO'){if(LLE_D06.online())await loadPersonnel();await loadAssignedQueue();}" in ui),
('Server reachability separate from navigator.onLine','serverReachable' in off and "fetch('/api/health'" in off),
('Offline photos as Blob',"put('photos'" in off and "op.blob" in off),
('Offline GPS store',"put('gps'" in off and "operation('gps'" in off),
('Offline delete queue','delete-gps' in off and 'delete-photo' in off),
('Offline session cache','cachedUser' in off and 'cacheUser' in off),
('PWA manifest standalone','"display":"standalone"' in mf),
('Service Worker navigation fallback',"caches.match(SCOPE+'index.html')" in sw),
('Service Worker API bypass',"u.pathname.startsWith('/api/')" in sw),
('HTTPS warning',"modo offline requiere HTTPS" in off),
('D01-D05 state machine retained',all(x in server for x in ['VALID_STATUSES','o.pop(\'status\', None)','row[\'status\']!=\'INFORME_FINALIZADO_PENDIENTE_VB\'']))
]
for n,ok in checks:C(n,ok)
# clean database sanity
c=sqlite3.connect(ROOT/'sistema_gestion_ambiental.sqlite3'); counts={t:c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['expedientes','personal','usuarios','notificaciones','asignaciones']}; c.close();C('Clean DB baseline',counts['expedientes']==0 and counts['notificaciones']==0 and counts['asignaciones']==0,str(counts))
passed=sum(R);print(f'RESUMEN {passed}/{len(R)} PASS');raise SystemExit(0 if passed==len(R) else 1)
