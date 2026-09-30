import urllib.request, urllib.error, urllib.parse, json, http.cookiejar, pathlib, re, subprocess
BASE='http://127.0.0.1:18082'; ROOT=pathlib.Path(__file__).parent

def op():
    cj=http.cookiejar.CookieJar(); return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def req(o,path,method='GET',data=None):
    body=json.dumps(data).encode() if data is not None else None
    headers={'Content-Type':'application/json'} if body is not None else {}
    try:
        r=o.open(urllib.request.Request(BASE+path,data=body,headers=headers,method=method),timeout=8)
        return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code,json.loads(e.read().decode())
def T(n,ok,d=''): print(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else ''))

results=[]
def C(n,ok,d=''): results.append((n,ok,d)); T(n,ok,d)

r=subprocess.run(['python','-m','py_compile',str(ROOT/'server.py')],capture_output=True,text=True); C('Python syntax',r.returncode==0,r.stderr.strip())
for f in [ROOT/'01_SISTEMA_INSPECCIONES/index.html',ROOT/'02_MOTOR_SEGUIMIENTO/index.html']:
    js='\n'.join(re.findall(r'<script>(.*?)</script>',f.read_text(encoding='utf-8'),re.S)); tmp=pathlib.Path('/tmp/'+f.parent.name+'_D01.js'); tmp.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True); C(f'{f.parent.name} JavaScript syntax',r.returncode==0,r.stderr.strip())

o=op(); st,h=req(o,'/api/health'); C('Health V5.6.26',st==200 and h.get('version')=='V5.6.26',str(h))
st,j=req(o,'/api/login','POST',{'username':'gerente','password':'LLE-Gerente-2026!'}); C('Gerente login',st==200)

districts=['Antiguo Cuscatlán','Huizúcar','Nuevo Cuscatlán','San José Villanueva','Zaragoza']
actions=['Inspección','Visita técnica','Verificación','Seguimiento','De oficio','A solicitud','Interinstitucional','Otra']
mods=['INDIVIDUAL','CONJUNTA_TAD','CONJUNTA_MUNICIPAL','INTERINSTITUCIONAL']
for i,d in enumerate(districts):
    p={'origen':'Solicitud de inspección','tipo':'OI','tipo_actuacion':actions[i],'modalidad_inspeccion':mods[i%4],'fecha_recepcion':'2026-09-25','distrito':d,'referencia_externa':f'D01-D-{i}','solicitante':'D01','descripcion_inicial':'Prueba','prioridad':'Media'}
    st,j=req(o,'/api/recepcion','POST',p); C('Distrito '+d,st==200,str(j))
for i,a in enumerate(actions):
    p={'origen':'Solicitud de inspección','tipo':'OI','tipo_actuacion':a,'modalidad_inspeccion':'INDIVIDUAL','fecha_recepcion':'2026-09-25','distrito':'Zaragoza','referencia_externa':f'D01-A-{i}','solicitante':'D01','descripcion_inicial':'Prueba','prioridad':'Media'}
    st,j=req(o,'/api/recepcion','POST',p); C('Tipo actuación '+a,st==200,str(j))
for i,m in enumerate(mods):
    p={'origen':'Solicitud de inspección','tipo':'OI','tipo_actuacion':'Inspección','modalidad_inspeccion':m,'fecha_recepcion':'2026-09-25','distrito':'Zaragoza','referencia_externa':f'D01-M-{i}','solicitante':'D01','descripcion_inicial':'Prueba','prioridad':'Media'}
    st,j=req(o,'/api/recepcion','POST',p); C('Modalidad '+m,st==200,str(j))
for field,val in [('origen','INVALIDO'),('distrito','Distrito inexistente'),('tipo_actuacion','INVALIDO'),('modalidad_inspeccion','INVALIDO')]:
    p={'origen':'Solicitud de inspección','tipo':'OI','tipo_actuacion':'Inspección','modalidad_inspeccion':'INDIVIDUAL','fecha_recepcion':'2026-09-25','distrito':'Zaragoza','referencia_externa':'D01-X-'+field,'solicitante':'D01','descripcion_inicial':'Prueba','prioridad':'Media'}; p[field]=val
    st,j=req(o,'/api/recepcion','POST',p); C('Rechazo '+field,st==400,str(j))

s1=(ROOT/'01_SISTEMA_INSPECCIONES/index.html').read_text(encoding='utf-8'); s2=(ROOT/'02_MOTOR_SEGUIMIENTO/index.html').read_text(encoding='utf-8')
C('Acta type catalog unified', all(x in s1 for x in actions))
C('Acta type is reception-controlled', '<select id="acta_tipo_actuacion" disabled>' in s1)
C('Monitor reception has type catalog', 'id="recTipoActuacion"' in s2 and all(x in s2 for x in actions))
C('San José Villanueva canonical in UI', 'San José Villanueva' in s1 and 'San José Villanueva' in s2)
C('No obsolete split district label', 'San José</option><option>Villanueva' not in s1+s2)

passed=sum(1 for _,ok,_ in results if ok); total=len(results)
(ROOT/'REPORTE_AUDITORIA_D01_V5_6_26.txt').write_text(f'AUDITORÍA D01 V5.6.26 — CATÁLOGOS PC → API → SQLITE\nResultado: {passed}/{total} PASS\n\n'+'\n'.join(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else '') for n,ok,d in results)+'\n',encoding='utf-8')
print(f'RESUMEN {passed}/{total} PASS')
raise SystemExit(0 if passed==total else 1)
