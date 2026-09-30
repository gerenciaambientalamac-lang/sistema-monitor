import json, http.cookiejar, pathlib, re, subprocess, urllib.error, urllib.request

BASE='http://127.0.0.1:8001'
ROOT=pathlib.Path(__file__).parent

def op():
    cj=http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def req(o,path,method='GET',data=None):
    body=json.dumps(data,ensure_ascii=False).encode() if data is not None else None
    headers={'Content-Type':'application/json'} if body is not None else {}
    try:
        r=o.open(urllib.request.Request(BASE+path,data=body,headers=headers,method=method),timeout=8)
        return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:return e.code,json.loads(e.read().decode())
        except:return e.code,{}

def C(name,ok,detail=''):
    results.append((name,ok,detail))
    print(('PASS' if ok else 'FAIL')+' | '+name+(' | '+detail if detail else ''))

results=[]
# Static
r=subprocess.run(['python','-m','py_compile',str(ROOT/'server.py')],capture_output=True,text=True)
C('Python syntax',r.returncode==0,r.stderr.strip())
for f in [ROOT/'01_SISTEMA_INSPECCIONES/index.html',ROOT/'02_MOTOR_SEGUIMIENTO/index.html']:
    js='\n'.join(re.findall(r'<script>(.*?)</script>',f.read_text(encoding='utf-8'),re.S))
    tmp=pathlib.Path('/tmp/'+f.parent.name+'_D03.js'); tmp.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True)
    C(f'{f.parent.name} JavaScript syntax',r.returncode==0,r.stderr.strip())

s= (ROOT/'server.py').read_text(encoding='utf-8')
ui1=(ROOT/'01_SISTEMA_INSPECCIONES/index.html').read_text(encoding='utf-8')
ui2=(ROOT/'02_MOTOR_SEGUIMIENTO/index.html').read_text(encoding='utf-8')
C('Historical inactive participant rule present', 'existing_participants=set()' in s and 'name not in existing_participants' in s)
C('Assignment remains Gerente-only', "if user['rol']!='GERENTE': raise PermissionError('Solo el Gerente Ambiental puede asignar actuaciones a técnicos.')" in s)
C('Technical module keeps source district immutable', 'El distrito de la actuación no coincide con el registrado en la recepción' in s)

# API
G=op(); T=op()
st,h=req(G,'/api/health'); C('Health V5.6.26',st==200 and h.get('version')=='V5.6.26',str(h))
st,j=req(G,'/api/login','POST',{'username':'gerente','password':'LLE-Gerente-2026!'}); C('Gerente login',st==200 and j.get('rol')=='GERENTE')
st,j=req(T,'/api/login','POST',{'username':'tecnico','password':'LLE-Tecnico-2026!'}); C('Técnico login',st==200 and j.get('rol')=='TECNICO')
# Unlock initial passwords for both sessions.
st,_=req(G,'/api/cambiar-password','POST',{'password_actual':'LLE-Gerente-2026!','password_nueva':'LLE-D03-Gerente-2026!'})
C('Gerente initial password change',st==200)
st,_=req(T,'/api/cambiar-password','POST',{'password_actual':'LLE-Tecnico-2026!','password_nueva':'LLE-D03-Tecnico-2026!'})
C('Técnico initial password change',st==200)

# Personnel
for n in ['D03 Participante Activo','D03 Participante Dos']:
    st,j=req(G,'/api/personal','POST',{'nombre':n,'cargo':'Técnico Ambiental Distrital'})
    C('Alta '+n,st==200,str(j))
st,pers=req(G,'/api/personal'); C('Personnel catalog contains D03 participants',st==200 and any(x['nombre']=='D03 Participante Activo' and x['activo'] for x in pers))

# Reception and assignment
rec={'origen':'Solicitud de inspección','tipo':'OI','tipo_actuacion':'Inspección','modalidad_inspeccion':'INDIVIDUAL','fecha_recepcion':'2026-09-25','distrito':'Zaragoza','referencia_externa':'D03-001','solicitante':'D03','descripcion_inicial':'Prueba de asignación y participantes','prioridad':'Media'}
st,j=req(G,'/api/recepcion','POST',rec); code=j.get('codigo',''); C('Reception created pending assignment',st==200 and code.startswith('AMB-LLE-2026-'))
st,j=req(G,'/api/asignar','POST',{'codigo':code,'tecnico':'Técnico Ambiental Distrital de Prueba','observacion':'Asignación D03'})
exp=j.get('expediente',{}) if isinstance(j,dict) else {}
C('Gerente assigns active technician',st==200 and exp.get('status')=='ASIGNADO_A_INSPECCION')
st,j=req(G,'/api/asignaciones/'+code); hist=j.get('asignaciones',[]) if isinstance(j,dict) else []
C('Assignment history persisted',st==200 and len(hist)==1 and hist[0].get('tecnico')=='Técnico Ambiental Distrital de Prueba')
st,j=req(T,'/api/notificaciones'); ns=j.get('notificaciones',[]) if isinstance(j,dict) else []
C('Technician receives assignment notification',st==200 and any(n.get('accion')=='ABRIR_ACTUACION' and n.get('expediente_codigo')==code for n in ns))
st,j=req(T,'/api/expedientes'); C('Technician sees assigned case',st==200 and any(x.get('codigo')==code and x.get('status')=='ASIGNADO_A_INSPECCION' for x in j))

