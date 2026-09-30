from pathlib import Path
import re, subprocess, tempfile, json
ROOT=Path(__file__).resolve().parent
S1=ROOT/'01_SISTEMA_INSPECCIONES'/'index.html'
s=S1.read_text(encoding='utf-8')
checks=[]
def C(name,ok,detail=''):
    checks.append((name,bool(ok),detail))
C('Sistema 1 HTML', '<html' in s.lower() and '</html>' in s.lower())
C('Paso 1 funcional', 'onclick="openTechStep(1)"' in s and 'function openTechStep(step)' in s)
C('Paso 2 funcional', 'onclick="openTechStep(2)"' in s)
C('Paso 3 funcional', 'onclick="openTechStep(3)"' in s)
C('Paso 4 funcional', 'onclick="openTechStep(4)"' in s)
C('Bandeja siempre accesible', 'id="assignedQueue"' in s and 'No hay actuaciones disponibles para iniciar.' in s)
C('Flujo institucional preservado', 'El Técnico no crea ni modifica la recepción' in s and 'asignada por el Gerente Ambiental' in s)
C('Logo ruta LAN', '/01_SISTEMA_INSPECCIONES/escudo_la_libertad_este.png' in s)
C('Estado de conexión', 'techConnectionStatus' in s and 'serverReachable' in s)
C('D06 offline core', (ROOT/'01_SISTEMA_INSPECCIONES'/'offline-core.js').exists())
C('Service Worker', (ROOT/'01_SISTEMA_INSPECCIONES'/'sw.js').exists())
C('GitHub sin SQLite', not (ROOT/'sistema_gestion_ambiental.sqlite3').exists())
# JS syntax
js='\n'.join(re.findall(r'<script>(.*?)</script>',s,re.S))
with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8') as f:
    f.write(js); jspath=f.name
r=subprocess.run(['node','--check',jspath],capture_output=True,text=True)
C('Sistema 1 JS syntax',r.returncode==0,(r.stderr or r.stdout).strip())
for name,ok,detail in checks:
    print(('PASS' if ok else 'FAIL')+' | '+name+((' | '+detail) if detail else ''))
print(f'\nTOTAL: {sum(1 for _,ok,_ in checks if ok)}/{len(checks)} PASS')
raise SystemExit(0 if all(ok for _,ok,_ in checks) else 1)
