# Dave Voice Recognition Review Packet

Paste this to Claude. It contains only the relevant Dave voice/mic code and known facts. Do not paste API keys.

## What We Need Reviewed

Dave is an Electron desktop assistant. The user clicks `Live Mic`, speaks, Dave records a short audio turn, sends it to the local Python server, the server transcribes it, routes the text through Dave chat, and Dave replies with ElevenLabs TTS.

Main question: after STT credentials are fixed, is there any remaining mic lifecycle issue that would cause Dave to stop, restart, or bounce unnecessarily?

## Known Hard Blocker

The current ElevenLabs API key can do text-to-speech but fails speech-to-text with:

```text
missing_permissions: The API key you used is missing the permission speech_to_text
```

The OpenAI fallback key file is also missing or empty:

```text
../Hancock_CoPilot/openai_key.txt
```

So the current code can record audio, but it cannot complete transcription until one provider is unlocked:

- enable `speech_to_text` permission on ElevenLabs, or
- add a valid OpenAI key locally at `../Hancock_CoPilot/openai_key.txt`

## Files To Review

- `server.py`
- `dave_command.html`
- `Start Dave Electron.command`
- `dave-desktop/main.js`

Current build marker:

```text
dave_stt_fallback_v10
```

## Server: STT Provider Fallback

```python
def dave_transcribe_audio(audio_bytes, filename='dave-turn.webm', mime_type='audio/webm'):
    errors=[]
    if ELEVENLABS_API_KEY:
        try:
            text=elevenlabs_transcribe_audio(audio_bytes,filename,mime_type)
            DAVE_STT_HEALTH.update({'provider':'elevenlabs','model':ELEVENLABS_STT_MODEL,'fallback_provider':''})
            return text
        except Exception as exc:
            errors.append(str(exc))
            DAVE_STT_HEALTH.update({
                'provider':'elevenlabs',
                'model':ELEVENLABS_STT_MODEL,
                'status':'fallback_to_openai',
                'fallback_provider':'openai' if OPENAI_API_KEY else '',
                'error':str(exc)[:180],
            })
    if OPENAI_API_KEY:
        try:
            text=openai_transcribe_audio(audio_bytes,filename,mime_type)
            DAVE_STT_HEALTH.update({
                'provider':'openai',
                'model':OPENAI_TRANSCRIBE_MODEL,
                'fallback_from':'elevenlabs' if errors else '',
            })
            return text
        except Exception as exc:
            errors.append(str(exc))
    if errors:
        raise RuntimeError(' | '.join(errors))
    raise RuntimeError('Dave native voice needs ELEVENLABS_API_KEY with speech_to_text permission or OPENAI_API_KEY.')
```

## Server: Voice Command Endpoint

```python
def api_dave_voice_command(self,user):
    if self.rate_limited('dave-voice-command',60,10):
        self.send_json({'error':'Dave voice channel needs a short pause.'},429); return
    data=self.read_body()
    audio=(data.get('audio') or '').strip()
    mime=(data.get('mime') or 'audio/webm').strip()[:80]
    if not audio:
        self.send_json({'error':'audio required'},400); return
    if ',' in audio and audio.split(',',1)[0].startswith('data:'):
        header,audio_payload=audio.split(',',1)
        if ';base64' in header and ':' in header:
            mime=header.split(':',1)[1].split(';',1)[0] or mime
    else:
        audio_payload=audio
    try:
        audio_bytes=base64.b64decode(audio_payload,validate=True)
    except Exception:
        self.send_json({'error':'audio payload must be base64'},400); return
    if len(audio_bytes) < 900:
        self.send_json({'heard':'','reply':'Dave did not receive enough audio. Keep speaking or try again.','mode':'native_voice','briefing':dave_briefing(user)})
        return
    if len(audio_bytes) > 12_000_000:
        self.send_json({'error':'audio turn too large'},413); return
    filename='dave-turn.webm'
    if 'mpeg' in mime or 'mp3' in mime:
        filename='dave-turn.mp3'
    elif 'wav' in mime:
        filename='dave-turn.wav'
    elif 'mp4' in mime or 'm4a' in mime:
        filename='dave-turn.m4a'
    elif 'ogg' in mime:
        filename='dave-turn.ogg'
    try:
        heard=dave_transcribe_audio(audio_bytes,filename,mime)
        DAVE_STT_HEALTH.update({'status':'working','last_success_at':now(),'error':''})
    except Exception as exc:
        error=str(exc)
        DAVE_STT_HEALTH.update({'status':'unavailable','checked_at':now(),'error':error[:180]})
        self.send_json({'error':error,'stt':DAVE_STT_HEALTH},503); return
    if not heard:
        self.send_json({'heard':'','reply':'I did not catch a command. Keep talking or say standby.','mode':'native_voice','briefing':dave_briefing(user)})
        return
    reply,briefing,mode=dave_chat_reply(user,heard)
    save_conversation_turn(user['id'],'user','Dave voice: '+heard)
    save_conversation_turn(user['id'],'assistant','Dave: '+reply)
    log_action(user['id'],'spoke to Dave',heard[:140])
    self.send_json({
        'heard':heard,
        'reply':reply,
        'mode':'native_voice_'+mode,
        'briefing':briefing,
    })
```

