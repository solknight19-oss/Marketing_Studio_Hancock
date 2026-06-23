#!/usr/bin/env python3
import base64
import datetime as dt
import hashlib
import hmac
import http.cookies
import http.server
import json
import os
import secrets
import sqlite3
import subprocess
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = Path(os.environ.get('APP_DATA_DIR', str(ROOT / 'app_data')))
APP.mkdir(parents=True, exist_ok=True)
DB = APP / 'studio.db'
SECRET_FILE = APP / '.session_secret'
INITIAL_LOGINS = APP / 'INITIAL_LOGINS.md'
SESSION_DAYS = 7
PORT = int(os.environ.get('PORT', '8765'))
HOST = os.environ.get('HOST', '0.0.0.0')
USERS = [
    ('admin', 'rknight@hancockclaims.com', 'Ryan Knight', 'owner'),
    ('cassie', '', 'Cassie Tant', 'admin'),
    ('jennifer', '', 'Jennifer Walker', 'admin'),
]
PASSWORD_ENV_VARS = {
    'admin': 'ADMIN_PASSWORD',
    'cassie': 'CASSIE_PASSWORD',
    'jennifer': 'JENNIFER_PASSWORD',
}
SERVICE_LINES = ['Storm / CAT Damage','Underwriting Inspection','Contents','Engineering','Commercial','Residential','4-Point Inspection','Ladder Assist','Loss Control','DI / UDI Inspections']

def now(): return dt.datetime.now().isoformat(timespec='seconds')
def human_time(value):
    try: return dt.datetime.fromisoformat(value).strftime('%b %d, %I:%M %p')
    except Exception: return value or ''
def secret():
    env_secret = os.environ.get('SESSION_SECRET', '').strip()
    if env_secret:
        return env_secret.encode()
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_urlsafe(48), encoding='utf-8')
        try: SECRET_FILE.chmod(0o600)
        except Exception: pass
    return SECRET_FILE.read_text(encoding='utf-8').strip().encode()
def sign(value): return value + '.' + hmac.new(secret(), value.encode(), hashlib.sha256).hexdigest()
def unsign(value):
    try: raw, sig = value.rsplit('.', 1)
    except ValueError: return ''
    good = hmac.new(secret(), raw.encode(), hashlib.sha256).hexdigest()
    return raw if hmac.compare_digest(sig, good) else ''
def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 180000)
    return salt + '$' + base64.b64encode(digest).decode()
def check_password(password, stored):
    try: salt, _ = stored.split('$', 1)
    except ValueError: return False
    return hmac.compare_digest(password_hash(password, salt), stored)
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db(); cur = con.cursor()
    cur.executescript("""
    create table if not exists users(id integer primary key autoincrement, username text unique not null, email text, name text not null, role text not null, password_hash text not null, created_at text not null);
    create table if not exists sessions(token text primary key, user_id integer not null, expires_at text not null);
    create table if not exists drafts(id integer primary key autoincrement, title text not null, content_type text not null, service_line text, body text not null, status text not null, owner_id integer, updated_by integer, created_at text not null, updated_at text not null);
    create table if not exists tasks(id integer primary key autoincrement, title text not null, details text, status text not null, assigned_to integer, created_by integer, created_at text not null, updated_at text not null);
    create table if not exists activity(id integer primary key autoincrement, user_id integer, action text not null, meta text, created_at text not null);
    """)
    user_columns = {row['name'] for row in cur.execute('pragma table_info(users)')}
    if 'email' not in user_columns:
        cur.execute('alter table users add column email text')
    cur.execute("update users set email=? where username='admin'", ('rknight@hancockclaims.com',))
    if cur.execute('select count(*) as n from users').fetchone()['n'] == 0:
        lines=['# Initial Live Studio Logins','','Temporary local passwords. Change before public deployment.','']
        ids={}
        for username, email, name, role in USERS:
            pw=os.environ.get(PASSWORD_ENV_VARS[username], '').strip() or secrets.token_urlsafe(9)
            cur.execute('insert into users(username,email,name,role,password_hash,created_at) values(?,?,?,?,?,?)',(username,email or None,name,role,password_hash(pw),now()))
            ids[username]=cur.lastrowid
            login=email or username
            lines.append(f'- {name}: login `{login}`, password `{pw}`')
        INITIAL_LOGINS.write_text('\n'.join(lines)+'\n', encoding='utf-8')
        try: INITIAL_LOGINS.chmod(0o600)
        except Exception: pass
        cur.execute('insert into tasks(title,details,status,assigned_to,created_by,created_at,updated_at) values(?,?,?,?,?,?,?)',("Review today's Industry Radar",'Pick one live trend and turn it into a Hancock post or article.','todo',ids.get('cassie'),ids.get('admin'),now(),now()))
        cur.execute('insert into tasks(title,details,status,assigned_to,created_by,created_at,updated_at) values(?,?,?,?,?,?,?)',('Complete first article draft','Use the bot suggestions, add the Hancock angle, and move the draft to Ready for Review.','todo',ids.get('jennifer'),ids.get('admin'),now(),now()))
    for username, env_name in PASSWORD_ENV_VARS.items():
        configured_password = os.environ.get(env_name, '').strip()
        if configured_password:
            cur.execute('update users set password_hash=? where username=?',
                        (password_hash(configured_password), username))
    con.commit(); con.close()
