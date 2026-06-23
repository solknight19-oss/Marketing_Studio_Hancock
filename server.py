#!/usr/bin/env python3
import base64
import datetime as dt
import hashlib
import hmac
import html
import http.cookies
import http.server
import json
import os
import secrets
import sqlite3
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = Path(os.environ.get('APP_DATA_DIR', str(ROOT / 'app_data')))
APP.mkdir(parents=True, exist_ok=True)
DB = APP / 'studio.db'
SECRET_FILE = APP / '.session_secret'
INITIAL_LOGINS = APP / 'INITIAL_LOGINS.md'
SESSION_DAYS = 7
INVITE_HOURS = 24
RESET_HOURS = 1
PORT = int(os.environ.get('PORT', '8765'))
HOST = os.environ.get('HOST', '0.0.0.0')
BASE_URL = os.environ.get('BASE_URL', '').rstrip('/')
ALLOWED_EMAIL_DOMAIN = os.environ.get('ALLOWED_EMAIL_DOMAIN', 'hancockclaims.com').strip().lower()
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '').strip()
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'Hancock Marketing Studio <studio@hancockclaims.com>').strip()
USERS = [
    ('admin', 'rknight@hancockclaims.com', 'Ryan Knight', 'owner'),
    ('cassie', 'ctant@hancockclaims.com', 'Cassie Tant', 'admin'),
    ('jennifer', 'jwalker@hancockclaims.com', 'Jennifer Walker', 'admin'),
]
PASSWORD_ENV_VARS = {
    'admin': 'ADMIN_PASSWORD',
}
SERVICE_LINES = ['Storm / CAT Damage','Underwriting Inspection','Contents','Engineering','Commercial','Residential','4-Point Inspection','Ladder Assist','Loss Control','DI / UDI Inspections']
RATE_LIMITS = {}

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
    iterations = 310000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
    return f'{iterations}${salt}$' + base64.b64encode(digest).decode()
def check_password(password, stored):
    try:
        parts = stored.split('$')
        if len(parts) == 3:
            iterations, salt, expected = int(parts[0]), parts[1], parts[2]
            digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
            return hmac.compare_digest(base64.b64encode(digest).decode(), expected)
        salt, expected = stored.split('$', 1)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 180000)
        return hmac.compare_digest(base64.b64encode(digest).decode(), expected)
    except (ValueError, TypeError):
        return False
def valid_password(password):
    if len(password) < 12: return 'Use at least 12 characters.'
    if not any(c.islower() for c in password): return 'Add a lowercase letter.'
    if not any(c.isupper() for c in password): return 'Add an uppercase letter.'
    if not any(c.isdigit() for c in password): return 'Add a number.'
    if not any(not c.isalnum() for c in password): return 'Add a symbol.'
    return ''
def valid_hancock_email(email):
    email = email.strip().lower()
    return '@' in email and email.rsplit('@', 1)[1] == ALLOWED_EMAIL_DOMAIN
def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()
def public_url(handler):
    if BASE_URL: return BASE_URL
    proto = handler.headers.get('X-Forwarded-Proto', 'http').split(',')[0].strip()
    return f"{proto}://{handler.headers.get('Host', f'127.0.0.1:{PORT}')}"
def send_email(to_email, subject, text, html_body):
    if not RESEND_API_KEY:
        raise RuntimeError('Email delivery is not configured. Add RESEND_API_KEY in Render.')
    payload = json.dumps({'from': EMAIL_FROM, 'to': [to_email], 'subject': subject, 'text': text, 'html': html_body}).encode()
    request = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode() or '{}')
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors='replace')[:500]
        raise RuntimeError(f'Email service rejected the message: {detail}') from exc
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con
def create_access_token(user_id, purpose, hours):
    raw = secrets.token_urlsafe(40)
    expires = (dt.datetime.now() + dt.timedelta(hours=hours)).isoformat(timespec='seconds')
    con = db()
    con.execute('delete from access_tokens where user_id=? and purpose=? and used_at is null', (user_id, purpose))
    con.execute('insert into access_tokens(token_hash,user_id,purpose,expires_at,created_at) values(?,?,?,?,?)',
                (token_hash(raw), user_id, purpose, expires, now()))
    con.commit(); con.close()
    return raw

