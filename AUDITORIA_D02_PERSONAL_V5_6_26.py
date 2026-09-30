import json, pathlib, re, subprocess, sqlite3, time, urllib.request, urllib.error, http.cookiejar, os, signal
ROOT=pathlib.Path(__file__).parent
BASE='http://127.0.0.1:18083'
R=[]
def C(name,ok,detail=''): R.append((name,bool(ok),detail)); print(('PASS' if ok else 'FAIL')+' | '+name+(' | '+detail if detail else ''))

def req(op,path,method='GET',data=None):
    body=json.dumps(data).encode() if data is not None else None
    headers={'Content-Type':'application/json'} if body else {}
    try:
        x=op.open(urllib.request.Request(BASE+path,data=body,headers=headers,method=method),timeout=8)
        return x.status,json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code,json.loads(e.read().decode())

# Static audit
r=subprocess.run(['python','-m','py_compile',str(ROOT/'server.py')],capture_output=True,text=True); C('Python syntax',r.returncode==0,r.stderr.strip())
for f in [ROOT/'01_SISTEMA_INSPECCIONES/index.html',ROOT/'02_MOTOR_SEGUIMIENTO/index.html']:
    js='\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',f.read_text(encoding='utf-8'),re.S)); tmp=pathlib.Path('/tmp/'+f.parent.name+'_D02.js'); tmp.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True); C(f'{f.parent.name} JavaScript syntax',r.returncode==0,r.stderr.strip())
s=(ROOT/'server.py').read_text(encoding='utf-8'); u=(ROOT/'02_MOTOR_SEGUIMIENTO/index.html').read_text(encoding='utf-8')
C('Gerente is sole personnel manager', "if u['rol']!='GERENTE':raise PermissionError('Solo el Gerente Ambiental puede gestionar el personal técnico.')" in s)
C('Case-insensitive duplicate protection', 'LOWER(TRIM(nombre))=LOWER(TRIM(?))' in s)
C('Name whitespace normalization', "' '.join(str(o.get('nombre') or '').split())" in s)
C('Unknown personnel ID rejected', "if not row: raise ValueError('El registro de personal no existe.')" in s)
C('Personnel UI restricted to Gerente', "personnelCard').style.display=u.rol==='GERENTE'?'block':'none'" in u)

db=sqlite3.connect(ROOT/'sistema_gestion_ambiental.sqlite3'); C('Clean DB has no test expedients',db.execute('SELECT COUNT(*) FROM expedientes').fetchone()[0]==0); C('Clean DB has baseline personnel only',db.execute('SELECT COUNT(*) FROM personal').fetchone()[0]==1); db.close()

# Runtime audit on isolated local server
p=subprocess.Popen(['python','-u','server.py'],cwd=ROOT,env={**os.environ,'LLE_PORT':'18083'},stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
try:
    time.sleep(1); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    st,j=req(op,'/api/health'); C('Health V5.6.26',st==200 and j.get('version')=='V5.6.26',str(j))
    st,j=req(op,'/api/login','POST',{'username':'gerente','password':'LLE-Gerente-2026!'}); C('Gerente login',st==200,str(j))
    st,j=req(op,'/api/personal','POST',{'nombre':'  Técnico   D02   Uno  ','cargo':' Técnico Ambiental Distrital '}); C('Add personnel by Gerente',st==200,str(j))
    st,j=req(op,'/api/personal','POST',{'nombre':'técnico d02 uno'}); C('Case-insensitive duplicate rejected',st==400 and 'ya está registrado' in j.get('error',''),str(j))
    st,j=req(op,'/api/personal','POST',{'nombre':'   '}); C('Blank name rejected',st==400,str(j))
    plist=req(op,'/api/personal')[1]; tech=[x for x in plist if x['nombre']=='Técnico D02 Uno'][0]
    st,j=req(op,'/api/personal/status','POST',{'id':tech['id'],'activo':False}); C('Deactivate personnel',st==200,str(j))
    st,j=req(op,'/api/recepcion','POST',{'origen':'Denuncia ambiental','fecha_recepcion':'2026-09-25','tipo':'OI','distrito':'Zaragoza','tipo_actuacion':'Inspección','modalidad_inspeccion':'INDIVIDUAL','solicitante':'D02','descripcion_inicial':'Prueba'}); C('Create reception for assignment test',st==200,str(j)); code=j.get('codigo')
    st,j=req(op,'/api/asignar','POST',{'codigo':code,'tecnico':'Técnico D02 Uno'}); C('Inactive technician cannot be assigned',st==403,str(j))
    st,j=req(op,'/api/personal/status','POST',{'id':tech['id'],'activo':True}); C('Reactivate personnel',st==200,str(j))
    st,j=req(op,'/api/asignar','POST',{'codigo':code,'tecnico':'Técnico D02 Uno'}); C('Active technician can be assigned',st==200,str(j))
    st,j=req(op,'/api/personal/status','POST',{'id':tech['id'],'activo':False}); C('Deactivate after historical assignment',st==200,str(j))
    plist=req(op,'/api/personal')[1]; C('Historical personnel remains in catalog',any(x['id']==tech['id'] and x['activo']==0 for x in plist),str(plist))
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except: p.kill()

passed=sum(x[1] for x in R); total=len(R)
(ROOT/'REPORTE_AUDITORIA_D02_PERSONAL_V5_6_26.txt').write_text('AUDITORÍA D02 V5.6.26 — PERSONAL, ACTIVACIÓN Y ASIGNACIÓN\nResultado: %d/%d PASS\n\n'% (passed,total) + '\n'.join(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else '') for n,ok,d in R)+'\n',encoding='utf-8')
print(f'RESUMEN D02: {passed}/{total} PASS')
raise SystemExit(0 if passed==total else 1)