base={'codigo':code,'tipo':'OI','origen':'Solicitud de inspección','distrito':'Zaragoza','tipo_actuacion':'Inspección','modalidad_inspeccion':'INDIVIDUAL','tecnico_responsable':'Técnico Ambiental Distrital de Prueba','tecnicos_participantes':['D03 Participante Activo'],'facts':[{'hecho':'Hecho D03'}]}
st,j=req(T,'/api/expediente','POST',base); C('Technical save with active participant',st==200 and j.get('status')=='BORRADOR')
st,j=req(T,'/api/expediente/'+code); loaded=j.get('expediente',{}) if isinstance(j,dict) else {}
C('Participant persisted in expediente',st==200 and 'D03 Participante Activo' in loaded.get('tecnicos_participantes',[]))

# Deactivate participant and preserve historical participation.
st,pers=req(G,'/api/personal'); pid=next(x['id'] for x in pers if x['nombre']=='D03 Participante Activo')
st,j=req(G,'/api/personal/status','POST',{'id':pid,'activo':False}); C('Participant deactivated by Gerente',st==200)
st,j=req(T,'/api/expediente','POST',base); C('Historical inactive participant can remain on edit',st==200 and j.get('status')=='BORRADOR',str(j))
st,j=req(T,'/api/expediente/'+code); loaded=j.get('expediente',{}) if isinstance(j,dict) else {}
C('Historical inactive participant remains persisted',st==200 and 'D03 Participante Activo' in loaded.get('tecnicos_participantes',[]))

# New case: inactive participant must not be newly added.
rec2=dict(rec); rec2['referencia_externa']='D03-002'; rec2['descripcion_inicial']='Prueba rechazo participante inactivo'
st,j=req(G,'/api/recepcion','POST',rec2); code2=j.get('codigo',''); C('Second reception created',st==200)
st,j=req(G,'/api/asignar','POST',{'codigo':code2,'tecnico':'Técnico Ambiental Distrital de Prueba'}); C('Second case assigned',st==200)
bad=dict(base); bad.update({'codigo':code2,'tecnicos_participantes':['D03 Participante Activo']})
st,j=req(T,'/api/expediente','POST',bad); C('Inactive participant rejected when newly introduced',st==400 and 'inactivo' in j.get('error','').lower(),str(j))

# Security and source-of-truth tests.
st,j=req(T,'/api/asignar','POST',{'codigo':code2,'tecnico':'Técnico Ambiental Distrital de Prueba'}); C('Technician cannot assign cases',st==403,str(j))
bad=dict(base); bad['distrito']='Huizúcar'; st,j=req(T,'/api/expediente','POST',bad); C('District mutation rejected',st==400 and 'distrito' in j.get('error','').lower())
bad=dict(base); bad['origen']='Oficio'; st,j=req(T,'/api/expediente','POST',bad); C('Origin mutation rejected',st==400 and 'origen' in j.get('error','').lower())
bad=dict(base); bad['tipo']='RS'; st,j=req(T,'/api/expediente','POST',bad); C('Component mutation rejected',st==400 and 'componente' in j.get('error','').lower())

# Finish first case and verify server-owned state/version.
final=dict(base); final.update({'_client_finalize':True,'acta_objeto':'Objeto D03','analisis':'Análisis D03','conclusions':[{'text':'Conclusión D03'}],'recommendations':[{'text':'Recomendación D03'}]})
st,j=req(T,'/api/expediente','POST',final); C('Technical finalization reaches review state',st==200 and j.get('status')=='INFORME_FINALIZADO_PENDIENTE_VB')
st,j=req(G,'/api/expediente/'+code); loaded=j.get('expediente',{}) if isinstance(j,dict) else {}
C('Payload status synchronized with server status',st==200 and loaded.get('status')=='INFORME_FINALIZADO_PENDIENTE_VB')
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'VALIDAR','obs':'Validación D03'}); C('Gerente can validate finalized report',st==200 and j.get('expediente',{}).get('status')=='VB_APROBADO')
st,j=req(T,'/api/revision','POST',{'codigo':code,'action':'VALIDAR','obs':'No autorizado'}); C('Technician cannot validate',st==403)

passed=sum(1 for _,ok,_ in results if ok); total=len(results)
report='AUDITORÍA D03 V5.6.26 — PARTICIPANTES E INTEGRIDAD DE ASIGNACIÓN\nResultado: %d/%d PASS\n\n'% (passed,total)
report+='\n'.join(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else '') for n,ok,d in results)+'\n'
(ROOT/'REPORTE_AUDITORIA_D03_V5_6_26.txt').write_text(report,encoding='utf-8')
print('RESUMEN',passed,'/',total)
raise SystemExit(0 if passed==total else 1)
