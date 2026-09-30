import json, os, sqlite3, hashlib, urllib.request, urllib.error, http.cookiejar, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent; BASE='http://127.0.0.1:8001'; DB=ROOT/'sistema_gestion_ambiental.sqlite3'
PASS=0; FAIL=0

def check(name, ok, detail=''):
    global PASS,FAIL
    print(('PASS' if ok else 'FAIL').ljust(5),name,'-',detail)
    PASS+=ok; FAIL+=not ok

jar=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def req(path, method='GET', data=None, headers=None, raw=None):
    h=headers or {}; body=raw
    if data is not None:
        body=json.dumps(data,ensure_ascii=False).encode();h['Content-Type']='application/json'
    r=urllib.request.Request(BASE+path,data=body,headers=h,method=method)
    try:
        with op.open(r,timeout=8) as x:return x.status,dict(x.headers),x.read()
    except urllib.error.HTTPError as e:return e.code,dict(e.headers),e.read()

def multipart(fields,filefield,filename,data,mime):
    boundary='----LLE'+uuid.uuid4().hex; chunks=[]
    for k,v in fields.items():chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()]
    chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="{filefield}"; filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'.encode(),data,b'\r\n',f'--{boundary}--\r\n'.encode()]
    return b''.join(chunks), 'multipart/form-data; boundary='+boundary

# login
s,_,b=req('/api/login','POST',{'username':'tecnico','password':'LLE-Tecnico-2026!'});check('Login técnico',s==200,b.decode())
s,_,b=req('/api/me'); jme=json.loads(b); check('Credenciales de prueba estables',s==200 and not jme.get('debe_cambiar',True),'No se fuerza cambio de contraseña durante desarrollo')
# draft
payload={'tipo':'RS','origen':'Inspección de oficio','distrito':'Zaragoza','tecnico_responsable':'Técnico Ambiental Distrital de Prueba','lugar':'Sitio V5.5.1','acta_objeto':'Prueba funcional','facts':[{'descripcion':'Hecho de prueba','ubicacion':'Punto 1'}]}
s,_,b=req('/api/expediente','POST',payload);j=json.loads(b);code=j.get('codigo');check('Crear borrador',s==200 and bool(code),str(j))
# gps x2
gps_ids=[]
for lat,lng in [(13.48,-89.32),(13.49,-89.33)]:
    s,_,b=req('/api/gps','POST',{'codigo':code,'lat':lat,'lng':lng,'precision_m':5.0,'altitud_m':100,'descripcion':'Punto de prueba','hecho_id':'H-001'}); gj=json.loads(b); gps_ids.append(gj.get('punto_gps',{}).get('id')); check('Registrar punto GPS',s==200 and bool(gj.get('punto_gps',{}).get('codigo')),str(gj))
# photo actual png
png=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000000020001e221bc330000000049454e44ae426082')
body,ctype=multipart({'codigo':code,'descripcion':'Fotografía de prueba','gps_point_id':str(gps_ids[0]),'hecho_id':'H-001','fecha_captura':'2026-09-08T14:00:00'},'foto','prueba.png',png,'image/png')
s,_,b=req('/api/fotografia','POST',headers={'Content-Type':ctype,'Content-Length':str(len(body))},raw=body);pj=json.loads(b);fid=pj.get('fotografia',{}).get('id');check('Guardar fotografía real',s==200 and bool(fid),str(pj))
# list
s,_,b=req('/api/evidencias/'+code);ev=json.loads(b);check('Múltiples GPS persistidos',s==200 and len(ev['puntos_gps'])==2,[x['codigo'] for x in ev['puntos_gps']]);check('Fotografía vinculada a GPS/hecho',len(ev['fotografias'])==1 and ev['fotografias'][0]['gps_point_id']==gps_ids[0] and ev['fotografias'][0]['hecho_id']=='H-001',str(ev['fotografias'][0]))
# file/hash
s,h,b=req('/api/fotografia/'+str(fid)); sha=hashlib.sha256(b).hexdigest(); db=sqlite3.connect(DB); stored=db.execute('select sha256 from fotografias where id=?',(fid,)).fetchone()[0];db.close();check('Archivo fotográfico recuperable',s==200 and b==png,str(len(b)));check('Hash SHA-256 íntegro',sha==stored,sha)
# finish and block
payload['codigo']=code;payload['_client_finalize']=True
s,_,b=req('/api/expediente','POST',payload);check('Finalizar expediente',s==200 and json.loads(b).get('status')=='INFORME_FINALIZADO_PENDIENTE_VB',b.decode())
s,_,_=req('/api/gps','POST',{'codigo':code,'lat':13,'lng':-89});check('GPS bloqueado después de finalizar',s==403)
body,ctype=multipart({'codigo':code},'foto','post.png',png,'image/png');s,_,_=req('/api/fotografia','POST',headers={'Content-Type':ctype,'Content-Length':str(len(body))},raw=body);check('Fotografía bloqueada después de finalizar',s==403)
# db integrity
c=sqlite3.connect(DB);ic=c.execute('pragma integrity_check').fetchone()[0];fk=c.execute('pragma foreign_key_check').fetchall();c.close();check('SQLite integrity_check',ic=='ok',ic);check('SQLite foreign_key_check',len(fk)==0,str(len(fk)))
print(f'\nRESULTADO: {PASS} PASS / {FAIL} FAIL')
raise SystemExit(0 if FAIL==0 else 1)
