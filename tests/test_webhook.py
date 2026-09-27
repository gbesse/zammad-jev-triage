import base64
import hashlib
import hmac
import io
import json
import unittest
from webhook import check_signature, make_app
class WebhookTests(unittest.TestCase):
    def test_signatures(self):
        raw=b'{}'; secret='secret'
        sha1='sha1='+hmac.new(secret.encode(),raw,hashlib.sha1).hexdigest()
        b64=base64.b64encode(hmac.new(secret.encode(),raw,hashlib.sha256).digest()).decode()
        self.assertTrue(check_signature(raw,sha1,secret,'sha1'))
        self.assertTrue(check_signature(raw,b64,secret,'base64-sha256'))
        self.assertFalse(check_signature(raw,sha1,'wrong','sha1'))
    def test_rejects_unsigned_and_accepts_signed(self):
        calls=[]
        app=make_app(lambda event:calls.append(event) or {'outcome':'review'},secret='secret',header='HTTP_X_TEST',scheme='sha1')
        def invoke(sig):
            result=[]; body=b'{"id":7}'
            env={'REQUEST_METHOD':'POST','PATH_INFO':'/webhook','CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body),'HTTP_X_TEST':sig}
            app(env,lambda status,headers:result.append(status))
            return result[0]
        self.assertEqual(invoke(''),'401 Unauthorized')
        self.assertEqual(calls,[])
        self.assertEqual(invoke('sha1='+hmac.new(b'secret',b'{"id":7}',hashlib.sha1).hexdigest()),'200 OK')
        self.assertEqual(calls,[{'id':7}])
