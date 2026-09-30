import json, http.cookiejar, pathlib, re, subprocess, urllib.error, urllib.request, sqlite3
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

s=(ROOT/'server.py').read_text(encoding='utf-8'); ui1=(ROOT/'01_SISTEMA_INSPECCIONES/index.html').read_text(encoding='utf-8'); ui2=(ROOT/'02_MOTOR_SEGUIMIENTO/index.html').read_text(encoding='utf-8')
r=subprocess.run(['python','-m','py_compile',str(ROOT/'server.py')],capture_output=True,text=True); C('Python syntax',r.returncode==0,r.stderr.strip())
for f in [ROOT/'01_SISTEMA_INSPECCIONES/index.html',ROOT/'02_MOTOR_SEGUIMIENTO/index.html']:
    js='\n'.join(re.findall(r'<script>(.*?)</script>',f.read_text(encoding='utf-8'),re.S)); tmp=pathlib.Path('/tmp/'+f.parent.name+'_D05.js'); tmp.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True); C(f'{f.parent.name} JavaScript syntax',r.returncode==0,r.stderr.strip())
C('D01-D04 server controls retained', all(x in s for x in ['ACTION_TYPES','INSPECTION_MODALITIES','CORRECTION_SCOPE_KEYS','source_action','source_modality','existing_participants']))
C('Server declares complete state catalog', "VALID_STATUSES = {'RECIBIDO_PENDIENTE_ASIGNACION','ASIGNADO_A_INSPECCION','BORRADOR','INFORME_FINALIZADO_PENDIENTE_VB','DEVUELTO','VB_APROBADO','REMITIDO','FINALIZADO'}" in s)
C('Server ignores client status/actor', "o.pop('status', None); o.pop('_actor', None)" in s)
C('Review only accepts pending review', "row['status']!='INFORME_FINALIZADO_PENDIENTE_VB'" in s)
C('Remission requires validation', "row['status']!='VB_APROBADO'" in s)
C('Closure requires validation', "row['status'] not in ('VB_APROBADO','REMITIDO')" in s)
C('Technical editing blocked after review', "current not in ('ASIGNADO_A_INSPECCION','BORRADOR','DEVUELTO','RECIBIDO_PENDIENTE_ASIGNACION')" in s)
C('Dashboard exposes state progression', all(x in ui2 for x in ['INFORME_FINALIZADO_PENDIENTE_VB','VB_APROBADO','REMITIDO','FINALIZADO']))

G=op(); T=op();
st,h=req(G,'/api/health'); C('Health V5.6.26',st==200 and h.get('version')=='V5.6.26',str(h))
st,j=req(G,'/api/login','POST',{'username':'gerente','password':'LLE-Gerente-2026!'}); C('Gerente login',st==200 and j.get('rol')=='GERENTE')
st,j=req(T,'/api/login','POST',{'username':'tecnico','password':'LLE-Tecnico-2026!'}); C('Técnico login',st==200 and j.get('rol')=='TECNICO')

rec={'origen':'Solicitud de inspección','tipo':'TP','tipo_actuacion':'Verificación','modalidad_inspeccion':'CONJUNTA_TAD','fecha_recepcion':'2026-09-25','distrito':'Zaragoza','referencia_externa':'D05-001','solicitante':'D05','descripcion_inicial':'Prueba máquina de estados','prioridad':'Media'}
st,j=req(G,'/api/recepcion','POST',rec); code=j.get('codigo',''); C('Reception creates pending state',st==200 and code)
st,j=req(G,'/api/asignar','POST',{'codigo':code,'tecnico':'Técnico Ambiental Distrital de Prueba'}); C('Assignment reaches assigned state',st==200 and j.get('expediente',{}).get('status')=='ASIGNADO_A_INSPECCION')
base={'codigo':code,'tipo':'TP','origen':'Solicitud de inspección','distrito':'Zaragoza','tipo_actuacion':'Verificación','modalidad_inspeccion':'CONJUNTA_TAD','tecnico_responsable':'Técnico Ambiental Distrital de Prueba','acta_objeto':'Objeto D05','facts':[{'hecho':'Hecho D05'}]}
# Technician attempts privileged transitions directly.
for label,path,payload in [
 ('Técnico no puede revisar','/api/revision',{'codigo':code,'action':'VALIDAR','obs':'fraude'}),
 ('Técnico no puede devolver','/api/revision',{'codigo':code,'action':'DEVOLVER','obs':'fraude','scope':['acta_objeto']}),
 ('Técnico no puede remitir','/api/remision',{'codigo':code,'destino':'Institución','motivo':'fraude'}),
 ('Técnico no puede cerrar','/api/cierre',{'codigo':code,'motivo':'fraude'})]:
    st,j=req(T,path,'POST',payload); C(label,st==403,str(j))
# Save and finalize.
st,j=req(T,'/api/expediente','POST',base); C('Technical save reaches BORRADOR',st==200 and j.get('status')=='BORRADOR',str(j))
# Client attempts to force review/approval/finalized status: server must ignore.
for forced in ['VB_APROBADO','REMITIDO','FINALIZADO','INFORME_FINALIZADO_PENDIENTE_VB']:
    tampered=dict(base); tampered['status']=forced; tampered['_actor']='gerente'; tampered['_client_finalize']=False
    st,j=req(T,'/api/expediente','POST',tampered); C('Client status tamper ignored: '+forced,st==200 and j.get('status')=='BORRADOR',str(j))