def init_db():
    con = db(); cur = con.cursor()
    cur.executescript("""
    create table if not exists users(id integer primary key autoincrement, username text unique not null, email text, name text not null, role text not null, password_hash text not null, created_at text not null);
    create table if not exists sessions(token text primary key, user_id integer not null, expires_at text not null);
    create table if not exists access_tokens(id integer primary key autoincrement, token_hash text unique not null, user_id integer not null, purpose text not null, expires_at text not null, used_at text, created_at text not null);
    create table if not exists settings(key text primary key, value text not null);
    create table if not exists drafts(id integer primary key autoincrement, title text not null, content_type text not null, service_line text, body text not null, status text not null, owner_id integer, updated_by integer, created_at text not null, updated_at text not null);
    create table if not exists tasks(id integer primary key autoincrement, title text not null, details text, status text not null, assigned_to integer, created_by integer, created_at text not null, updated_at text not null);
    create table if not exists activity(id integer primary key autoincrement, user_id integer, action text not null, meta text, created_at text not null);
    """)
    user_columns = {row['name'] for row in cur.execute('pragma table_info(users)')}
    if 'email' not in user_columns:
        cur.execute('alter table users add column email text')
    if 'password_reset_required' not in user_columns:
        cur.execute('alter table users add column password_reset_required integer not null default 0')
    cur.execute('create unique index if not exists users_email_unique on users(lower(email)) where email is not null and email != ""')
    cur.execute("update users set email=?,role='owner' where username='admin'", ('rknight@hancockclaims.com',))
    cur.execute("update users set password_reset_required=case when email is null or email='' then 1 else password_reset_required end,email=?,role='admin' where username='cassie'", ('ctant@hancockclaims.com',))
    cur.execute("update users set password_reset_required=case when email is null or email='' then 1 else password_reset_required end,email=?,role='admin' where username='jennifer'", ('jwalker@hancockclaims.com',))
    if cur.execute('select count(*) as n from users').fetchone()['n'] == 0:
        lines=['# Initial Live Studio Owner Login','','Use this only for initial owner access, then use the secure reset flow.','']
        ids={}
        for username, email, name, role in USERS:
            pw=os.environ.get(PASSWORD_ENV_VARS.get(username, ''), '').strip() or secrets.token_urlsafe(24)
            reset_required=0 if role == 'owner' else 1
            cur.execute('insert into users(username,email,name,role,password_hash,password_reset_required,created_at) values(?,?,?,?,?,?,?)',(username,email or None,name,role,password_hash(pw),reset_required,now()))
            ids[username]=cur.lastrowid
            if role == 'owner':
                lines.append(f'- {name}: login `{email}`, password `{pw}`')
        INITIAL_LOGINS.write_text('\n'.join(lines)+'\n', encoding='utf-8')
        try: INITIAL_LOGINS.chmod(0o600)
        except Exception: pass
        cur.execute('insert into tasks(title,details,status,assigned_to,created_by,created_at,updated_at) values(?,?,?,?,?,?,?)',("Review today's Industry Radar",'Pick one live trend and turn it into a Hancock post or article.','todo',ids.get('cassie'),ids.get('admin'),now(),now()))
        cur.execute('insert into tasks(title,details,status,assigned_to,created_by,created_at,updated_at) values(?,?,?,?,?,?,?)',('Complete first article draft','Use the bot suggestions, add the Hancock angle, and move the draft to Ready for Review.','todo',ids.get('jennifer'),ids.get('admin'),now(),now()))
    bootstrap_password=os.environ.get('ADMIN_PASSWORD', '').strip()
    bootstrapped=cur.execute("select value from settings where key='owner_bootstrap_applied'").fetchone()
    if bootstrap_password and not bootstrapped:
        cur.execute("update users set password_hash=?,password_reset_required=0 where username='admin'",(password_hash(bootstrap_password),))
        cur.execute("insert into settings(key,value) values('owner_bootstrap_applied',?)",(now(),))
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
        data=text.encode('utf-8'); self.send_response(code); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('X-Frame-Options','DENY'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def send_json(self,obj,code=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8'); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def redirect(self,path): self.send_response(302); self.send_header('Location',path); self.end_headers()
    def secure_cookie(self):
        return self.headers.get('X-Forwarded-Proto', '').split(',')[0].strip().lower() == 'https'
    def client_ip(self):
        return self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
    def rate_limited(self, action, limit=5, minutes=15):
        key=(self.client_ip(), action); cutoff=dt.datetime.now()-dt.timedelta(minutes=minutes)
        recent=[stamp for stamp in RATE_LIMITS.get(key, []) if stamp > cutoff]
        if len(recent) >= limit:
            RATE_LIMITS[key]=recent
            return True
        recent.append(dt.datetime.now()); RATE_LIMITS[key]=recent
        return False
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
        if path=='/forgot': self.send_html(FORGOT_HTML); return
        if path=='/reset':
            token=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('token',[''])[0]
            if not self.lookup_access_token(token):
                self.send_html(message_page('Link unavailable','This setup or reset link is invalid, expired, or already used.'),400); return
            self.send_html(reset_page(token)); return
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
        if path=='/forgot': self.handle_forgot(); return
        if path=='/reset': self.handle_reset(); return
        if path=='/logout': self.send_response(302); self.send_header('Location','/login'); self.send_header('Set-Cookie','hms_session=; Max-Age=0; Path=/'); self.end_headers(); return
        user=self.require_user();
        if not user: return
        if path=='/api/draft': self.api_save_draft(user); return
        if path=='/api/task': self.api_save_task(user); return
        if path=='/api/bot': self.api_bot(user); return
        if path=='/api/run-scan': self.api_run_scan(user); return
        if path=='/api/run-council': self.api_run_council(user); return
        if path=='/api/invite': self.api_invite(user); return
        self.send_json({'error':'not found'},404)
    def handle_login(self):
        data=self.read_body(); username=(data.get('username') or '').strip().lower(); password=data.get('password') or ''
        con=db(); row=con.execute('select * from users where lower(username)=? or lower(email)=?', (username, username)).fetchone()
        if self.rate_limited('login', 10, 15):
            con.close(); self.send_html(LOGIN_HTML.replace('<!--ERR-->','<div class="err">Too many attempts. Wait 15 minutes and try again.</div>'),429); return
        if row and check_password(password,row['password_hash']) and not row['password_reset_required']:
            token=secrets.token_urlsafe(32); expires=(dt.datetime.now()+dt.timedelta(days=SESSION_DAYS)).isoformat(timespec='seconds')
            con.execute('insert into sessions(token,user_id,expires_at) values(?,?,?)',(token,row['id'],expires)); con.commit(); con.close(); log_action(row['id'],'logged in')
            secure='; Secure' if self.secure_cookie() else ''
            self.send_response(302); self.send_header('Location','/dashboard'); self.send_header('Set-Cookie',f'hms_session={sign(token)}; HttpOnly; SameSite=Lax; Path=/{secure}'); self.end_headers()
        else:
            con.close(); self.send_html(LOGIN_HTML.replace('<!--ERR-->','<div class="err">Login failed. Check your email and password, or use Forgot password.</div>'),401)
    def lookup_access_token(self, token):
        if not token: return None
        con=db()
        row=con.execute('select t.*,u.email,u.name from access_tokens t join users u on u.id=t.user_id where t.token_hash=? and t.used_at is null and t.expires_at>?',
                        (token_hash(token), now())).fetchone()
        con.close()
        return rowdict(row)
    def handle_forgot(self):
        if self.rate_limited('forgot', 5, 30):
            self.send_html(message_page('Check your email','If that address is authorized, a reset link will arrive shortly.')); return
        data=self.read_body(); email=(data.get('email') or '').strip().lower()
        con=db(); row=con.execute('select * from users where lower(email)=?', (email,)).fetchone(); con.close()
        if row and valid_hancock_email(email):
            token=create_access_token(row['id'], 'reset', RESET_HOURS)
            link=f'{public_url(self)}/reset?token={urllib.parse.quote(token)}'
            try:
                send_email(
                    email,
                    'Reset your Hancock Marketing Studio password',
                    f'Use this secure link within {RESET_HOURS} hour to reset your password: {link}',
                    email_template('Reset your password', f'Use this secure link within {RESET_HOURS} hour. If you did not request this, ignore this email.', link, 'Reset password'),
                )
            except RuntimeError as exc:
                print(f'Password reset email failed for {email}: {exc}')
        self.send_html(message_page('Check your email','If that address is authorized, a secure reset link will arrive shortly.'))
    def handle_reset(self):
        if self.rate_limited('reset', 10, 30):
            self.send_html(message_page('Try again later','Too many password attempts. Wait 30 minutes.'),429); return
        data=self.read_body(); token=data.get('token') or ''; password=data.get('password') or ''; confirm=data.get('confirm') or ''
        access=self.lookup_access_token(token)
        if not access:
            self.send_html(message_page('Link unavailable','This setup or reset link is invalid, expired, or already used.'),400); return
        error=valid_password(password)
        if password != confirm: error='The passwords do not match.'
        if error:
            self.send_html(reset_page(token, error),400); return
        con=db()
        con.execute('update users set password_hash=?,password_reset_required=0 where id=?',(password_hash(password),access['user_id']))
        con.execute('update access_tokens set used_at=? where token_hash=?',(now(),token_hash(token)))
        con.execute('delete from sessions where user_id=?',(access['user_id'],))
        con.commit(); con.close()
        log_action(access['user_id'],'set a secure password')
        self.send_html(message_page('Password saved','Your account is ready. Sign in with your Hancock email.', '/login', 'Sign in'))
    def api_invite(self,user):
        if user['role'] not in ('owner','admin'):
            self.send_json({'error':'admin access required'},403); return
        if self.rate_limited('invite', 10, 60):
            self.send_json({'error':'invite limit reached; try again later'},429); return
        data=self.read_body(); user_id=str(data.get('user_id') or '').strip(); email=(data.get('email') or '').strip().lower()
        if not user_id.isdigit() or not valid_hancock_email(email):
            self.send_json({'error':f'Use an authorized @{ALLOWED_EMAIL_DOMAIN} email address.'},400); return
        con=db(); target=con.execute('select * from users where id=?',(int(user_id),)).fetchone()
        conflict=con.execute('select id from users where lower(email)=? and id!=?',(email,int(user_id))).fetchone()
        if not target or conflict:
            con.close(); self.send_json({'error':'That account or email cannot be invited.'},400); return
        con.execute('update users set email=?,password_reset_required=1 where id=?',(email,int(user_id)))
        con.execute('delete from sessions where user_id=?',(int(user_id),)); con.commit(); con.close()
        token=create_access_token(int(user_id), 'invite', INVITE_HOURS)
        link=f'{public_url(self)}/reset?token={urllib.parse.quote(token)}'
        try:
            send_email(
                email,
                'Your Hancock Marketing Studio invitation',
                f'{user["name"]} invited you to the Hancock Marketing Studio. Create your password within {INVITE_HOURS} hours: {link}',
                email_template('You are invited', f'{html.escape(user["name"])} invited you to the Hancock Marketing Studio. This secure link expires in {INVITE_HOURS} hours.', link, 'Create my password'),
            )
        except RuntimeError as exc:
            con=db()
            con.execute('update users set email=?,password_reset_required=? where id=?',
                        (target['email'], target['password_reset_required'], int(user_id)))
            con.execute('delete from access_tokens where token_hash=?',(token_hash(token),))
            con.commit(); con.close()
            self.send_json({'error':str(exc)},502); return
        log_action(user['id'],'invited user',f'{target["name"]} ({email})')
        self.send_json({'ok':True,'message':f'Invitation sent to {email}.'})
    def api_state(self,user):
        con=db()
        users=[dict(r) for r in con.execute('select id,username,email,name,role,password_reset_required from users order by name')]
        drafts=[dict(r) for r in con.execute('select d.*, u.name owner_name, uu.name updated_by_name from drafts d left join users u on u.id=d.owner_id left join users uu on uu.id=d.updated_by order by d.updated_at desc limit 50')]
        tasks=[dict(r) for r in con.execute("select t.*, u.name assigned_name, c.name created_by_name from tasks t left join users u on u.id=t.assigned_to left join users c on c.id=t.created_by order by case t.status when 'doing' then 0 when 'todo' then 1 when 'review' then 2 else 3 end, t.updated_at desc")]
        activity=[dict(r) for r in con.execute('select a.*, u.name user_name from activity a left join users u on u.id=a.user_id order by a.id desc limit 30')]
        con.close()
        for collection in (drafts,tasks,activity):
            for item in collection:
                for key in ('created_at','updated_at'):
                    if key in item: item[key+'_human']=human_time(item.get(key))
        self.send_json({'user':{k:user[k] for k in ('id','username','email','name','role')},'users':users,'drafts':drafts,'tasks':tasks,'activity':activity,'botData':latest_bot_data(),'serviceLines':SERVICE_LINES,'welcome':bot_welcome(user,tasks,drafts,activity)})
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

AUTH_STYLE = """:root{--navy:#1D4F91;--blue:#2F6FBF;--bg:#EFF2F7;--border:#E3E9F2;--text:#15243C}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(900px 400px at 80% -5%,#E4EAF4 0%,var(--bg) 55%);font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--text)}.card{width:min(440px,92vw);background:#fff;border:1px solid var(--border);border-radius:18px;padding:28px;box-shadow:0 20px 60px rgba(21,36,60,.14)}.brand{display:flex;gap:12px;align-items:center;margin-bottom:18px}.mark{width:48px;height:48px;border-radius:8px;background:var(--navy);color:#fff;display:grid;place-items:center;font-weight:900}.eyebrow{font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;color:var(--blue)}h1{margin:0;color:var(--navy);font-size:25px}p{color:#5B6B82;line-height:1.5}label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#5B6B82;font-weight:900;margin:16px 0 7px}input{width:100%;border:1px solid var(--border);border-radius:8px;padding:12px}input:focus{outline:2px solid #4F93E0;outline-offset:1px;border-color:#4F93E0}button,.button{display:block;width:100%;border:0;border-radius:8px;background:var(--navy);color:white;font-weight:900;padding:13px;margin-top:18px;cursor:pointer;text-align:center;text-decoration:none}.link{display:block;text-align:center;margin-top:15px;color:var(--navy);font-weight:700;text-decoration:none}.err{background:#fff1f1;border:1px solid #ffd0d0;color:#9a1a1a;padding:10px;border-radius:8px;margin-bottom:12px}.note{font-size:12px;color:#5B6B82}"""

def auth_shell(title, body):
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)} · Hancock Marketing Studio</title><style>{AUTH_STYLE}</style></head><body><main class='card'><div class='brand'><div class='mark'>H</div><div><div class='eyebrow'>Live Marketing Studio</div><h1>{html.escape(title)}</h1></div></div>{body}</main></body></html>"""
def message_page(title, message, href='', button=''):
    action=f"<a class='button' href='{html.escape(href)}'>{html.escape(button)}</a>" if href else ''
    return auth_shell(title, f"<p>{html.escape(message)}</p>{action}")
def reset_page(token, error=''):
    err=f"<div class='err'>{html.escape(error)}</div>" if error else ''
    return auth_shell('Create your password', f"""{err}<p>Use at least 12 characters with uppercase, lowercase, a number, and a symbol.</p><form method='post' action='/reset'><input type='hidden' name='token' value='{html.escape(token)}'><label>New password</label><input name='password' type='password' autocomplete='new-password' required minlength='12'><label>Confirm password</label><input name='confirm' type='password' autocomplete='new-password' required minlength='12'><button>Save secure password</button></form>""")
def email_template(title, message, link, button):
    return f"""<!doctype html><html><body style="margin:0;background:#eff2f7;font-family:Arial,sans-serif;color:#15243c"><div style="max-width:560px;margin:30px auto;background:#fff;border:1px solid #e3e9f2;padding:28px"><div style="font-weight:800;color:#1d4f91">Hancock Claims Consultants</div><h1 style="font-size:24px;color:#1d4f91">{html.escape(title)}</h1><p style="line-height:1.6">{message}</p><p><a href="{html.escape(link)}" style="display:inline-block;background:#1d4f91;color:#fff;text-decoration:none;padding:12px 18px;font-weight:700">{html.escape(button)}</a></p><p style="font-size:12px;color:#5b6b82">For security, this link can only be used once.</p></div></body></html>"""

LOGIN_HTML = auth_shell('Sign in', """<!--ERR--><p>Use your authorized Hancock email and private password.</p><form method='post' action='/login'><label>Hancock email</label><input name='username' type='email' autocomplete='username' autofocus required><label>Password</label><input name='password' type='password' autocomplete='current-password' required><button>Open Studio</button></form><a class='link' href='/forgot'>Forgot password?</a>""")
FORGOT_HTML = auth_shell('Reset password', """<p>Enter your Hancock email. If the account is authorized, we will send a secure one-time reset link.</p><form method='post' action='/forgot'><label>Hancock email</label><input name='email' type='email' autocomplete='email' required><button>Send reset link</button></form><a class='link' href='/login'>Back to sign in</a>""")

DASHBOARD_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hancock Live Marketing Studio</title><style>
:root{--navy:#1D4F91;--navy2:#163E74;--gold:#4F93E0;--gold2:#D7E8FB;--bg:#EFF2F7;--text:#15243C;--sub:#5B6B82;--border:#E3E9F2;--card:#fff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 400px at 80% -5%,#E4EAF4 0%,var(--bg) 55%);color:var(--text);font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,select,textarea{font:inherit}button{cursor:pointer}.header{position:sticky;top:0;z-index:10;background:linear-gradient(112deg,#0E2A52 0%,var(--navy2) 44%,var(--navy) 100%);color:#fff;box-shadow:0 10px 28px rgba(14,42,82,.22)}.top{display:flex;justify-content:space-between;gap:16px;align-items:center;padding:18px 24px}.brand h1{margin:0;font-size:21px}.brand p{margin:4px 0 0;color:#A8C2E8;font-size:12px}.tabs{display:flex;gap:4px;overflow-x:auto;padding:0 20px}.tab{border:0;background:transparent;color:#B9C8E0;border-radius:12px 12px 0 0;padding:12px 14px;font-weight:900}.tab.active{background:var(--bg);color:var(--navy)}main{max-width:1280px;margin:0 auto;padding:24px}.view{display:none}.view.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}.layout{display:grid;grid-template-columns:380px 1fr;gap:18px}.card,.panel{background:var(--card);border:1px solid var(--border);border-radius:18px;box-shadow:0 8px 25px rgba(21,36,60,.055);padding:18px}.hero{background:linear-gradient(135deg,#0E2A52,var(--navy));color:#fff;border-radius:20px;padding:22px;display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center;margin-bottom:18px}.hero h2{margin:4px 0 6px}.hero p{color:#cfe0f4;margin:0}.eyebrow{font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;color:var(--gold2)}label{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--sub);font-weight:900;margin:14px 0 7px}input,select,textarea{width:100%;border:1px solid var(--border);border-radius:12px;padding:11px;background:#FBFDFF}textarea{min-height:150px;resize:vertical}.btn{border:0;border-radius:12px;background:var(--navy);color:#fff;font-weight:900;padding:11px 14px;margin-top:12px}.btn.gold{background:linear-gradient(135deg,var(--gold),var(--gold2));color:#112b50}.btn.secondary{background:#edf4fb;color:var(--navy);border:1px solid #d6e3f3}.mini{border:1px solid #d8e4f2;background:#fff;color:var(--navy);border-radius:10px;font-size:12px;font-weight:800;padding:8px 10px;margin:5px 5px 0 0}.badge{display:inline-flex;border-radius:7px;background:#eef5ff;color:var(--navy);font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;padding:5px 8px}.badge.hot{background:#ffe9e9;color:#9a1a1a}.muted{color:var(--sub);font-size:13px}.activity{display:flex;flex-direction:column;gap:9px}.activity div{border-left:3px solid var(--gold);padding-left:10px;color:#41516a}.task{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:start;border-top:1px solid var(--border);padding:12px 0}.task:first-child{border-top:0}.botreply{background:#f8fbff;border:1px solid #dce8f7;border-left:4px solid var(--gold);border-radius:14px;padding:13px;line-height:1.45}.chatrow{display:flex;gap:8px;margin-top:10px}.chatrow input{flex:1}.draftList{display:grid;gap:12px}.draftItem{border:1px solid var(--border);border-radius:14px;padding:14px;background:#fff}.out{white-space:pre-wrap;line-height:1.55}.adminbar{display:flex;gap:8px;flex-wrap:wrap}.who{font-size:12px;color:#cfe0f4}.logout{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.25);padding:8px 10px;border-radius:10px}.status{font-size:12px;color:var(--sub);min-height:18px}@media(max-width:900px){.layout,.hero{grid-template-columns:1fr}.top{padding:16px}main{padding:16px}}
</style></head><body>
<header class="header"><div class="top"><div class="brand"><h1>Hancock Live Marketing Studio</h1><p>Shared drafts, live scans, task focus, and bot guidance</p></div><div><div class="who" id="who"></div><form method="post" action="/logout" style="display:inline"><button class="logout" style="background:transparent">Logout</button></form></div></div><nav class="tabs" id="tabs"></nav></header>
<main>
<section id="dash" class="view active"><div class="hero"><div><div class="eyebrow">Welcome Bot</div><h2 id="welcomeTitle">Good to see you.</h2><p id="welcomeText">Loading workspace guidance...</p></div><div><button class="btn gold" onclick="askBot('What should I focus on next?')">What next?</button><button class="btn secondary" onclick="openTab('radar')">Open Radar</button></div></div><div class="grid"><div class="card"><h3>Bot Coach</h3><div class="botreply" id="botReply">Ask me what to work on, what the other user is doing, or what article to create next.</div><div class="chatrow"><input id="botInput" placeholder="Ask the bot..."><button class="mini" onclick="sendBot()">Send</button><button class="mini" onclick="voiceAsk()">Voice</button></div><div class="status" id="voiceStatus"></div></div><div class="card"><h3>Activity</h3><div class="activity" id="activity"></div></div><div class="card"><h3>Open Tasks</h3><div id="taskPreview"></div></div></div></section>
<section id="radar" class="view"><div class="hero"><div><div class="eyebrow">Live Industry Radar</div><h2>Fresh signals from the marketing bot</h2><p id="scanStamp">Loading scan data...</p></div><button class="btn gold" onclick="runScan()">Run Live Scan</button></div><div id="radarGrid" class="grid"></div></section>
<section id="drafts" class="view"><div class="layout"><div class="card"><h3>Create / Edit Draft</h3><input type="hidden" id="draftId"><label>Title</label><input id="draftTitle"><label>Type</label><select id="draftType"><option>Blog Post</option><option>LinkedIn Post</option><option>Email</option><option>Website Update</option><option>FAQ</option></select><label>Service Line</label><select id="draftLine"></select><label>Status</label><select id="draftStatus"><option>draft</option><option>doing</option><option>review</option><option>approved</option></select><label>Body</label><textarea id="draftBody"></textarea><button class="btn" onclick="saveDraft()">Save Shared Draft</button><button class="btn secondary" onclick="clearDraftForm()">New Blank Draft</button><div class="status" id="draftSaveStatus"></div></div><div class="panel"><h3>Shared Drafts</h3><div id="draftList" class="draftList"></div></div></div></section>
<section id="tasks" class="view"><div class="layout"><div class="card"><h3>Create / Edit Task</h3><input type="hidden" id="taskId"><label>Task</label><input id="taskTitle"><label>Details</label><textarea id="taskDetails"></textarea><label>Assign To</label><select id="taskAssigned"></select><label>Status</label><select id="taskStatus"><option>todo</option><option>doing</option><option>review</option><option>done</option></select><button class="btn" onclick="saveTask()">Save Task</button><button class="btn secondary" onclick="clearTaskForm()">New Task</button><div class="status" id="taskSaveStatus"></div></div><div class="panel"><h3>Team Tasks</h3><div id="taskList"></div></div></div></section>
<section id="admin" class="view"><div class="grid"><div class="card"><h3>Invite Team Member</h3><p class="muted">Send a secure, one-time setup link to an authorized Hancock email. The link expires after 24 hours.</p><label>Team member</label><select id="inviteUser"></select><label>Hancock email</label><input id="inviteEmail" type="email" placeholder="name@hancockclaims.com"><button class="btn" onclick="sendInvite()">Send Secure Invitation</button><div class="status" id="inviteStatus"></div></div><div class="card"><h3>Studio Administration</h3><p class="muted">Ryan is the owner. Cassie and Jennifer have administrator access after accepting their invitations.</p><div class="adminbar"><button class="btn" onclick="location.href='/studio'">Open Approved Studio</button><button class="btn secondary" onclick="runScan()">Run Bot Scan</button></div><pre class="out" id="adminOut"></pre></div></div></section>
</main><script>
let STATE={}; const TABLIST=[['dash','Dashboard'],['radar','Industry Radar'],['drafts','Drafts'],['tasks','Tasks'],['admin','Admin']]; function $(id){return document.getElementById(id)} function esc(s){return String(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))} function openTab(id){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===id));document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===id));} function renderTabs(){ $('tabs').innerHTML=TABLIST.map((t,i)=>`<button class="tab ${i?'':'active'}" data-tab="${t[0]}" onclick="openTab('${t[0]}')">${t[1]}</button>`).join('') } async function api(path, body){let opt=body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{};let r=await fetch(path,opt);let data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed');return data} async function load(){STATE=await api('/api/state');render()} function render(){ $('who').textContent=STATE.user.name+' · '+STATE.user.role; $('welcomeTitle').textContent='Hi, '+STATE.user.name.split(' ')[0]+'.'; $('welcomeText').textContent=STATE.welcome; $('botReply').textContent=STATE.welcome; renderUsers();renderActivity();renderTasks();renderDrafts();renderRadar()} function renderUsers(){let opts='<option value="">Unassigned</option>'+STATE.users.map(u=>`<option value="${u.id}">${esc(u.name)}</option>`).join('');$('taskAssigned').innerHTML=opts;$('draftLine').innerHTML=STATE.serviceLines.map(x=>`<option>${esc(x)}</option>`).join('');$('inviteUser').innerHTML=STATE.users.map(u=>`<option value="${u.id}" data-email="${esc(u.email||'')}">${esc(u.name)} · ${esc(u.role)}</option>`).join('');$('inviteUser').onchange=()=>{let o=$('inviteUser').selectedOptions[0];$('inviteEmail').value=o?o.dataset.email:''};$('inviteUser').onchange()} function renderActivity(){ $('activity').innerHTML=(STATE.activity||[]).slice(0,8).map(a=>`<div><b>${esc(a.user_name||'System')}</b> ${esc(a.action)} ${esc(a.meta||'')}<br><span class="muted">${esc(a.created_at_human||'')}</span></div>`).join('')||'<p class="muted">No activity yet.</p>'} function taskHtml(t){return `<div class="task"><div><span class="badge">${esc(t.status)}</span><h4>${esc(t.title)}</h4><p class="muted">${esc(t.details||'')}<br>Assigned: ${esc(t.assigned_name||'Unassigned')} · Updated ${esc(t.updated_at_human||'')}</p></div><div><button class="mini" onclick="editTask(${t.id})">Edit</button><button class="mini" onclick="quickTask(${t.id},'doing')">Doing</button><button class="mini" onclick="quickTask(${t.id},'done')">Done</button></div></div>`} function renderTasks(){let open=(STATE.tasks||[]).filter(t=>t.status!=='done');$('taskPreview').innerHTML=open.slice(0,4).map(taskHtml).join('')||'<p class="muted">No open tasks.</p>';$('taskList').innerHTML=(STATE.tasks||[]).map(taskHtml).join('')} function renderDrafts(){ $('draftList').innerHTML=(STATE.drafts||[]).map(d=>`<div class="draftItem"><span class="badge">${esc(d.status)}</span><h3>${esc(d.title)}</h3><p class="muted">${esc(d.content_type)} · ${esc(d.service_line||'')} · owner ${esc(d.owner_name||'')} · updated ${esc(d.updated_at_human||'')}</p><p>${esc((d.body||'').slice(0,260))}...</p><button class="mini" onclick="editDraft(${d.id})">Edit</button><button class="mini" onclick="copyDraft(${d.id})">Copy</button></div>`).join('')||'<p class="muted">No shared drafts yet.</p>'} function renderRadar(){let b=STATE.botData||{};$('scanStamp').textContent=(b.generatedHuman||'No scan yet')+' · '+(b.source||'');$('radarGrid').innerHTML=(b.stories||[]).slice(0,12).map((s,i)=>`<div class="card"><span class="badge ${s.tag==='Hot'?'hot':''}">${esc(s.tag||'Trend')}</span><h3>${esc(s.title)}</h3><p>${esc(s.summary)}</p><p><b>Hancock angle:</b> ${esc(s.angle)}</p><p class="muted">${esc(s.source||'')} ${s.date?'· '+esc(s.date):''}</p><button class="mini" onclick="draftFromRadar(${i})">Draft from this</button></div>`).join('')||'<div class="card"><p>No scan data yet. Run Live Scan.</p></div>'} function editDraft(id){let d=STATE.drafts.find(x=>x.id===id);if(!d)return;$('draftId').value=d.id;$('draftTitle').value=d.title;$('draftType').value=d.content_type;$('draftLine').value=d.service_line||STATE.serviceLines[0];$('draftStatus').value=d.status;$('draftBody').value=d.body;openTab('drafts')} function copyDraft(id){let d=STATE.drafts.find(x=>x.id===id); if(d)navigator.clipboard.writeText(d.body||'')} function clearDraftForm(){['draftId','draftTitle','draftBody'].forEach(id=>$(id).value='');$('draftStatus').value='draft'} async function saveDraft(){await api('/api/draft',{id:$('draftId').value,title:$('draftTitle').value,content_type:$('draftType').value,service_line:$('draftLine').value,status:$('draftStatus').value,body:$('draftBody').value});$('draftSaveStatus').textContent='Saved.';await load()} function draftFromRadar(i){let s=STATE.botData.stories[i];clearDraftForm();$('draftTitle').value=s.title;$('draftLine').value=s.line||STATE.serviceLines[0];$('draftBody').value='# '+s.title+'\n\n'+s.summary+'\n\n## Hancock angle\n'+s.angle+'\n\n## Next step\nTurn this into a useful post with a clear carrier-facing takeaway.';openTab('drafts')} function editTask(id){let t=STATE.tasks.find(x=>x.id===id);if(!t)return;$('taskId').value=t.id;$('taskTitle').value=t.title;$('taskDetails').value=t.details||'';$('taskAssigned').value=t.assigned_to||'';$('taskStatus').value=t.status;openTab('tasks')} function clearTaskForm(){['taskId','taskTitle','taskDetails'].forEach(id=>$(id).value='');$('taskStatus').value='todo';$('taskAssigned').value=''} async function saveTask(){await api('/api/task',{id:$('taskId').value,title:$('taskTitle').value,details:$('taskDetails').value,assigned_to:$('taskAssigned').value,status:$('taskStatus').value});$('taskSaveStatus').textContent='Saved.';await load()} async function quickTask(id,status){let t=STATE.tasks.find(x=>x.id===id);await api('/api/task',{id:id,title:t.title,details:t.details,assigned_to:t.assigned_to,status:status});await load()} async function askBot(msg){$('botReply').textContent='Thinking...';let r=await api('/api/bot',{message:msg});$('botReply').textContent=r.reply;speak(r.reply)} function sendBot(){let m=$('botInput').value.trim();if(!m)return;askBot(m);$('botInput').value=''} function speak(text){if(!('speechSynthesis' in window))return;let u=new SpeechSynthesisUtterance(text);u.rate=.95;window.speechSynthesis.cancel();window.speechSynthesis.speak(u)} function voiceAsk(){let SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){$('voiceStatus').textContent='Voice input is not available in this browser. Use the text box.';return}let rec=new SR();rec.lang='en-US';rec.onstart=()=>$('voiceStatus').textContent='Listening...';rec.onerror=()=>$('voiceStatus').textContent='Voice input stopped.';rec.onresult=e=>{let text=e.results[0][0].transcript;$('botInput').value=text;askBot(text)};rec.start()} async function runScan(){let out=$('adminOut');if(out)out.textContent='Running live scan...';let r=await api('/api/run-scan',{});if(out)out.textContent=r.output;await load();openTab('radar')} async function sendInvite(){let status=$('inviteStatus');status.textContent='Sending secure invitation...';try{let r=await api('/api/invite',{user_id:$('inviteUser').value,email:$('inviteEmail').value});status.textContent=r.message;await load()}catch(e){status.textContent=e.message}} renderTabs();load();setInterval(load,6000);
</script></body></html>"""

def run():
    init_db(); server=http.server.ThreadingHTTPServer((HOST,PORT),Handler); print(f'Hancock Live Site running at http://{HOST}:{PORT}'); print(f'Initial logins: {INITIAL_LOGINS}'); server.serve_forever()
if __name__=='__main__': run()
