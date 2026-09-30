import urllib.request, urllib.error, urllib.parse, json, http.cookiejar, os, re, subprocess, pathlib, time
BASE='http://127.0.0.1:18082'
ROOT=pathlib.Path(__file__).parent

def browser():
    cj=http.cookiejar.CookieJar(); return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def req(op,path,method='GET',data=None):
    body=json.dumps(data).encode() if data is not None else None
    h={'Content-Type':'application/json'} if body is not None else {}
    try:
        r=op.open(urllib.request.Request(BASE+path,data=body,headers=h,method=method),timeout=8)
        raw=r.read().decode(); return r.status,json.loads(raw)
    except urllib.error.HTTPError as e:
        raw=e.read().decode()
        try:j=json.loads(raw)
        except:j={'raw':raw}
        return e.code,j

def login(user,pw):
    op=browser(); st,j=req(op,'/api/login','POST',{'username':user,'password':pw}); return op,st,j

results=[]
def T(name, ok, detail=''):
    results.append((name,bool(ok),detail)); print(('PASS' if ok else 'FAIL')+' | '+name+(' | '+detail if detail else ''))

# static syntax
sp=ROOT/'server.py'; r=subprocess.run(['python','-m','py_compile',str(sp)],capture_output=True,text=True); T('Python syntax',r.returncode==0,r.stderr.strip())
for f in [ROOT/'01_SISTEMA_INSPECCIONES/index.html',ROOT/'02_MOTOR_SEGUIMIENTO/index.html']:
    import re
    s=f.read_text(encoding='utf-8'); js='\n'.join(re.findall(r'<script>(.*?)</script>',s,re.S))
    tmp=pathlib.Path('/tmp/'+f.parent.name+'.js'); tmp.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True)
    T(f'{f.parent.name} JavaScript syntax',r.returncode==0,r.stderr.strip())

m,st,j=login('gerente','LLE-Gerente-2026!'); T('Gerente login',st==200)
t,st,j=login('tecnico','LLE-Tecnico-2026!'); T('Técnico login',st==200)

# All catalog components: reception persists exact type and report code derives exact type after assignment/save
components={'OI':'Otros componentes ambientales','RS':'Residuos sólidos','VH':'Vertidos / descargas','RH':'Recursos hídricos','AU':'Arbolado urbano','TP':'Tala / poda','CO':'Contaminación ambiental','CR':'Ruido','CS':'Suelo','EP':'Espacios públicos / áreas verdes','ZR':'Zonas de protección','MT':'Movimientos de tierra','GR':'Gestión de riesgo'}
for code,name in components.items():
    payload={'origen':'Solicitud de inspección','tipo':code,'materias_adicionales':[],'fecha_recepcion':'2026-09-09','referencia_externa':f'TEST-{code}','institucion_solicitante':'','solicitante':f'Solicitante {code}','condicion':'Persona natural','contacto':'','prioridad':'Media','distrito':'Zaragoza','descripcion_inicial':f'Prueba de componente {name}.'}
    st,j=req(m,'/api/recepcion','POST',payload)
    ok=st==200 and bool(j.get('codigo'))
    if not ok: T(f'Recepción {code}',False,str(j)); continue
    expcode=j['codigo']
    st,j=req(m,'/api/asignar','POST',{'codigo':expcode,'tecnico':'Técnico Ambiental Distrital de Prueba','observacion':f'Auditoría {code}'})
    ok=st==200 and j.get('expediente',{}).get('tipo')==code
    T(f'Asignación conserva {code}',ok,str(j.get('expediente',{}).get('tipo')))
    st,j=req(t,'/api/expediente/'+urllib.parse.quote(expcode,safe=''))
    e=j.get('expediente',{})
    ok=st==200 and e.get('tipo')==code and e.get('codigo_acta')==f'ACTA-{code}-2026-{int(expcode.rsplit("-",1)[1]):04d}' and e.get('codigo_informe')==f'INF-{code}-2026-{int(expcode.rsplit("-",1)[1]):04d}'
    T(f'Técnico recibe {code} + códigos derivados',ok,f"tipo={e.get('tipo')} acta={e.get('codigo_acta')} informe={e.get('codigo_informe')}")