def log_action(user_id, action, meta=''):
    con=db(); con.execute('insert into activity(user_id,action,meta,created_at) values(?,?,?,?)',(user_id,action,meta,now())); con.commit(); con.close()
def rowdict(row): return dict(row) if row else None
def load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return fallback

def latest_bot_data():
    path=ROOT/'data'/'latest_bot.json'
    if not path.exists(): return {'stories':[],'clusters':[],'library':[],'generatedHuman':'No bot scan yet'}
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {'stories':[],'clusters':[],'library':[],'generatedHuman':'Bot data could not be read'}
def chad_feed():
    return load_json(ROOT/'data'/'main_speaking_bot_feed.json', {'mainSpeakingBot': {'priority': 'Run Chad council first.', 'next_steps': []}, 'bots': []})
def collect_state():
    con=db()
    tasks=[dict(r) for r in con.execute('select * from tasks order by updated_at desc limit 30')]
    drafts=[dict(r) for r in con.execute('select * from drafts order by updated_at desc limit 30')]
    activity=[dict(r) for r in con.execute('select a.*, u.name as user_name from activity a left join users u on u.id=a.user_id order by a.id desc limit 30')]
    con.close(); return {'tasks':tasks,'drafts':drafts,'activity':activity,'botData':latest_bot_data()}
def bot_welcome(user, tasks, drafts, activity):
    feed = chad_feed().get('mainSpeakingBot', {})
    open_tasks=[t for t in tasks if t.get('status')!='done']; doing=[t for t in tasks if t.get('status')=='doing']; recent=[a for a in activity if a.get('user_id')!=user['id']][:2]
    parts=[f"Hi {user['name'].split()[0]}. Chad has the latest bot briefing ready."]
    if feed.get('priority'):
        parts.append(f"Priority: {feed['priority']}")
    if doing: parts.append(f"Active work: {doing[0]['title']}. Let's complete that before starting another item.")
    elif open_tasks: parts.append(f"Best next step: {open_tasks[0]['title']}.")
    else: parts.append('No open tasks are blocking you. Pick a fresh radar trend and start the next draft.')
    if drafts: parts.append(f"Latest draft: {drafts[0]['title']} ({drafts[0]['status']}).")
    if recent: parts.append(f"Workspace update: {recent[0].get('user_name') or 'Someone'} {recent[0].get('action')} {recent[0].get('meta') or ''}.")
    return ' '.join(parts)
def bot_reply(user, message, state):
    lower=message.lower(); tasks=state['tasks']; bot_data=state['botData']; activity=state['activity']
    if any(w in lower for w in ['cassie','jennifer','other','working']):
        recent=[a for a in activity if a.get('user_name') and a.get('user_name')!=user['name']]
        return 'Recent workspace activity: '+('; '.join(f"{a['user_name']} {a['action']} {a.get('meta') or ''}" for a in recent[:3]) if recent else 'No recent activity from the other user yet. Assign a task so the handoff is clear.')
    if any(w in lower for w in ['post','article','blog','content']):
        stories=bot_data.get('stories') or []
        if stories:
            s=stories[0]; return f"Use the current top radar item: {s.get('title')}. Hancock angle: {s.get('angle')}. Create the article first, then repurpose it into LinkedIn copy."
        return 'Start with one service-line article. Pick Storm/CAT, Underwriting, or Ladder Assist, write the Hancock angle, then generate the draft.'
    doing=[t for t in tasks if t.get('status')=='doing']; todo=[t for t in tasks if t.get('status') in ('todo','review')]
    if doing: return f"Stay on {doing[0]['title']}. Finish the missing information, then move it to Review."
    if todo: return f"Next step: {todo[0]['title']}. Assign it, set it to Doing, and create one working draft."
    return 'Pick one radar trend, create one draft, assign one owner, and move it to Review.'

