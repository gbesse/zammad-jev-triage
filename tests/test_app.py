import os
import unittest
from unittest.mock import patch
from app import process
from webhook import InvalidEvent
class ZammadTests(unittest.TestCase):
    def test_route_and_skip(self):
        event={"ticket":{"id":1,"title":"Invoice problem","group_id":3},"article":{"sender":"Customer","body":"<b>Charged twice</b>"}}
        updates=[]
        with patch.dict(os.environ,{"TYPESAFE_API_KEY":"test","ZAMMAD_GROUP_IDS":"{\"billing\":2}"}):
            result=process(event,evaluate=lambda text,policy,key:{"outcome":"billing"},update=lambda *args:updates.append(args))
        self.assertEqual(updates,[(1,2)])
        event["article"]["sender"]="Agent"
        self.assertIn("skipped",process(event))

    def test_internal_customer_article_is_not_routed(self):
        event={"ticket":{"id":1,"title":"Internal note"},"article":{"sender":"Customer","internal":True,"body":"Billing"}}
        self.assertIn("skipped",process(event,evaluate=lambda *_: self.fail("Jev must not run")))

    def test_ticket_update_request(self):
        from app import update_ticket
        import json
        requests=[]
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return b'{}'
        with patch.dict(os.environ,{"ZAMMAD_URL":"https://zammad.example","ZAMMAD_API_TOKEN":"secret"}),patch('app.urlopen',side_effect=lambda request,timeout:requests.append(request) or Response()):
            update_ticket(7,2)
        self.assertEqual(requests[0].full_url,'https://zammad.example/api/v1/tickets/7')
        self.assertEqual(json.loads(requests[0].data),{'group_id':2})
        self.assertEqual(requests[0].get_method(),'PUT')

    def test_rejects_malformed_customer_fields_without_evaluation(self):
        evaluate=lambda *_: self.fail("Jev must not run")
        for event in (
            {"ticket":[],"article":{"sender":"Customer"}},
            {"ticket":{"id":1},"article":[]},
            {"ticket":{"id":1},"article":{"sender":"Customer","body":["invalid"]}},
            {"ticket":{"id":1,"title":{"invalid":True}},"article":{"sender":"Customer"}},
        ):
            with self.subTest(event=event), self.assertRaises(InvalidEvent):
                process(event,evaluate=evaluate)

    def test_rejects_boolean_group_mapping(self):
        event={"ticket":{"id":1,"group_id":1},"article":{"sender":"Customer","body":"Billing"}}
        with patch.dict(os.environ,{"TYPESAFE_API_KEY":"test","ZAMMAD_GROUP_IDS":"{\"billing\":true}"}):
            with self.assertRaises(ValueError):
                process(event,evaluate=lambda *_:{"outcome":"billing"},update=lambda *_:self.fail("must not update"))
