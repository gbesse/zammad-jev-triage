"""Zammad ticket routing from signed customer-article webhooks."""
import html
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen
from jev_core import decide
from webhook import InvalidEvent, make_app, serve
POLICY=json.loads(Path(__file__).with_name("policy.json").read_text())

def process(event, *, evaluate=decide, update=None):
    ticket=event.get("ticket",{}); article=event.get("article",{})
    if not isinstance(ticket,dict) or not isinstance(article,dict): raise InvalidEvent("ticket and article must be objects")
    ticket_id=ticket.get("id")
    if article.get("sender") != "Customer" or article.get("internal") is True or not isinstance(ticket_id,int) or isinstance(ticket_id,bool) or ticket_id < 1: return {"skipped":"non-public customer article"}
    body=article.get("body") or ""
    title=ticket.get("title") or ""
    if not isinstance(body,str) or not isinstance(title,str): raise InvalidEvent("title and body must be strings")
    clean=re.sub(r"<[^>]*>"," ",body)
    text=title+"\n"+html.unescape(clean)
    result=evaluate(text,POLICY,os.environ["TYPESAFE_API_KEY"])
    groups=json.loads(os.environ.get("ZAMMAD_GROUP_IDS","{}"))
    group=groups.get(result["outcome"])
    if group is not None:
        if not isinstance(group,int) or isinstance(group,bool) or group < 1: raise ValueError("group IDs must be positive integers")
        if group != ticket.get("group_id"):
            (update or update_ticket)(ticket_id,group)
    return result

def update_ticket(ticket_id,group_id):
    base=os.environ["ZAMMAD_URL"].rstrip("/")
    token=os.environ["ZAMMAD_API_TOKEN"]
    if not base.startswith("https://"): raise ValueError("HTTPS required")
    req=Request(f"{base}/api/v1/tickets/{ticket_id}",data=json.dumps({"group_id":group_id}).encode(),headers={"Authorization":"Token token="+token,"Content-Type":"application/json","X-Zammad-Suppress-Notifications":"true"},method="PUT")
    with urlopen(req,timeout=15) as response: response.read()

if __name__=="__main__":
    serve(make_app(process,secret=os.environ["ZAMMAD_WEBHOOK_SECRET"],header="HTTP_X_HUB_SIGNATURE",scheme="sha1"))
