"""Signed webhook receiver with bounded request bodies."""
import base64
import hashlib
import hmac
import json
import os
from wsgiref.simple_server import make_server

MAX_BODY = 1024 * 1024

def check_signature(body, supplied, secret, scheme):
    if not secret or not supplied: return False
    if scheme == "sha1": expected = "sha1=" + hmac.new(secret.encode(),body,hashlib.sha1).hexdigest()
    elif scheme == "base64-sha256": expected = base64.b64encode(hmac.new(secret.encode(),body,hashlib.sha256).digest()).decode()
    else: raise ValueError("unsupported signature scheme")
    return hmac.compare_digest(expected, supplied)

def make_app(process, *, secret, header, scheme):
    def app(environ, start_response):
        if environ.get("REQUEST_METHOD") != "POST" or environ.get("PATH_INFO") != "/webhook":
            start_response("404 Not Found", [("Content-Type","application/json")]); return [b'{}']
        try: length = int(environ.get("CONTENT_LENGTH") or "0")
        except ValueError: length = -1
        if length < 1 or length > MAX_BODY:
            start_response("413 Payload Too Large", [("Content-Type","application/json")]); return [b'{}']
        body = environ["wsgi.input"].read(length)
        if not check_signature(body,environ.get(header,""),secret,scheme):
            start_response("401 Unauthorized", [("Content-Type","application/json")]); return [b'{}']
        try:
            result = process(json.loads(body))
            data = json.dumps({"ok":True,"decision":result}).encode()
            start_response("200 OK", [("Content-Type","application/json"),("Content-Length",str(len(data)))])
            return [data]
        except Exception:
            # Let the source retry. Never return a successful decision on model or API errors.
            start_response("503 Service Unavailable", [("Content-Type","application/json")]); return [b'{"ok":false}']
    return app

def serve(app):
    host = os.getenv("LISTEN_HOST","127.0.0.1")
    port = int(os.getenv("PORT","8080"))
    with make_server(host,port,app) as server: server.serve_forever()