class Handler(http.server.BaseHTTPRequestHandler):
    server_version='HancockLiveStudio/0.1'
    def send_html(self,text,code=200):
        data=text.encode('utf-8'); self.send_response(code); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def send_json(self,obj,code=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8'); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def redirect(self,path): self.send_response(302); self.send_header('Location',path); self.end_headers()
    def read_body(self):
        raw=self.rfile.read(int(self.headers.get('Content-Length','0') or 0)).decode('utf-8')
        if 'application/json' in self.headers.get('Content-Type',''): return json.loads(raw or '{}')
        return {k:v[0] for k,v in urllib.parse.parse_qs(raw).items()}
    def current_user(self):
        cookie=http.cookies.SimpleCookie(self.headers.get('Cookie','')); morsel=cookie.get('hms_session')
        if not morsel: return None
        token=unsign(morsel.value)
        if not token: return None
        con=db(); row=con.execute('select u.* from sessions s join users u on u.id=s.user_id where s.token=? and s.expires_at>?',(token,now())).fetchone(); con.close(); return rowdict(row)
    def require_user(self):
        user=self.current_user()
        if not user: self.send_json({'error':'login required'},401); return None
        return user
    def do_GET(self):
        path=urllib.parse.urlparse(self.path).path
        if path=='/healthz': self.send_json({'ok': True, 'service': 'hancock-live-site'}); return
        if path=='/': self.redirect('/dashboard' if self.current_user() else '/login'); return
        if path=='/login': self.send_html(LOGIN_HTML); return
        if path=='/dashboard':
            if not self.current_user(): self.redirect('/login'); return
            self.send_html(DASHBOARD_HTML); return
        if path=='/studio':
            if not self.current_user(): self.redirect('/login'); return
            p=ROOT/'Hancock_Marketing_Studio.html'; self.send_html(p.read_text(encoding='utf-8') if p.exists() else '<h1>Studio not found</h1>', 200 if p.exists() else 404); return
        if path=='/api/state':
            user=self.require_user();
            if user: self.api_state(user)
            return
        if path=='/api/chad-feed':
            user=self.require_user();
            if user: self.send_json(chad_feed())
            return
        self.send_html('<h1>Not found</h1>',404)
    def do_POST(self):
        path=urllib.parse.urlparse(self.path).path
        if path=='/login': self.handle_login(); return
        if path=='/logout': self.send_response(302); self.send_header('Location','/login'); self.send_header('Set-Cookie','hms_session=; Max-Age=0; Path=/'); self.end_headers(); return
        user=self.require_user();
        if not user: return
        if path=='/api/draft': self.api_save_draft(user); return
        if path=='/api/task': self.api_save_task(user); return
        if path=='/api/bot': self.api_bot(user); return
        if path=='/api/run-scan': self.api_run_scan(user); return
        if path=='/api/run-council': self.api_run_council(user); return
        self.send_json({'error':'not found'},404)
    def handle_login(self):
        data=self.read_body(); username=(data.get('username') or '').strip().lower(); password=data.get('password') or ''
        con=db(); row=con.execute('select * from users where lower(username)=? or lower(email)=?', (username, username)).fetchone()
        if row and check_password(password,row['password_hash']):
            token=secrets.token_urlsafe(32); expires=(dt.datetime.now()+dt.timedelta(days=SESSION_DAYS)).isoformat(timespec='seconds')
            con.execute('insert into sessions(token,user_id,expires_at) values(?,?,?)',(token,row['id'],expires)); con.commit(); con.close(); log_action(row['id'],'logged in')
            self.send_response(302); self.send_header('Location','/dashboard'); self.send_header('Set-Cookie',f'hms_session={sign(token)}; HttpOnly; SameSite=Lax; Path=/'); self.end_headers()
        else:
            con.close(); self.send_html(LOGIN_HTML.replace('<!--ERR-->','<div class="err">Login failed. Check username and password.</div>'),401)
    def api_state(self,user):
        con=db()
        users=[dict(r) for r in con.execute('select id,username,name,role from users order by name')]
        drafts=[dict(r) for r in con.execute('select d.*, u.name owner_name, uu.name updated_by_name from drafts d left join users u on u.id=d.owner_id left join users uu on uu.id=d.updated_by order by d.updated_at desc limit 50')]
        tasks=[dict(r) for r in con.execute("select t.*, u.name assigned_name, c.name created_by_name from tasks t left join users u on u.id=t.assigned_to left join users c on c.id=t.created_by order by case t.status when 'doing' then 0 when 'todo' then 1 when 'review' then 2 else 3 end, t.updated_at desc")]
        activity=[dict(r) for r in con.execute('select a.*, u.name user_name from activity a left join users u on u.id=a.user_id order by a.id desc limit 30')]
        con.close()
        for collection in (drafts,tasks,activity):
            for item in collection:
                for key in ('created_at','updated_at'):
                    if key in item: item[key+'_human']=human_time(item.get(key))
        self.send_json({'user':{k:user[k] for k in ('id','username','name','role')},'users':users,'drafts':drafts,'tasks':tasks,'activity':activity,'botData':latest_bot_data(),'serviceLines':SERVICE_LINES,'welcome':bot_welcome(user,tasks,drafts,activity)})
    def api_save_draft(self,user):
        data=self.read_body(); title=(data.get('title') or 'Untitled draft').strip()[:160]; body=data.get('body') or ''; ctype=(data.get('content_type') or 'Blog Post')[:60]; line=(data.get('service_line') or '')[:80]; status=(data.get('status') or 'draft')[:40]; draft_id=data.get('id')
        con=db()
        if draft_id:
            con.execute('update drafts set title=?,body=?,content_type=?,service_line=?,status=?,updated_by=?,updated_at=? where id=?',(title,body,ctype,line,status,user['id'],now(),draft_id)); action='updated draft'
        else:
            cur=con.execute('insert into drafts(title,body,content_type,service_line,status,owner_id,updated_by,created_at,updated_at) values(?,?,?,?,?,?,?,?,?)',(title,body,ctype,line,status,user['id'],user['id'],now(),now())); draft_id=cur.lastrowid; action='created draft'
        con.commit(); con.close(); log_action(user['id'],action,title); self.send_json({'ok':True,'id':draft_id})
    def api_save_task(self,user):
        data=self.read_body(); title=(data.get('title') or 'Untitled task').strip()[:160]; details=data.get('details') or ''; status=data.get('status') or 'todo'; assigned=data.get('assigned_to') or None; task_id=data.get('id')
        con=db()
        if task_id:
            con.execute('update tasks set title=?,details=?,status=?,assigned_to=?,updated_at=? where id=?',(title,details,status,assigned,now(),task_id)); action='updated task'
        else:
            cur=con.execute('insert into tasks(title,details,status,assigned_to,created_by,created_at,updated_at) values(?,?,?,?,?,?,?)',(title,details,status,assigned,user['id'],now(),now())); task_id=cur.lastrowid; action='created task'
        con.commit(); con.close(); log_action(user['id'],action,title); self.send_json({'ok':True,'id':task_id})
    def api_bot(self,user):
        data=self.read_body(); msg=(data.get('message') or '').strip(); reply=bot_reply(user,msg,collect_state()); log_action(user['id'],'asked bot',msg[:140]); self.send_json({'reply':reply})
    def api_run_scan(self,user):
        try:
            result=subprocess.run(['python3','marketing_bot.py'],cwd=str(ROOT),text=True,capture_output=True,timeout=120)
            ok=result.returncode==0; log_action(user['id'],'ran live scan','success' if ok else 'failed'); self.send_json({'ok':ok,'output':(result.stdout+result.stderr)[-5000:]})
        except Exception as exc: self.send_json({'ok':False,'output':str(exc)},500)
    def api_run_council(self,user):
        try:
            result=subprocess.run(['python3','bot_council.py'],cwd=str(ROOT),text=True,capture_output=True,timeout=140)
            ok=result.returncode==0; log_action(user['id'],'ran Chad council','success' if ok else 'failed'); self.send_json({'ok':ok,'output':(result.stdout+result.stderr)[-5000:],'feed':chad_feed()})
        except Exception as exc: self.send_json({'ok':False,'output':str(exc)},500)

LOGIN_HTML = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Hancock Live Studio Login</title><style>:root{--navy:#1D4F91;--gold:#C9A227;--bg:#EFF2F7;--border:#E3E9F2;--text:#15243C}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(900px 400px at 80% -5%,#E4EAF4 0%,var(--bg) 55%);font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--text)}.card{width:min(440px,92vw);background:#fff;border:1px solid var(--border);border-radius:22px;padding:28px;box-shadow:0 20px 60px rgba(21,36,60,.14)}.brand{display:flex;gap:12px;align-items:center;margin-bottom:18px}.mark{width:48px;height:48px;border-radius:12px;background:var(--navy);color:#fff;display:grid;place-items:center;font-weight:900}.eyebrow{font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;color:var(--gold)}h1{margin:0;color:var(--navy);font-size:25px}p{color:#5B6B82;line-height:1.5}label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#5B6B82;font-weight:900;margin:16px 0 7px}input{width:100%;border:1px solid var(--border);border-radius:12px;padding:12px}button{width:100%;border:0;border-radius:13px;background:var(--navy);color:white;font-weight:900;padding:13px;margin-top:18px;cursor:pointer}.err{background:#fff1f1;border:1px solid #ffd0d0;color:#9a1a1a;padding:10px;border-radius:12px;margin-bottom:12px}</style></head><body><form class='card' method='post' action='/login'><div class='brand'><div class='mark'>H</div><div><div class='eyebrow'>Live Marketing Studio</div><h1>Sign in</h1></div></div><!--ERR--><p>Ryan, Cassie, Jennifer, and authorized admins can share drafts, tasks, bot guidance, and live scan results here.</p><label>Email or username</label><input name='username' autocomplete='username' autofocus><label>Password</label><input name='password' type='password' autocomplete='current-password'><button>Open Studio</button></form></body></html>"""

DASHBOARD_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hancock Live Marketing Studio</title><style>
:root{--navy:#1D4F91;--navy2:#163E74;--gold:#C9A227;--gold2:#E0C158;--bg:#EFF2F7;--text:#15243C;--sub:#5B6B82;--border:#E3E9F2;--card:#fff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 400px at 80% -5%,#E4EAF4 0%,var(--bg) 55%);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,select,textarea{font:inherit}button{cursor:pointer}.header{position:sticky;top:0;z-index:10;background:linear-gradient(112deg,#0E2A52 0%,var(--navy2) 44%,var(--navy) 100%);color:#fff;box-shadow:0 10px 28px rgba(14,42,82,.22)}.top{display:flex;justify-content:space-between;gap:16px;align-items:center;padding:18px 24px}.brand h1{margin:0;font-size:21px}.brand p{margin:4px 0 0;color:#A8C2E8;font-size:12px}.tabs{display:flex;gap:4px;overflow-x:auto;padding:0 20px}.tab{border:0;background:transparent;color:#B9C8E0;border-radius:12px 12px 0 0;padding:12px 14px;font-weight:900}.tab.active{background:var(--bg);color:var(--navy)}main{max-width:1280px;margin:0 auto;padding:24px}.view{display:none}.view.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}.layout{display:grid;grid-template-columns:380px 1fr;gap:18px}.card,.panel{background:var(--card);border:1px solid var(--border);border-radius:18px;box-shadow:0 8px 25px rgba(21,36,60,.055);padding:18px}.hero{background:linear-gradient(135deg,#0E2A52,var(--navy));color:#fff;border-radius:20px;padding:22px;display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center;margin-bottom:18px}.hero h2{margin:4px 0 6px}.hero p{color:#cfe0f4;margin:0}.eyebrow{font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;color:var(--gold2)}label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--sub);font-weight:900;margin:14px 0 7px}input,select,textarea{width:100%;border:1px solid var(--border);border-radius:12px;padding:11px;background:#FBFDFF}textarea{min-height:150px;resize:vertical}.btn{border:0;border-radius:12px;background:var(--navy);color:#fff;font-weight:900;padding:11px 14px;margin-top:12px}.btn.gold{background:linear-gradient(135deg,var(--gold),var(--gold2));color:#112b50}.btn.secondary{background:#edf4fb;color:var(--navy);border:1px solid #d6e3f3}.mini{border:1px solid #d8e4f2;background:#fff;color:var(--navy);border-radius:10px;font-size:12px;font-weight:800;padding:8px 10px;margin:5px 5px 0 0}.badge{display:inline-flex;border-radius:7px;background:#eef5ff;color:var(--navy);font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;padding:5px 8px}.badge.hot{background:#fff0dc;color:#9a4d00}.muted{color:var(--sub);font-size:13px}.activity{display:flex;flex-direction:column;gap:9px}.activity div{border-left:3px solid var(--gold);padding-left:10px;color:#41516a}.task{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:start;border-top:1px solid var(--border);padding:12px 0}.task:first-child{border-top:0}.botreply{background:#f8fbff;border:1px solid #dce8f7;border-left:4px solid var(--gold);border-radius:14px;padding:13px;line-height:1.45}.chatrow{display:flex;gap:8px;margin-top:10px}.chatrow input{flex:1}.draftList{display:grid;gap:12px}.draftItem{border:1px solid var(--border);border-radius:14px;padding:14px;background:#fff}.out{white-space:pre-wrap;line-height:1.55}.adminbar{display:flex;gap:8px;flex-wrap:wrap}.who{font-size:12px;color:#cfe0f4}.logout{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.25);padding:8px 10px;border-radius:10px}.status{font-size:12px;color:var(--sub);min-height:18px}@media(max-width:900px){.layout,.hero{grid-template-columns:1fr}.top{padding:16px}main{padding:16px}}
</style></head><body>
<header class="header"><div class="top"><div class="brand"><h1>Hancock Live Marketing Studio</h1><p>Shared drafts, live scans, task focus, and bot guidance</p></div><div><div class="who" id="who"></div><form method="post" action="/logout" style="display:inline"><button class="logout" style="background:transparent">Logout</button></form></div></div><nav class="tabs" id="tabs"></nav></header>
<main>
<section id="dash" class="view active"><div class="hero"><div><div class="eyebrow">Welcome Bot</div><h2 id="welcomeTitle">Good to see you.</h2><p id="welcomeText">Loading workspace guidance...</p></div><div><button class="btn gold" onclick="askBot('What should I focus on next?')">What next?</button><button class="btn secondary" onclick="openTab('radar')">Open Radar</button></div></div><div class="grid"><div class="card"><h3>Bot Coach</h3><div class="botreply" id="botReply">Ask me what to work on, what the other user is doing, or what article to create next.</div><div class="chatrow"><input id="botInput" placeholder="Ask the bot..."><button class="mini" onclick="sendBot()">Send</button><button class="mini" onclick="voiceAsk()">Voice</button></div><div class="status" id="voiceStatus"></div></div><div class="card"><h3>Activity</h3><div class="activity" id="activity"></div></div><div class="card"><h3>Open Tasks</h3><div id="taskPreview"></div></div></div></section>
<section id="radar" class="view"><div class="hero"><div><div class="eyebrow">Live Industry Radar</div><h2>Fresh signals from the marketing bot</h2><p id="scanStamp">Loading scan data...</p></div><button class="btn gold" onclick="runScan()">Run Live Scan</button></div><div id="radarGrid" class="grid"></div></section>
<section id="drafts" class="view"><div class="layout"><div class="card"><h3>Create / Edit Draft</h3><input type="hidden" id="draftId"><label>Title</label><input id="draftTitle"><label>Type</label><select id="draftType"><option>Blog Post</option><option>LinkedIn Post</option><option>Email</option><option>Website Update</option><option>FAQ</option></select><label>Service Line</label><select id="draftLine"></select><label>Status</label><select id="draftStatus"><option>draft</option><option>doing</option><option>review</option><option>approved</option></select><label>Body</label><textarea id="draftBody"></textarea><button class="btn" onclick="saveDraft()">Save Shared Draft</button><button class="btn secondary" onclick="clearDraftForm()">New Blank Draft</button><div class="status" id="draftSaveStatus"></div></div><div class="panel"><h3>Shared Drafts</h3><div id="draftList" class="draftList"></div></div></div></section>
<section id="tasks" class="view"><div class="layout"><div class="card"><h3>Create / Edit Task</h3><input type="hidden" id="taskId"><label>Task</label><input id="taskTitle"><label>Details</label><textarea id="taskDetails"></textarea><label>Assign To</label><select id="taskAssigned"></select><label>Status</label><select id="taskStatus"><option>todo</option><option>doing</option><option>review</option><option>done</option></select><button class="btn" onclick="saveTask()">Save Task</button><button class="btn secondary" onclick="clearTaskForm()">New Task</button><div class="status" id="taskSaveStatus"></div></div><div class="panel"><h3>Team Tasks</h3><div id="taskList"></div></div></div></section>
<section id="admin" class="view"><div class="card"><h3>Admin</h3><p class="muted">Cassie and Jennifer are admins in this local build. Public deployment should add SSL, real email invites, password reset, and server-managed secrets.</p><div class="adminbar"><button class="btn" onclick="location.href='/studio'">Open Approved Studio</button><button class="btn secondary" onclick="runScan()">Run Bot Scan</button></div><pre class="out" id="adminOut"></pre></div></section>
</main><script>
let STATE={}; const TABLIST=[['dash','Dashboard'],['radar','Industry Radar'],['drafts','Drafts'],['tasks','Tasks'],['admin','Admin']]; function $(id){return document.getElementById(id)} function esc(s){return String(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))} function openTab(id){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===id));document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===id));} function renderTabs(){ $('tabs').innerHTML=TABLIST.map((t,i)=>`<button class="tab ${i?'':'active'}" data-tab="${t[0]}" onclick="openTab('${t[0]}')">${t[1]}</button>`).join('') } async function api(path, body){let opt=body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{};let r=await fetch(path,opt);if(!r.ok)throw new Error(await r.text());return r.json()} async function load(){STATE=await api('/api/state');render()} function render(){ $('who').textContent=STATE.user.name+' · '+STATE.user.role; $('welcomeTitle').textContent='Hi, '+STATE.user.name.split(' ')[0]+'.'; $('welcomeText').textContent=STATE.welcome; $('botReply').textContent=STATE.welcome; renderUsers();renderActivity();renderTasks();renderDrafts();renderRadar()} function renderUsers(){let opts='<option value="">Unassigned</option>'+STATE.users.map(u=>`<option value="${u.id}">${esc(u.name)}</option>`).join('');$('taskAssigned').innerHTML=opts;$('draftLine').innerHTML=STATE.serviceLines.map(x=>`<option>${esc(x)}</option>`).join('')} function renderActivity(){ $('activity').innerHTML=(STATE.activity||[]).slice(0,8).map(a=>`<div><b>${esc(a.user_name||'System')}</b> ${esc(a.action)} ${esc(a.meta||'')}<br><span class="muted">${esc(a.created_at_human||'')}</span></div>`).join('')||'<p class="muted">No activity yet.</p>'} function taskHtml(t){return `<div class="task"><div><span class="badge">${esc(t.status)}</span><h4>${esc(t.title)}</h4><p class="muted">${esc(t.details||'')}<br>Assigned: ${esc(t.assigned_name||'Unassigned')} · Updated ${esc(t.updated_at_human||'')}</p></div><div><button class="mini" onclick="editTask(${t.id})">Edit</button><button class="mini" onclick="quickTask(${t.id},'doing')">Doing</button><button class="mini" onclick="quickTask(${t.id},'done')">Done</button></div></div>`} function renderTasks(){let open=(STATE.tasks||[]).filter(t=>t.status!=='done');$('taskPreview').innerHTML=open.slice(0,4).map(taskHtml).join('')||'<p class="muted">No open tasks.</p>';$('taskList').innerHTML=(STATE.tasks||[]).map(taskHtml).join('')} function renderDrafts(){ $('draftList').innerHTML=(STATE.drafts||[]).map(d=>`<div class="draftItem"><span class="badge">${esc(d.status)}</span><h3>${esc(d.title)}</h3><p class="muted">${esc(d.content_type)} · ${esc(d.service_line||'')} · owner ${esc(d.owner_name||'')} · updated ${esc(d.updated_at_human||'')}</p><p>${esc((d.body||'').slice(0,260))}...</p><button class="mini" onclick="editDraft(${d.id})">Edit</button><button class="mini" onclick="copyDraft(${d.id})">Copy</button></div>`).join('')||'<p class="muted">No shared drafts yet.</p>'} function renderRadar(){let b=STATE.botData||{};$('scanStamp').textContent=(b.generatedHuman||'No scan yet')+' · '+(b.source||'');$('radarGrid').innerHTML=(b.stories||[]).slice(0,12).map((s,i)=>`<div class="card"><span class="badge ${s.tag==='Hot'?'hot':''}">${esc(s.tag||'Trend')}</span><h3>${esc(s.title)}</h3><p>${esc(s.summary)}</p><p><b>Hancock angle:</b> ${esc(s.angle)}</p><p class="muted">${esc(s.source||'')} ${s.date?'· '+esc(s.date):''}</p><button class="mini" onclick="draftFromRadar(${i})">Draft from this</button></div>`).join('')||'<div class="card"><p>No scan data yet. Run Live Scan.</p></div>'} function editDraft(id){let d=STATE.drafts.find(x=>x.id===id);if(!d)return;$('draftId').value=d.id;$('draftTitle').value=d.title;$('draftType').value=d.content_type;$('draftLine').value=d.service_line||STATE.serviceLines[0];$('draftStatus').value=d.status;$('draftBody').value=d.body;openTab('drafts')} function copyDraft(id){let d=STATE.drafts.find(x=>x.id===id); if(d)navigator.clipboard.writeText(d.body||'')} function clearDraftForm(){['draftId','draftTitle','draftBody'].forEach(id=>$(id).value='');$('draftStatus').value='draft'} async function saveDraft(){await api('/api/draft',{id:$('draftId').value,title:$('draftTitle').value,content_type:$('draftType').value,service_line:$('draftLine').value,status:$('draftStatus').value,body:$('draftBody').value});$('draftSaveStatus').textContent='Saved.';await load()} function draftFromRadar(i){let s=STATE.botData.stories[i];clearDraftForm();$('draftTitle').value=s.title;$('draftLine').value=s.line||STATE.serviceLines[0];$('draftBody').value='# '+s.title+'\n\n'+s.summary+'\n\n## Hancock angle\n'+s.angle+'\n\n## Next step\nTurn this into a useful post with a clear carrier-facing takeaway.';openTab('drafts')} function editTask(id){let t=STATE.tasks.find(x=>x.id===id);if(!t)return;$('taskId').value=t.id;$('taskTitle').value=t.title;$('taskDetails').value=t.details||'';$('taskAssigned').value=t.assigned_to||'';$('taskStatus').value=t.status;openTab('tasks')} function clearTaskForm(){['taskId','taskTitle','taskDetails'].forEach(id=>$(id).value='');$('taskStatus').value='todo';$('taskAssigned').value=''} async function saveTask(){await api('/api/task',{id:$('taskId').value,title:$('taskTitle').value,details:$('taskDetails').value,assigned_to:$('taskAssigned').value,status:$('taskStatus').value});$('taskSaveStatus').textContent='Saved.';await load()} async function quickTask(id,status){let t=STATE.tasks.find(x=>x.id===id);await api('/api/task',{id:id,title:t.title,details:t.details,assigned_to:t.assigned_to,status:status});await load()} async function askBot(msg){$('botReply').textContent='Thinking...';let r=await api('/api/bot',{message:msg});$('botReply').textContent=r.reply;speak(r.reply)} function sendBot(){let m=$('botInput').value.trim();if(!m)return;askBot(m);$('botInput').value=''} function speak(text){if(!('speechSynthesis' in window))return;let u=new SpeechSynthesisUtterance(text);u.rate=.95;window.speechSynthesis.cancel();window.speechSynthesis.speak(u)} function voiceAsk(){let SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){$('voiceStatus').textContent='Voice input is not available in this browser. Use the text box.';return}let rec=new SR();rec.lang='en-US';rec.onstart=()=>$('voiceStatus').textContent='Listening...';rec.onerror=()=>$('voiceStatus').textContent='Voice input stopped.';rec.onresult=e=>{let text=e.results[0][0].transcript;$('botInput').value=text;askBot(text)};rec.start()} async function runScan(){let out=$('adminOut');if(out)out.textContent='Running live scan...';let r=await api('/api/run-scan',{});if(out)out.textContent=r.output;await load();openTab('radar')} renderTabs();load();setInterval(load,6000);
</script></body></html>"""

def run():
    init_db(); server=http.server.ThreadingHTTPServer((HOST,PORT),Handler); print(f'Hancock Live Site running at http://{HOST}:{PORT}'); print(f'Initial logins: {INITIAL_LOGINS}'); server.serve_forever()
if __name__=='__main__': run()
