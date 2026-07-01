# Dave Mic Handoff For Claude

## Goal
Dave needs reliable voice interaction inside the Electron desktop app:
- user speaks to Dave
- Dave transcribes the audio
- Dave routes the text through `/api/dave-chat`
- Dave replies using the existing ElevenLabs Dave voice
- saying `standby` stops the loop

## Current Architecture
- Desktop shell: `dave-desktop/main.js`
- UI and mic loop: `dave_command.html`
- Local API server: `server.py`
- Launcher: `Start Dave Electron.command`

## Current Build
- Interaction version: `dave_stt_fallback_v9`
- Dave TTS voice works through ElevenLabs.
- Native mic mode records short turns with `MediaRecorder`.
- The browser sends base64 audio to `POST /api/dave-voice-command`.
- Server attempts ElevenLabs STT first, then OpenAI STT if `OPENAI_API_KEY` is configured.

## Verified Blocker
The ElevenLabs key can perform text-to-speech, but it currently fails speech-to-text:

```text
missing_permissions: The API key you used is missing the permission speech_to_text
```

The expected fallback file is also missing or empty:

```text
../Hancock_CoPilot/openai_key.txt
```

Until one of those is fixed, Dave can record microphone audio but cannot reliably turn speech into text.

## Recent Fixes
- `server.py` now ignores `SIGHUP` so the local brain survives terminal/window hangups.
- `Start Dave Electron.command` starts the local service with `nohup` before opening Electron.
- The launcher stops stale Dave services when the interaction version changes.
- `server.py` now falls back from ElevenLabs STT to OpenAI STT when available.
- `dave_command.html` now stops the mic loop on STT provider failure instead of bouncing on/off.

## Review Request
Please review:
- `dave_command.html`: native recorder lifecycle, `submitNativeAudio`, `startNativeTurn`, and standby handling.
- `server.py`: `dave_transcribe_audio`, `api_dave_voice_command`, and health status reporting.
- `Start Dave Electron.command`: background service startup and stale service replacement.
- `dave-desktop/main.js`: whether Electron should spawn the server at all now that the launcher starts it first.

Main question: after STT credentials are available, is there any remaining lifecycle issue that would cause Dave's mic to stop or restart unnecessarily?