# Dedicated mismatch attack using a new TP case
st,j=req(m,'/api/recepcion','POST',{'origen':'Solicitud de inspección','tipo':'TP','materias_adicionales':[],'fecha_recepcion':'2026-09-09','referencia_externa':'TEST-MISMATCH','institucion_solicitante':'','solicitante':'Prueba Tala','condicion':'Persona natural','contacto':'','prioridad':'Alta','distrito':'Nuevo Cuscatlán','descripcion_inicial':'Solicitud de tala.'})
code=j.get('codigo')
req(m,'/api/asignar','POST',{'codigo':code,'tecnico':'Técnico Ambiental Distrital de Prueba','observacion':'Mismatch'})
st,j=req(t,'/api/expediente/'+urllib.parse.quote(code,safe='')); e=j.get('expediente',{})
base=dict(e); base.update({'tipo':'RS','materia_principal':'RS','materias':['RS'],'materias_adicionales':[],'tecnico_responsable':'Técnico Ambiental Distrital de Prueba','distrito':'Nuevo Cuscatlán','origen':'Solicitud de inspección','acta_fecha':'2026-09-09','acta_hora_inicio':'08:00','acta_tipo_actuacion':'Inspección','acta_objeto':'Prueba','acta_alcance':'Prueba','fecha_elaboracion':'2026-09-09','objeto_informe':'Prueba','metodologia':'Inspección','alcance_inf':'Prueba'})
st,j2=req(t,'/api/expediente','POST',base); T('Servidor rechaza TP→RS',st==400,'status=%s error=%s'%(st,j2.get('error')))
# Proper TP save
base['tipo']='TP'; base['materia_principal']='TP'; base['materias']=['TP']
st,j3=req(t,'/api/expediente','POST',base); T('Guardado TP coherente',st==200,str(j3))
st,j=req(t,'/api/expediente/'+urllib.parse.quote(code,safe='')); e=j.get('expediente',{})
T('Persistencia mantiene TP',e.get('tipo')=='TP' and str(e.get('codigo_informe','')).startswith('INF-TP-'),str((e.get('tipo'),e.get('codigo_informe'))))

# Origin mismatch also rejected
bad=dict(base); bad['origen']='Denuncia ambiental'
st,j2=req(t,'/api/expediente','POST',bad); T('Servidor rechaza cambio de origen',st==400,str(j2))

# Static consistency checks
s1=(ROOT/'01_SISTEMA_INSPECCIONES/index.html').read_text(encoding='utf-8')
s2=(ROOT/'02_MOTOR_SEGUIMIENTO/index.html').read_text(encoding='utf-8')
T('Componente técnico es solo lectura', '<select id="tipo" disabled>' in s1)
T('Acta muestra componente en solo lectura', 'id="acta_materia_principal" readonly' in s1)
T('Informe muestra tipo en solo lectura', 'id="tipo_informe" readonly' in s1)
T('Recepción exige componente', 'id="recTipo"' in s2 and 'Seleccione el componente principal' in s2)
T('MT incluido en informe', "MT:'Movimientos de tierra'" in s1)
T('Scope no ofrece origen para corrección', "['origen','Origen']" not in s2)
T('Scope no ofrece técnico responsable para corrección', "['tecnico_responsable','Técnico responsable']" not in s2)

passed=sum(ok for _,ok,_ in results); total=len(results)
report=ROOT/'REPORTE_AUDITORIA_CONSISTENCIA_V5_6_9.txt'
report.write_text(f'AUDITORÍA V5.6.9 — CONSISTENCIA DE COMPONENTES\nResultado: {passed}/{total} PASS\n\n'+'\n'.join(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else '') for n,ok,d in results)+'\n',encoding='utf-8')
print(f'RESUMEN {passed}/{total} PASS')
raise SystemExit(0 if passed==total else 1)
