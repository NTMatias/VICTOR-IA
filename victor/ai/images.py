"""Official image APIs in a disposable worker; only verified images enter history."""
import base64
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid
from PIL import Image
from victor.errors import VictorError,check_cancel

MODELS={'OpenAI':'gpt-image-2.5-sunburst','Gemini':'gemini-nano-banana-2.1'}


def image_capability_question(text):
    import unicodedata
    folded=''.join(c for c in unicodedata.normalize('NFD',str(text).casefold()) if unicodedata.category(c)!='Mn')
    return bool(re.search(r'\b(?:puedes|puede victor|eres capaz de)\s+(?:generar|crear|hacer|dibujar)\s+(?:(?:una?|las?)\s+)?(?:imagenes?|fotos?|dibujos?)\s*[?¿.! ]*$',folded))


def wants_image(text):
    import unicodedata
    folded=''.join(c for c in unicodedata.normalize('NFD',str(text).casefold()) if unicodedata.category(c)!='Mn').strip(' ¿¡')
    folded=re.sub(r'^victor[,.]?\s+','',folded)
    prefix=r'(?:(?:por favor[, ]*|puedes\s+|podrias\s+|quiero (?:que\s+)?|quisiera (?:que\s+)?|necesito (?:que\s+)?|me\s+)*)'
    return bool(re.match(prefix+r'(?:dibuja(?:me)?\b|dibujar(?:me)?\b|(?:crea(?:me)?|crees|genera(?:me)?|generes|generar|crear|haz(?:me)?)\s+(?:(?:una?|la|otra|esta)\s+)?(?:imagen|foto|ilustracion|dibujo|caratula|poster|logo|retrato)\b)',folded))


def api_error(exc,provider=None):
    status=next((v for v in (getattr(exc,'status_code',None),getattr(exc,'code',None),getattr(getattr(exc,'response',None),'status_code',None)) if isinstance(v,int)),None)
    if status in (401,403):return 'La clave API no tiene acceso a imágenes o no está autorizada. Revisa la clave y los permisos del proveedor.'
    if status==402:return 'El proveedor necesita saldo o facturación de API para generar imágenes. Revisa la cuenta de facturación del proyecto y sus créditos.'
    if status==429:
        if provider=='Gemini':return 'Gemini rechazó la imagen por cuota de API (429). Revisa la cuota y la facturación del proyecto en Google AI Studio: la API de imágenes no tiene nivel gratuito. También puedes elegir OpenAI con su propia clave y cuota. No se cambió de proveedor automáticamente.'
        return 'Se alcanzó la cuota de imágenes o el saldo de API. No se cambió de proveedor.'
    if status==404:return 'El modelo de imágenes no está disponible para esta cuenta. Elige otro modelo en el selector.'
    if status==400:return 'El proveedor rechazó el modelo, la descripción o los parámetros de imagen. Revisa la solicitud.'
    if status and status>=500:return 'El servicio de imágenes está fallando temporalmente. Inténtalo más tarde.'
    return 'No se pudo completar la generación de imagen. Revisa Internet y la conexión del proveedor.'


def openai_image(payload):
    from openai import OpenAI
    with OpenAI(api_key=payload['key'],timeout=180,max_retries=0) as client:
        result=client.images.generate(model=payload['model'],prompt=payload['prompt'],n=1,size='1024x1024',
                                      quality='medium',output_format='png')
        if not result.data or not result.data[0].b64_json:raise VictorError('OpenAI no devolvió una imagen completa.')
        return base64.b64decode(result.data[0].b64_json,validate=True)


def gemini_image(payload):
    import requests
    model=payload['model']
    if model=='gemini-nano-banana-2.1':
        endpoint='https://generativelanguage.googleapis.com/v1beta/interactions'
        body={'model':model,'input':[{'type':'text','text':payload['prompt']}],'store':False}
    else:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,150}',model):raise VictorError('Modelo Gemini no válido.')
        endpoint='https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent'
        body={'contents':[{'role':'user','parts':[{'text':payload['prompt']}]}],
              'generationConfig':{'responseModalities':['TEXT','IMAGE']}}
    with requests.post(endpoint,headers={'x-goog-api-key':payload['key']},json=body,timeout=(10,180)) as response:
        response.raise_for_status();data=response.json()
    images=[]
    if model=='gemini-nano-banana-2.1':
        if data.get('status','completed').lower()!='completed':raise VictorError('Gemini no completó la imagen.')
        final=data.get('output_image') or data.get('outputImage')
        if isinstance(final,dict):images.append(final)
        images.extend(part for part in data.get('outputs',[]) if part.get('type')=='image')
        # REST returns model_output steps; output_image is an SDK convenience.
        for step in data.get('steps',[]):
            if step.get('type')=='model_output':
                images.extend(part for part in step.get('content',[]) if part.get('type')=='image' and not part.get('thought'))
    else:
        for candidate in data.get('candidates',[]):
            if candidate.get('finishReason') not in (None,'STOP'):continue
            for part in (candidate.get('content') or {}).get('parts',[]):
                if not part.get('thought') and part.get('inlineData'):images.append(part['inlineData'])
    for image in images:
        mime=image.get('mime_type') or image.get('mimeType') or 'image/png'
        if mime in ('image/png','image/jpeg','image/webp') and image.get('data'):
            return base64.b64decode(image['data'],validate=True)
    raise VictorError('Gemini no devolvió una imagen final. Puede haber rechazado la solicitud; cambia la descripción.')