## Browser/Electron Page: Native Recorder Loop

```javascript
function stopVoice(){conversationMode=false;manualStop=true;processingVoice=false;nativeMode=false;stopNativeTurn(true);$('openDaveBtn').classList.remove('primary');$('talkBtn').classList.remove('primary');stopListening();releaseMic();stopPlayback();focusTimers.forEach(clearTimeout);focusTimers=[];document.body.className='';$('statusLine').textContent='Dave is standing by.'}
function nativeRecordingSupported(){return !!(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia&&window.MediaRecorder)}
function nativeMimeType(){let choices=['audio/webm;codecs=opus','audio/webm','audio/mp4'];for(let i=0;i<choices.length;i++){if(!MediaRecorder.isTypeSupported||MediaRecorder.isTypeSupported(choices[i]))return choices[i]}return''}
function blobToDataUrl(blob){return new Promise(function(resolve,reject){let reader=new FileReader();reader.onload=function(){resolve(reader.result)};reader.onerror=function(){reject(reader.error||new Error('audio read failed'))};reader.readAsDataURL(blob)})}
function stopNativeTurn(discard){clearTimeout(nativeTurnTimer);nativeTurnTimer=null;if(nativeRecorder&&nativeRecorder.state!=='inactive'){try{nativeRecorder._discard=!!discard;nativeRecorder.stop()}catch(e){}}nativeRecorder=null}
function voiceProviderBlocked(message){let lower=(message||'').toLowerCase();return lower.indexOf('speech_to_text')>=0||lower.indexOf('openai_api_key')>=0||lower.indexOf('transcription failed')>=0||lower.indexOf('native voice needs')>=0}
async function submitNativeAudio(blob){if(!conversationMode||manualStop||!blob||blob.size<900){if(conversationMode&&!manualStop)queueListening(250);return}processingVoice=true;setCoreState('thinking');$('statusLine').textContent='Dave is transcribing...';try{let audio=await blobToDataUrl(blob);let data=await api('/api/dave-voice-command',{audio:audio,mime:blob.type||'audio/webm'});let heard=data.heard||'';let reply=data.reply||'Dave is online.';if(data.briefing){DAVE=data.briefing;render()}$('transcript').textContent=(heard?'Ryan: '+heard+'\n':'')+'Dave: '+reply;if(heard&&isStandbyCommand(heard)){stopVoice();return}setFocus(detectFocus((heard||'')+' '+reply));await speakDave(reply)}catch(e){let msg=e.message||'Dave native voice channel unavailable.';$('statusLine').textContent=msg;$('transcript').textContent='Dave: '+msg;if(voiceProviderBlocked(msg)){conversationMode=false;manualStop=true;nativeMode=false;$('openDaveBtn').classList.remove('primary');$('talkBtn').classList.remove('primary');stopNativeTurn(true);stopListening();releaseMic();setCoreState('');$('statusLine').textContent='Dave recorded audio, but speech-to-text is not unlocked. Add an OpenAI key file or enable ElevenLabs speech_to_text, then click Live Mic.';return}if(conversationMode&&!manualStop)queueListening(1400)}finally{processingVoice=false}}
async function startNativeTurn(){if(!conversationMode||manualStop||processingVoice||currentAudio)return;if(!nativeRecordingSupported()){nativeMode=false;startListening(true);return}nativeMode=true;stopListening(true);stopNativeTurn(true);try{await ensureMic()}catch(e){conversationMode=false;$('openDaveBtn').classList.remove('primary');$('talkBtn').classList.remove('primary');setCoreState('');$('statusLine').textContent='Dave cannot access the microphone. Allow mic access for Dave Desktop, then click Live Mic.';return}nativeChunks=[];let options={},mime=nativeMimeType();if(mime)options.mimeType=mime;try{nativeRecorder=new MediaRecorder(micStream,options)}catch(e){nativeMode=false;startListening(true);return}let rec=nativeRecorder;rec.ondataavailable=function(event){if(event.data&&event.data.size>0)nativeChunks.push(event.data)};rec.onerror=function(){if(conversationMode&&!manualStop){$('statusLine').textContent='Native recorder blinked. Restarting Dave mic...';queueListening(900)}};rec.onstop=function(){if(rec._discard)return;let blob=new Blob(nativeChunks,{type:rec.mimeType||mime||'audio/webm'});nativeChunks=[];submitNativeAudio(blob)};setCoreState('listening');$('talkBtn').classList.add('primary');$('openDaveBtn').classList.add('primary');$('statusLine').textContent='Dave native mic is on. Speak naturally, or say standby.';try{rec.start();nativeTurnTimer=setTimeout(function(){if(nativeRecorder===rec&&rec.state==='recording')rec.stop()},4200)}catch(e){nativeMode=false;startListening(true)}}
function queueListening(delay){clearTimeout(listenTimer);if(!conversationMode||manualStop)return;listenTimer=setTimeout(function(){if(!conversationMode||manualStop)return;if(nativeMode||nativeRecordingSupported())startNativeTurn();else startListening(true)},delay||500)}
async function startConversation(){conversationMode=true;manualStop=false;nativeMode=nativeRecordingSupported();$('openDaveBtn').classList.add('primary');$('talkBtn').classList.add('primary');if(audioCtx&&audioCtx.state==='suspended')audioCtx.resume().catch(function(){});$('statusLine').textContent=nativeMode?'Dave native mic is starting...':'Dave fallback mic is starting...';if(nativeMode)startNativeTurn();else startListening(true)}
```

