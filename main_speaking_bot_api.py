#!/usr/bin/env python3
"""Tiny local API for the Main Speaking Bot feed."""
import json
import subprocess
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
FEED = ROOT / 'data' / 'main_speaking_bot_feed.json'
PORT = 8777

class Handler(BaseHTTPRequestHandler):
    def json_response(self, obj, code=200):
        data=json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def do_OPTIONS(self):
        self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS'); self.end_headers()
    def do_GET(self):
        if self.path.startswith('/api/briefing'):
            if not FEED.exists():
                subprocess.run(['python3','bot_council.py'], cwd=str(ROOT), timeout=90)
            try: self.json_response(json.loads(FEED.read_text(encoding='utf-8')))
            except Exception as e: self.json_response({'error':str(e)},500)
            return
        if self.path.startswith('/api/status'):
            self.json_response({'ok':True,'feedExists':FEED.exists(),'endpoint':'/api/briefing','scanEndpoint':'/api/scan'})
            return
        self.json_response({'error':'not found'},404)
    def do_POST(self):
        if self.path.startswith('/api/scan'):
            result=subprocess.run(['python3','bot_council.py'], cwd=str(ROOT), text=True, capture_output=True, timeout=120)
            ok=result.returncode==0
            payload={'ok':ok,'output':(result.stdout+result.stderr)[-5000:]}
            if FEED.exists():
                try: payload['briefing']=json.loads(FEED.read_text(encoding='utf-8')).get('mainSpeakingBot')
                except Exception: pass
            self.json_response(payload, 200 if ok else 500)
            return
        self.json_response({'error':'not found'},404)

if __name__ == '__main__':
    print(f'Main Speaking Bot API running at http://127.0.0.1:{PORT}')
    print('GET  /api/briefing')
    print('POST /api/scan')
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
