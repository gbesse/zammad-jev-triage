import io
import json
import unittest
from jev_core import DecisionError, decide

POLICY = json.load(open("policy.json"))
class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()

def fake(choice, probability, model=None):
    def opener(request, timeout):
        body = json.loads(request.data)
        assert body["model"] == POLICY["model"]
        assert request.get_header("Authorization") == "Bearer test"
        probs = {key: 0 for key in POLICY["criteria"]}
        probs[choice] = probability
        return Response(json.dumps({"model": model or POLICY["model"], "answers": {POLICY["question"]: {"type": "choice", "choice": choice, "probabilities": probs}}}).encode())
    return opener
class DecisionTests(unittest.TestCase):
    def test_accept_and_review(self):
        choice = next(key for key in POLICY["criteria"] if key != "other")
        self.assertEqual(decide("A specific request", POLICY, "test", opener=fake(choice, 0.95))["outcome"], choice)
        self.assertEqual(decide("A specific request", POLICY, "test", opener=fake(choice, 0.5))["outcome"], "review")
        self.assertEqual(decide("A specific request", POLICY, "test", opener=fake("other", 0.99))["outcome"], "review")
    def test_fail_closed(self):
        choice = next(iter(POLICY["criteria"]))
        with self.assertRaises(DecisionError): decide("text", POLICY, "test", opener=fake(choice, 0.9, "wrong-model"))
        with self.assertRaises(DecisionError): decide("", POLICY, "test", opener=fake(choice, 0.9))
        with self.assertRaises(DecisionError): decide("text", POLICY, "")
if __name__ == "__main__": unittest.main()
