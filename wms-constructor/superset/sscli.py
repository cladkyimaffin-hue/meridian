import json, os, sys, urllib.request, urllib.error, urllib.parse, http.cookiejar
def env(p):
    d={}
    for ln in open(p,encoding='utf-8'):
        ln=ln.rstrip('\n')
        if ln and not ln.startswith('#') and '=' in ln:
            k,v=ln.split('=',1); d[k.strip()]=v.strip()
    return d
sup=env('/opt/wms-constructor-secrets/superset.env'); app=env('/opt/wms-constructor-secrets/app.env')
SECRETS=[sup['ADMIN_PASSWORD'],app['MSSQL_PASSWORD']]
B=os.environ.get("SUPERSET_URL") or sys.exit("задайте SUPERSET_URL=http://<адрес>:8088")
def clean(x):
    t=x if isinstance(x,str) else json.dumps(x,ensure_ascii=False)
    for s in SECRETS: t=t.replace(s,'***'); t=t.replace(urllib.parse.quote(s,safe=''),'***')
    return t
class SS:
    """Клиент REST API Superset. Вход через сессию (как в браузере): при входе по JWT права администратора не подхватываются."""
    def __init__(self):
        self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        import re
        html=self.op.open(B+"/login/",timeout=60).read().decode("utf-8","replace")
        m=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',html) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"',html)
        assert m, "не найден csrf_token на странице входа"
        data=urllib.parse.urlencode({"csrf_token":m.group(1),"username":"admin","password":sup["ADMIN_PASSWORD"]}).encode()
        r=urllib.request.Request(B+"/login/",data=data,headers={"Referer":B+"/login/"})
        x=self.op.open(r,timeout=60)
        assert "login" not in x.geturl().split("/")[-2:], "вход не удался"
        self.csrf=self.call("GET","/api/v1/security/csrf_token/")[1]["result"]
    def call(self,m,p,body=None,t=180):
        h={"Content-Type":"application/json"} if body is not None else {}
        if m!="GET": h["X-CSRFToken"]=self.csrf; h["Referer"]=B
        p=urllib.parse.quote(p,safe="/?=&:,%{}[]"+chr(34))
        r=urllib.request.Request(B+p,method=m,data=(json.dumps(body).encode() if body is not None else None),headers=h)
        try:
            x=self.op.open(r,timeout=t); raw=x.read(); return x.status,(json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw=e.read().decode("utf-8","replace")
            try: return e.code,json.loads(raw)
            except Exception: return e.code,raw[:400]
def mssql_uri():
    return "mssql+pymssql://%s:%s@%s:%s/%s" % (urllib.parse.quote(app['MSSQL_USER'],safe=''),urllib.parse.quote(app['MSSQL_PASSWORD'],safe=''),app['MSSQL_HOST'],app.get('MSSQL_PORT','1433'),app.get('MSSQL_DB','LV_MERIDIAN'))
