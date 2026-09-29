"""Zammad ticket routing from signed customer-article webhooks."""
import html
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen
from jev_core import decide
from webhook import make_app, serve
POLICY=json.loads(Path(__file__).with_name("policy.json").read_text())

def process(event, *, evaluate=decide, update=None):
    ticket=event.get("ticket") or {}; article=event.get("article") or {}
    if article.get("sender") != "Customer" or article.get("internal") is True or not isinstance(ticket.get("id"),int): return {"skipped":"non-public customer article"}
    clean=re.sub(r"<[^>]*>"," ",article.get("body") or "")
    text=(ticket.get("title") or "")+"\n"+html.unescape(clean)
    result=evaluate(text,POLICY,os.environ["TYPESAFE_API_KEY"])
    groups=json.loads(os.environ.get("ZAMMAD_GROUP_IDS","{}"))
    group=groups.get(result["outcome"])
    if group is not None and group != ticket.get("group_id"):
        if not isinstance(group,int): raise ValueError("group IDs must be integers")
        (update or update_ticket)(ticket["id"],group)
    return result

def update_ticket(ticket_id,group_id):
    base=os.environ["ZAMMAD_URL"].rstrip("/")
    token=os.environ["ZAMMAD_API_TOKEN"]
    if not base.startswith("https://"): raise ValueError("HTTPS required")
    req=Request(f"{base}/api/v1/tickets/{ticket_id}",data=json.dumps({"group_id":group_id}).encode(),headers={"Authorization":"Token token="+token,"Content-Type":"application/json","X-Zammad-Suppress-Notifications":"true"},method="PUT")
    with urlopen(req,timeout=15) as response: response.read()

if __name__=="__main__":
    serve(make_app(process,secret=os.environ["ZAMMAD_WEBHOOK_SECRET"],header="HTTP_X_HUB_SIGNATURE",scheme="sha1"))
