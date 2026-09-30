from pathlib import Path
import re, subprocess, json, sqlite3
ROOT=Path(__file__).parent
results=[]
def C(n,ok,d=''): results.append((n,ok,d)); print(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else ''))
server=(ROOT/'server.py').read_text(encoding='utf-8'); ui1=(ROOT/'01_SISTEMA_INSPECCIONES/index.html').read_text(encoding='utf-8'); ui2=(ROOT/'02_MOTOR_SEGUIMIENTO/index.html').read_text(encoding='utf-8'); off=(ROOT/'01_SISTEMA_INSPECCIONES/offline-core.js').read_text(encoding='utf-8'); sw=(ROOT/'01_SISTEMA_INSPECCIONES/sw.js').read_text(encoding='utf-8'); mf=(ROOT/'01_SISTEMA_INSPECCIONES/manifest.json').read_text(encoding='utf-8')
r=subprocess.run(['python','-m','py_compile',str(ROOT/'server.py'),str(ROOT/'GENERAR_CERTIFICADO_LAN_D06.py')],capture_output=True,text=True);C('Python syntax',r.returncode==0,r.stderr.strip())
for n,f in [('Sistema1',ROOT/'01_SISTEMA_INSPECCIONES/index.html'),('Sistema2',ROOT/'02_MOTOR_SEGUIMIENTO/index.html')]:
 js='\n'.join(re.findall(r'<script>(.*?)</script>',f.read_text(encoding='utf-8'),re.S));tmp=Path('/tmp/'+n+'_D06.js');tmp.write_text(js,encoding='utf-8');r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True);C(n+' JavaScript syntax',r.returncode==0,r.stderr.strip())
r=subprocess.run(['node','--check',str(ROOT/'01_SISTEMA_INSPECCIONES/offline-core.js')],capture_output=True,text=True);C('offline-core JavaScript syntax',r.returncode==0,r.stderr.strip())
r=subprocess.run(['node','--check',str(ROOT/'01_SISTEMA_INSPECCIONES/sw.js')],capture_output=True,text=True);C('Service Worker syntax',r.returncode==0,r.stderr.strip())
for n,cond in [
('IndexedDB stores', 'indexedDB.open' in off and all(x in off for x in ['expedientes','queue','photos','gps','cache'])),
('Offline save', 'window.save=async function' in off and 'saveExpLocal(state)' in off),
('Offline photos as Blob', "put('photos'" in off and "fd.append('foto',op.blob" in off),
('Offline GPS queue', "kind:'gps'" in off),
('Sync queue states', 'PENDIENTE' in off and 'ENVIANDO' in off and 'ERROR_REINTENTABLE' in off),
('Offline reception for new field records', "kind:'reception'" in off and '/api/recepcion-desde-acta' in off),
('Save deduplication', 'dedupe_key' in off and 'old.dedupe_key===op.dedupe_key' in off),
('Offline session cache', 'cacheUser' in off and 'cachedUser' in off),
('Service Worker shell cache', "addEventListener('install'" in sw and 'caches.open' in sw),
('Service Worker excludes API', "if(u.pathname.startsWith('/api/'))return;" in sw),
('PWA manifest standalone', '"display":"standalone"' in mf),
('HTTPS server support', 'LLE_HTTPS' in server and 'SSLContext' in server),
('Offline assets public', all(x in server for x in ['offline-core.js','sw.js','manifest.json'])),
('HTTP mobile warning', 'HTTPS en el teléfono' in off)]: C(n,cond)
C('D01-D05 state machine retained', all(x in server for x in ['VALID_STATUSES','o.pop(\'status\', None)','row[\'status\']!=\'INFORME_FINALIZADO_PENDIENTE_VB\'']))
c=sqlite3.connect(ROOT/'sistema_gestion_ambiental.sqlite3'); counts={t:c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['expedientes','personal','usuarios','notificaciones','asignaciones']}; c.close(); C('Database remains clean for test package', counts['expedientes']==0 and counts['notificaciones']==0 and counts['asignaciones']==0,str(counts))
passed=sum(x[1] for x in results);print(f'RESULTADO {passed}/{len(results)} PASS');raise SystemExit(0 if passed==len(results) else 1)