def normalize_image(blob,path):
    if not blob or len(blob)>40_000_000:raise VictorError('La imagen recibida es demasiado grande o está vacía.')
    with Image.open(io.BytesIO(blob)) as picture:
        if picture.format not in ('PNG','JPEG','WEBP') or picture.width*picture.height>32_000_000:raise VictorError('El proveedor devolvió un formato de imagen no compatible.')
        picture.load();picture.convert('RGBA').save(path,'PNG')
        return {'width':picture.width,'height':picture.height}


class ImageArchive:
    def __init__(self,config,database):
        self.config=config;self.db=database;self.directory=config.data_dir/'generated_images';self.directory.mkdir(exist_ok=True)
        with self.db.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS image_attachments(message_id INTEGER PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,file TEXT NOT NULL,provider TEXT NOT NULL,model TEXT NOT NULL,width INTEGER,height INTEGER)')
    def store(self,conversation,path,provider,model,dimensions):
        filename=path.name
        if not re.fullmatch(r'[0-9a-f]{32}\.png',filename) or path.resolve().parent!=self.directory.resolve():raise VictorError('Ruta de imagen no válida.')
        text='Imagen generada con '+('ChatGPT / OpenAI' if provider=='OpenAI' else 'Gemini')+'.'
        with self.db.connect() as db:
            identity=db.execute('INSERT INTO messages(conversation_id,role,content) VALUES(?,?,?)',(conversation,'assistant',text)).lastrowid
            db.execute('INSERT INTO image_attachments VALUES(?,?,?,?,?,?)',(identity,filename,provider,model,dimensions['width'],dimensions['height']))
        return {'path':str(path),'provider':provider,'model':model,**dimensions,'message_id':identity}
    def attachment(self,message_id):
        with self.db.connect() as db:record=db.execute('SELECT * FROM image_attachments WHERE message_id=?',(message_id,)).fetchone()
        if not record:return None
        row=dict(record)
        if not re.fullmatch(r'[0-9a-f]{32}\.png',row['file']):return None
        row['path']=str(self.directory/row['file']);return row


class ImageService:
    def __init__(self,config,archive):self.config=config;self.archive=archive
    def generate(self,prompt,provider,model,cancel):
        check_cancel(cancel)
        if provider not in MODELS or not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,150}',model):raise VictorError('Proveedor o modelo de imagen no válido.')
        key=self.config.api_key(provider)
        if not key:raise VictorError('Configura tu clave API personal de '+provider+' en Ajustes → IA para generar imágenes.')
        with tempfile.TemporaryDirectory(prefix='image-request-',dir=self.config.data_dir) as folder:
            directory=Path(folder);result_path=directory/'result.json';image_path=directory/'image.png'
            payload={'provider':provider,'model':model,'prompt':prompt[:12000],'key':key,'directory':str(directory)}
            env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
            process=subprocess.Popen([sys.executable,'-X','utf8','-m','victor.ai.images','--worker'],stdin=subprocess.PIPE,
                                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,cwd=self.config.root,env=env,
                                     creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),shell=False)
            try:
                process.stdin.write(json.dumps(payload,ensure_ascii=False).encode('utf-8')+b'\n');process.stdin.close()
                deadline=time.monotonic()+240
                while process.poll() is None:
                    check_cancel(cancel)
                    if time.monotonic()>deadline:raise VictorError('El proveedor de imágenes tardó demasiado. La espera se detuvo.')
                    cancel.wait(.1)
                check_cancel(cancel)
                if not result_path.is_file():raise VictorError('El proceso de imágenes terminó sin un resultado válido.')
                result=json.loads(result_path.read_text(encoding='utf-8'))
                if process.returncode or not result.get('ok'):raise VictorError(result.get('error','No se completó la imagen.'))
                if not image_path.is_file():raise VictorError('No se encontró la imagen generada.')
                destination=self.archive.directory/(uuid.uuid4().hex+'.png')
                os.replace(image_path,destination);return destination,result['dimensions']
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=3)
                    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)


def worker():
    payload=json.loads(sys.stdin.buffer.readline().decode('utf-8'));directory=Path(payload['directory'])
    try:
        blob=openai_image(payload) if payload['provider']=='OpenAI' else gemini_image(payload)
        dimensions=normalize_image(blob,directory/'image.png');result={'ok':True,'dimensions':dimensions}
    except Exception as exc:result={'ok':False,'error':str(exc) if isinstance(exc,VictorError) else api_error(exc,payload['provider'])}
    (directory/'result.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
    raise SystemExit(0 if result['ok'] else 1)

if __name__=='__main__' and '--worker' in sys.argv:worker()
