import json, http.cookiejar, pathlib, re, subprocess, urllib.error, urllib.request
BASE='http://127.0.0.1:8001'; ROOT=pathlib.Path(__file__).parent; results=[]
def op():
    cj=http.cookiejar.CookieJar(); return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def req(o,path,method='GET',data=None):
    body=json.dumps(data,ensure_ascii=False).encode() if data is not None else None
    h={'Content-Type':'application/json'} if body is not None else {}
    try:
        r=o.open(urllib.request.Request(BASE+path,data=body,headers=h,method=method),timeout=8); return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:return e.code,json.loads(e.read().decode())
        except:return e.code,{}
def C(name,ok,detail=''):
    results.append((name,ok,detail)); print(('PASS' if ok else 'FAIL')+' | '+name+(' | '+detail if detail else ''))

# Static regressions
r=subprocess.run(['python','-m','py_compile',str(ROOT/'server.py')],capture_output=True,text=True); C('Python syntax',r.returncode==0,r.stderr.strip())
for f in [ROOT/'01_SISTEMA_INSPECCIONES/index.html',ROOT/'02_MOTOR_SEGUIMIENTO/index.html']:
    js='\n'.join(re.findall(r'<script>(.*?)</script>',f.read_text(encoding='utf-8'),re.S)); tmp=pathlib.Path('/tmp/'+f.parent.name+'_D04.js'); tmp.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True); C(f'{f.parent.name} JavaScript syntax',r.returncode==0,r.stderr.strip())
s=(ROOT/'server.py').read_text(encoding='utf-8'); ui1=(ROOT/'01_SISTEMA_INSPECCIONES/index.html').read_text(encoding='utf-8'); ui2=(ROOT/'02_MOTOR_SEGUIMIENTO/index.html').read_text(encoding='utf-8')
C('D01 catalog validation retained','ACTION_TYPES' in s and 'INSPECTION_MODALITIES' in s and 'tipo_actuacion no válido' not in s)
C('D02 personnel manager-only retained',"Solo el Gerente Ambiental puede gestionar el personal técnico." in s)
C('D03 historical participant rule retained','name not in existing_participants' in s)
C('Reception action/modality server catalogs retained',"tipo_actuacion not in ACTION_TYPES" in s and "modalidad not in INSPECTION_MODALITIES" in s)
C('Technical source action immutable', 'source_action=' in s and 'tipo_actuacion!=source_action' in s)
C('Technical source modality immutable', 'source_modality=' in s and 'modalidad!=source_modality' in s)
C('Correction scope has server whitelist','CORRECTION_SCOPE_KEYS' in s and 'invalid=sorted(set(scope)-CORRECTION_SCOPE_KEYS)' in s)
C('Acta action field remains reception-controlled UI','id="acta_tipo_actuacion"' in ui1 and 'disabled' in ui1[ui1.find('id="acta_tipo_actuacion"')-100:ui1.find('id="acta_tipo_actuacion"')+500])
C('Dashboard scope catalog present','const SCOPE=' in ui2)

G=op(); T=op(); st,h=req(G,'/api/health'); C('Health V5.6.26',st==200 and h.get('version')=='V5.6.26',str(h))
st,j=req(G,'/api/login','POST',{'username':'gerente','password':'LLE-Gerente-2026!'}); C('Gerente login',st==200 and j.get('rol')=='GERENTE')
st,j=req(T,'/api/login','POST',{'username':'tecnico','password':'LLE-Tecnico-2026!'}); C('Técnico login',st==200 and j.get('rol')=='TECNICO')
st,_=req(G,'/api/cambiar-password','POST',{'password_actual':'LLE-Gerente-2026!','password_nueva':'LLE-D04-Gerente-2026!'}); C('Gerente initial password change',st==200)
st,_=req(T,'/api/cambiar-password','POST',{'password_actual':'LLE-Tecnico-2026!','password_nueva':'LLE-D04-Tecnico-2026!'}); C('Técnico initial password change',st==200)