## Launcher: Always-On Service Startup

```bash
#!/bin/bash
cd "$(dirname "$0")"

NODE_BIN="/Users/rknight/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin"
export PATH="$NODE_BIN:$PATH"

export PORT="${PORT:-8772}"
export HOST="${HOST:-127.0.0.1}"
export APP_DATA_DIR="${APP_DATA_DIR:-$PWD/app_data}"
export DAVE_LOCAL_AUTO_LOGIN=1
export DAVE_ELEVENLABS_VOICE_NAME="${DAVE_ELEVENLABS_VOICE_NAME:-Jarvis 1.1 Voice}"
export DAVE_ELEVENLABS_FALLBACK_VOICE_ID="${DAVE_ELEVENLABS_FALLBACK_VOICE_ID:-6Lopt6P83rUsEz3TeM5C}"
export DAVE_ELEVENLABS_FALLBACK_VOICE_NAME="${DAVE_ELEVENLABS_FALLBACK_VOICE_NAME:-Jarvis}"

if [ -z "$ELEVENLABS_API_KEY" ] && [ -s "../Hancock_CoPilot/elevenlabs_key.txt" ]; then
  export ELEVENLABS_API_KEY="$(cat ../Hancock_CoPilot/elevenlabs_key.txt)"
fi
if [ -z "$ANTHROPIC_API_KEY" ] && [ -s "../Hancock_CoPilot/anthropic_key.txt" ]; then
  export ANTHROPIC_API_KEY="$(cat ../Hancock_CoPilot/anthropic_key.txt)"
fi
if [ -z "$OPENAI_API_KEY" ] && [ -s "../Hancock_CoPilot/openai_key.txt" ]; then
  export OPENAI_API_KEY="$(cat ../Hancock_CoPilot/openai_key.txt)"
fi

health_current() {
  curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/healthz" 2>/dev/null | grep -q 'dave_stt_fallback_v10'
}

health_any() {
  curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1
}

mkdir -p "$APP_DATA_DIR"

if ! health_current; then
  if health_any; then
    stale_pids="$(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$stale_pids" ]; then
      echo "Stopping older Dave service..."
      kill $stale_pids 2>/dev/null || true
      sleep 1
    fi
  fi
  echo "Starting Dave background service..."
  nohup python3 -u server.py >> "$APP_DATA_DIR/dave_server.log" 2>&1 &
  echo "$!" > "$APP_DATA_DIR/dave_server.pid"
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if health_current; then
      break
    fi
    sleep 1
  done
fi

./node_modules/.bin/electron .
```

## Electron Lifecycle Notes

`dave-desktop/main.js` has:

```javascript
const expectedInteractionVersion = 'dave_stt_fallback_v10';
```

Recent change:

```javascript
app.on('before-quit', () => {
  globalShortcut.unregisterAll();
  if (serverProcess && process.env.DAVE_STOP_SERVER_ON_QUIT === '1') {
    serverProcess.kill();
  }
});
```

Question for review: now that the launcher starts the Python service first, should Electron still spawn the server in `ensureServer()/spawnServer()`, or should Electron only attach to an existing background service and surface an error if unavailable?

## Requested Output

Please provide:

1. Any remaining bug in the mic lifecycle after STT credentials are fixed.
2. Whether the 4.2 second `MediaRecorder` turn loop should be changed.
3. Whether `processingVoice`, `manualStop`, `nativeMode`, and `currentAudio` can deadlock or restart too often.
4. Whether Electron should stop spawning the server now that the launcher does.
5. A minimal patch recommendation if you find an issue.
