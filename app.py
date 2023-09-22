import fastapi
from subprocess import Popen
import os
from pathlib import Path
import pydantic
import json

app = fastapi.FastAPI(title='EasyRSA', docs_url='/')

BASE_DIR=Path(os.environ.get('PKI_BASE_DIR', '/data'))
EASYRSA='/usr/share/easy-rsa/3/easyrsa'

if not BASE_DIR.exists():
    BASE_DIR.mkdir(parents=True, exist_ok=True)

@app.get('/pki/')
def list_pki():
    return os.listdir(BASE_DIR)

@app.put('/pki/{pki_name}')
def create_pki(pki_name: str):
    if (BASE_DIR / pki_name).exists():
        raise fastapi.HTTPException(422, 'PKI exists')
    _create_pki(pki_name)
    return {
        'detail': 'created'
    }

def _create_pki(pki_name):
    pki_dir = BASE_DIR / pki_name
    if not pki_dir.exists():
        pki_dir.mkdir()
        proc = Popen([EASYRSA, 'init-pki'], cwd=pki_dir)
        proc.wait()
    if not os.path.exists(pki_dir / 'pki' / 'ca.crt'):
       proc = Popen([EASYRSA, 'build-ca', 'nopass'], cwd=pki_dir, env={
           'EASYRSA_BATCH': '1',
           'EASYRSA_REQ_CN': pki_name
       })
       proc.wait()

def _create_server(pki_name, server_name):
    _create_pki(pki_name)
    pki_dir = BASE_DIR / pki_name
    if not os.path.exists(pki_dir / 'private' / ('%s.key' % server_name)):
        proc = Popen([EASYRSA, 'build-server-full', server_name, 'nopass'], cwd=pki_dir, env={
            'EASYRSA_BATCH': '1'
        })
        proc.wait()

@app.get('/pki/{pki_name}/ca.crt')
def get_ca(pki_name: str):
    cafile = BASE_DIR / pki_name / 'pki' / 'ca.crt'
    if not cafile.exists():
        raise fastapi.HTTPException(404, 'Not found')
    with open(cafile) as f:
        return fastapi.Response(f.read(), status_code=200, headers={'content-type': 'application/x-pem-file', 'content-disposition': 'attachment; filename="ca.crt"'})
    
@app.put('/pki/{pki_name}/servers/{server_name}')
def create_server(pki_name: str, server_name: str):
    keyfile = BASE_DIR / pki_name / 'pki' / 'private' / ('%s.key' % server_name)
    if keyfile.exists():
        raise fastapi.HTTPException(422, 'Already exists')
    _create_server(pki_name, server_name)
    return {
        'detail': 'ok'
    }
@app.get('/pki/{pki_name}/servers/{server_name}/key')
def get_key(pki_name: str, server_name: str):
    keyfile = BASE_DIR / pki_name / 'pki' / 'private' / ('%s.key' % server_name)
    if not keyfile.exists():
        raise fastapi.HTTPException(404, 'Not found')
    with open(keyfile) as f:
        return fastapi.Response(f.read(), status_code=200, 
                                headers={'content-type': 'application/x-pem-file', 
                                        'content-disposition': 'attachment; filename="%s.key"' % server_name})
    
@app.get('/pki/{pki_name}/servers/{server_name}/crt')
def get_crt(pki_name: str, server_name: str):
    certfile = BASE_DIR / pki_name / 'pki' / 'issued' / ('%s.crt' % server_name)
    if not certfile.exists():
        raise fastapi.HTTPException(404, 'Not found')
    
    with open(certfile) as f:
        return fastapi.Response(f.read(), status_code=200, 
                                headers={'content-type': 'application/x-pem-file', 
                                        'content-disposition': 'attachment; filename="%s.crt"' % server_name})
    
@app.get('/pki/{pki_name}/servers/{server_name}/req')
def get_req(pki_name: str, server_name: str):
    reqfile = BASE_DIR / pki_name / 'pki' / 'reqs' / ('%s.req' % server_name)
    if not reqfile.exists():
        raise fastapi.HTTPException(404, 'Not found')
    with open(reqfile) as f:
        return fastapi.Response(f.read(), status_code=200, 
                                headers={'content-type': 'application/x-pem-file', 
                                        'content-disposition': 'attachment; filename="%s.crt"' % server_name})
