# Dave Electron Desktop

Dave Desktop is the native container for the always-present computer brain.

The current build wraps the existing Dave cockpit and local Python brain service. Electron gives Dave a real desktop home for microphone permission, app focus, startup behavior, notifications, tray/menu controls, and future native automation.

## Start

Run once:

```bash
./Install\ Dave\ Electron.command
```

Then start Dave Desktop:

```bash
./Start\ Dave\ Electron.command
```

## What This Version Does

- Starts or reuses the local Dave service on `127.0.0.1:8772`.
- Verifies Dave is serving `dave_core_stable_talk_v4`.
- Opens Dave in a dedicated Electron window.
- Grants microphone/media permission only to the local Dave URL.
- Keeps a Dave app menu with Show Dave, Start Live Mic, Standby, Reload, and Quit.
- Adds a desktop bridge at `window.DaveDesktop` for future native controls.
- Loads ElevenLabs and Anthropic keys from the existing Hancock_CoPilot key files when available.
- Supports the v7 native recorder loop: Dave records short audio turns with Electron/MediaRecorder, sends them to the local Dave server, transcribes them, then routes the heard command into Dave chat.
- Uses ElevenLabs speech-to-text first through the existing `ELEVENLABS_API_KEY`; falls back to `OPENAI_API_KEY` or `../Hancock_CoPilot/openai_key.txt` when ElevenLabs is not configured.

## Next Build Targets

- Voice activity detection so Dave can end turns based on silence instead of fixed turn windows.
- Login item installer for Dave Desktop.
- Background agenda checks and notification popups.
- Local file watcher for Studio and workspace updates.
- Real Outlook, Gmail, and Teams Calendar connector jobs.
- Approval queue for risky actions like sending emails or changing meetings.