# Finalize.
final=dict(base); final.update({'_client_finalize':True,'analisis':'Análisis D05','conclusions':[{'text':'Conclusión D05'}],'recommendations':[{'text':'Recomendación D05'}]})
st,j=req(T,'/api/expediente','POST',final); C('Finalize reaches review state',st==200 and j.get('status')=='INFORME_FINALIZADO_PENDIENTE_VB',str(j))
# Technician cannot edit or finalize again while pending review.
edit=dict(final); edit['_client_finalize']=False; edit['acta_objeto']='Cambio fuera de revisión'
st2,j2=req(T,'/api/expediente','POST',edit); C('Technical edit blocked in review state',st2==403,str(j2))
st2,j2=req(T,'/api/expediente','POST',final); C('Technical re-finalize blocked in review state',st2==403,str(j2))
# Manager can return.
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'DEVOLVER','obs':'Corregir objeto','scope':['acta_objeto']}); C('Manager return reaches DEVUELTO',st==200 and j.get('expediente',{}).get('status')=='DEVUELTO',str(j))
# Technician can only correct authorized field.
st,j=req(T,'/api/expediente','POST',{**final,'_client_finalize':False,'acta_objeto':'Objeto corregido D05'}); C('Authorized correction save remains DEVUELTO',st==200 and j.get('status')=='DEVUELTO',str(j))
# Re-finalize after correction.
st,j=req(T,'/api/expediente','POST',{**final,'_client_finalize':True,'acta_objeto':'Objeto corregido D05'}); C('Re-finalization returns to review',st==200 and j.get('status')=='INFORME_FINALIZADO_PENDIENTE_VB',str(j))
# Manager validates.
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'VALIDAR','obs':'Validado D05'}); C('Manager validation reaches VB_APROBADO',st==200 and j.get('expediente',{}).get('status')=='VB_APROBADO',str(j))
# Invalid review/remit/close transitions after validation.
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'VALIDAR','obs':'again'}); C('Repeated validation rejected',st==403,str(j))
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'DEVOLVER','obs':'too late','scope':['acta_objeto']}); C('Return after validation rejected',st==403,str(j))
# Remit.
st,j=req(G,'/api/remision','POST',{'codigo':code,'destino':'Institución D05','motivo':'Remisión D05'}); C('Validated case can be remitted',st==200 and j.get('expediente',{}).get('status')=='REMITIDO',str(j))
# Re-remit and review after remission must fail.
st,j=req(G,'/api/remision','POST',{'codigo':code,'destino':'Otra','motivo':'Duplicada'}); C('Repeated remission rejected',st==403,str(j))
st,j=req(G,'/api/revision','POST',{'codigo':code,'action':'VALIDAR','obs':'late'}); C('Review after remission rejected',st==403,str(j))
# Close after remission.
st,j=req(G,'/api/cierre','POST',{'codigo':code,'motivo':'Cierre D05'}); C('Remitted case can close',st==200 and j.get('expediente',{}).get('status')=='FINALIZADO',str(j))
# All post-close mutation endpoints must reject.
for label,path,payload in [
 ('Review after close','/api/revision',{'codigo':code,'action':'VALIDAR','obs':'late'}),
 ('Remit after close','/api/remision',{'codigo':code,'destino':'Otra','motivo':'late'}),
 ('Close twice','/api/cierre',{'codigo':code,'motivo':'again'})]:
    st,j=req(G,path,'POST',payload); C(label,st==403,str(j))
post=dict(base); post['_client_finalize']=False; post['acta_objeto']='Post cierre'
st,j=req(T,'/api/expediente','POST',post); C('Technical edit after close rejected',st==403,str(j))
# Inspect versions: monotonically increasing and payload status agrees with row status.
c=sqlite3.connect(ROOT/'sistema_gestion_ambiental.sqlite3'); c.row_factory=sqlite3.Row
row=c.execute('SELECT status,payload_json FROM expedientes WHERE codigo=?',(code,)).fetchone(); vers=c.execute('SELECT version,estado,payload_json FROM versiones WHERE expediente_id=(SELECT id FROM expedientes WHERE codigo=?) ORDER BY version',(code,)).fetchall(); c.close()
statuses=[json.loads(v['payload_json']).get('status') for v in vers]; nums=[v['version'] for v in vers]
C('Final DB status and payload synchronized',row['status']=='FINALIZADO' and json.loads(row['payload_json']).get('status')=='FINALIZADO')
C('Version numbers strictly monotonic',nums==list(range(1,len(nums)+1)),str(nums))
C('Version payload states match version rows',[v['estado']==json.loads(v['payload_json']).get('status') for v in vers] == [True]*len(vers),str([(v['estado'],json.loads(v['payload_json']).get('status')) for v in vers]))

passed=sum(1 for _,ok,_ in results if ok); total=len(results)
report=f'AUDITORÍA D05 V5.6.26 — MÁQUINA DE ESTADOS E INTEGRIDAD DE TRANSICIONES\nResultado: {passed}/{total} PASS\n\n'+ '\n'.join(('PASS' if ok else 'FAIL')+' | '+n+(' | '+d if d else '') for n,ok,d in results)+'\n'
(ROOT/'REPORTE_AUDITORIA_D05_V5_6_26.txt').write_text(report,encoding='utf-8')
print('RESUMEN',passed,'/',total)
raise SystemExit(0 if passed==total else 1)