rec={'origen':'Solicitud de inspección','tipo':'TP','tipo_actuacion':'Verificación','modalidad_inspeccion':'CONJUNTA_TAD','fecha_recepcion':'2026-09-25','distrito':'Zaragoza','referencia_externa':'D04-001','solicitante':'D04','descripcion_inicial':'Prueba integridad maestro','prioridad':'Media'}
st,j=req(G,'/api/recepcion','POST',rec); code=j.get('codigo',''); C('Reception stores non-default action/modality',st==200 and code.startswith('AMB-LLE-2026-'))
st,j=req(G,'/api/expediente/'+code); e=j.get('expediente',{}) if isinstance(j,dict) else {}; C('Reception values persisted',st==200 and e.get('tipo_actuacion')=='Verificación' and e.get('modalidad_inspeccion')=='CONJUNTA_TAD')
st,j=req(G,'/api/asignar','POST',{'codigo':code,'tecnico':'Técnico Ambiental Distrital de Prueba'}); C('Gerente assigns case',st==200 and j.get('expediente',{}).get('status')=='ASIGNADO_A_INSPECCION')
base={'codigo':code,'tipo':'TP','origen':'Solicitud de inspección','distrito':'Zaragoza','tipo_actuacion':'Verificación','modalidad_inspeccion':'CONJUNTA_TAD','tecnico_responsable':'Técnico Ambiental Distrital de Prueba','acta_objeto':'Objeto original D04','facts':[{'hecho':'Hecho D04'}]}
st,j=req(T,'/api/expediente','POST',base); C('Technical save with source values',st==200 and j.get('status')=='BORRADOR',str(j))
for label,mut in [('action',{'tipo_actuacion':'De oficio','acta_tipo_actuacion':'De oficio'}),('modality',{'modalidad_inspeccion':'INTERINSTITUCIONAL'}),('action+modality',{'tipo_actuacion':'A solicitud','acta_tipo_actuacion':'A solicitud','modalidad_inspeccion':'CONJUNTA_MUNICIPAL'})]:
 bad=dict(base); bad.update(mut); st,j=req(T,'/api/expediente','POST',bad); C('Mutation rejected: '+label,st==400 and ('tipo de actuación' in j.get('error','').lower() or 'modalidad' in j.get('error','').lower()),str(j))

# Finish and exercise review correction scope security.
final=dict(base); final.update({'_client_finalize':True,'analisis':'Análisis D04','conclusions':[{'text':'Conclusión D04'}],'recommendations':[{'text':'Recomendación D04'}]})
st,j=req(T,'/api/expediente','POST',final); C('Technical finalization reaches review state',st==200 and j.get('status')=='INFORME_FINALIZADO_PENDIENTE_VB')
# Invalid scope must be rejected while the case is still in review.
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'DEVOLVER','obs':'Invalid scope','scope':['acta_objeto','NO_AUTORIZADO']}); C('Invalid correction scope rejected',st==400 and 'no autorizados' in j.get('error','').lower(),str(j))
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'DEVOLVER','obs':'Corregir objeto','scope':['acta_objeto','acta_objeto']}); C('Gerente can return with valid correction scope',st==200 and j.get('expediente',{}).get('status')=='DEVUELTO')
st,j=req(G,'/api/expediente/'+code); returned=j.get('expediente',{}) if isinstance(j,dict) else {}; C('Correction scope persisted normalized',st==200 and returned.get('_correction_scope')==['acta_objeto'])
# Technician must submit the complete current payload; only the authorized field may differ.
correct=dict(returned); correct['acta_objeto']='Objeto corregido D04'; correct.pop('status',None); correct['_client_finalize']=False
st,j=req(T,'/api/expediente','POST',correct); C('Authorized correction accepted',st==200 and j.get('status')=='DEVUELTO',str(j))
unauth=dict(correct); unauth['analisis']='Cambio no autorizado D04'; st,j=req(T,'/api/expediente','POST',unauth); C('Unauthorized correction field rejected',st==403 and 'campos no autorizados' in j.get('error','').lower(),str(j))
# Re-finalize after authorized correction using the latest persisted payload.
st,j=req(T,'/api/expediente/'+code); latest=j.get('expediente',{}) if isinstance(j,dict) else {}; refinal=dict(latest); refinal.pop('status',None); refinal['_client_finalize']=True; refinal['analisis']='Análisis D04'; refinal['conclusions']=[{'text':'Conclusión D04'}]; refinal['recommendations']=[{'text':'Recomendación D04'}]
st,j=req(T,'/api/expediente','POST',refinal); C('Corrected case can be finalized',st==200 and j.get('status')=='INFORME_FINALIZADO_PENDIENTE_VB',str(j))
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'VALIDAR','obs':'Validación D04'}); C('Gerente can validate corrected report',st==200 and j.get('expediente',{}).get('status')=='VB_APROBADO',str(j))

passed=sum(1 for _,ok,_ in results if ok); total=len(results); report=f'AUDITORÍA D04 V5.6.26 — INTEGRIDAD DEL ACTA MAESTRO Y DEVOLUCIÓN\nResultado: {passed}/{total} PASS\n\n'+ '\n'.join(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else '') for n,ok,d in results)+'\n'; (ROOT/'REPORTE_AUDITORIA_D04_V5_6_26.txt').write_text(report,encoding='utf-8'); print('RESUMEN',passed,'/',total); raise SystemExit(0 if passed==total else 1)
