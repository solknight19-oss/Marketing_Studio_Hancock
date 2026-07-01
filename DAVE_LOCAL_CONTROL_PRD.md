# Dave Local Control PRD

## Objective
Dave should become Ryan's always-on desktop command assistant: a local brain that can hear Ryan, brief Ryan, monitor approved business systems, and take approved actions across the Mac, Studio, email, calendar, files, browser, and specialist bots.

Dave should not be built as an unrestricted computer takeover tool. Dave should be built as a permissioned operator with action logs, reversible steps where possible, and approval gates for sensitive actions.

## Core Principle
Dave can recommend, prepare, and execute. Sensitive execution requires Ryan approval unless the action is explicitly pre-approved.

Examples:
- Safe automatic actions: summarize inbox, classify emails, draft replies, create task suggestions, open pages/apps, run Studio scans, create daily briefings.
- Approval-required actions: send email, delete/archive important files, schedule external meetings, update billing/account settings, post public content, modify production deployments.
- Blocked actions: bypass account security, hide activity, exfiltrate secrets, impersonate people, disable security protections.

## System Layers

### 1. Dave Desktop Shell
Electron app that gives Dave a persistent visual surface, tray menu, live mic, voice playback, and command cockpit.

Current files:
- `dave-desktop/main.js`
- `dave-desktop/preload.js`
- `dave_command.html`
- `Start Dave Electron.command`

### 2. Dave Background Brain
Local Python service that stays running even when the Electron window closes.

Responsibilities:
- serve Dave UI
- handle voice command endpoint
- manage Dave Core scans
- maintain local memory/status database
- coordinate action requests

Current file:
- `server.py`

### 3. Voice Layer
Dave needs two separate voice capabilities:
- TTS: Dave speaks using the licensed ElevenLabs Dave voice.
- STT: Dave hears Ryan through ElevenLabs speech-to-text or OpenAI transcription.

Current blocker:
- ElevenLabs key can do TTS but lacks `speech_to_text` permission.
- OpenAI fallback key file is missing or empty at `../Hancock_CoPilot/openai_key.txt`.

### 4. Control Bus
A local API that turns Dave's intentions into controlled computer actions.

Action request schema:
- `action_id`
- `source`
- `action_type`
- `target`
- `risk`
- `approval_required`
- `status`
- `dry_run_summary`
- `execution_result`
- `created_at`
- `updated_at`

### 5. Tool Adapters
Adapters should be narrow and auditable.

Planned adapters:
- Mac apps: open/focus apps, open files, create reminders, run Shortcuts.
- Browser: open tabs, navigate local Studio, gather page context.
- Studio: run Dave Core, update tasks, read bot reports.
- Gmail/Outlook: triage, summarize, draft replies, detect follow-ups.
- Teams/Calendar: read schedule, propose meetings, create approved events.
- Files: search, summarize, organize, create project packets.
- Specialist bots: receive reports from Chad and future bots.

### 6. Approval System
Dave should have three execution modes:

1. Observe
   Dave reads, summarizes, and reports. No changes.

2. Prepare
   Dave drafts actions and shows Ryan what would happen.

3. Execute
   Dave performs approved or pre-authorized actions.

Default mode should be Prepare for anything external-facing.

## Immediate Build Sequence

### Phase 1: Voice Reliability
Goal: Ryan can speak to Dave and Dave responds without the mic bouncing.

Tasks:
- unlock STT provider
- verify `/api/dave-voice-command`
- confirm native `MediaRecorder` loop works in Electron
- test `standby`
- test Dave response playback

### Phase 2: Always-On Local Brain
Goal: Dave starts at login and keeps the service alive.

Tasks:
- move background service to a proper macOS LaunchAgent
- keep Electron as the face, not the process owner
- add health monitor and auto-restart
- add visible status when voice, AI, or connectors are degraded

### Phase 3: Local Control Bus
Goal: Dave can safely execute approved local actions.

Tasks:
- add `dave_actions` table
- add `/api/dave-action-request`
- add `/api/dave-action-approve`
- add `/api/dave-action-run`
- add allowlisted action runners
- add audit log in the Dave UI

### Phase 4: Email And Calendar Connectors
Goal: Dave can triage communication and prepare responses.

Tasks:
- Gmail OAuth connector
- Microsoft Graph connector for Outlook/Teams calendar
- unified inbox summary
- draft reply generation
- follow-up detection
- meeting proposal flow
- approval before sending/scheduling

### Phase 5: Personal Operating Memory
Goal: Dave remembers Ryan's preferences, company context, project status, tone, and active priorities.

Tasks:
- local memory store
- source-aware notes
- daily briefing snapshots
- decision log
- recurring priorities
- weekly review

## Success Criteria
Dave is working when:
- Ryan can say a command and Dave responds by voice.
- Dave can produce a live agenda when the Mac starts.
- Dave can tell what changed while Ryan was away.
- Dave can draft emails and meetings without sending until approved.
- Dave can execute pre-approved local actions.
- Dave keeps an audit trail of what it did, what it prepared, and what needs Ryan.

## Non-Negotiables
- Do not paste API keys into chat.
- Do not give Dave unrestricted destructive control.
- Do not auto-send external communications without explicit approval until Ryan defines a trusted rule.
- Keep Dave local-first for sensitive context.
- Every meaningful action should leave a trail.
