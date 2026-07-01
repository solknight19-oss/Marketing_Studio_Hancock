# Product Requirements Document - Dave

## Summary

Dave is Ryan Knight's desktop command brain. Dave sits above Chad and the specialist bots, opens as a voice-first briefing surface, and tells Ryan what changed, what matters, and what to do next.

The first implementation lives inside the Hancock Live Marketing Studio service at `/dave`. It uses the separate Dave ElevenLabs voice configuration with the user-created voice named `Jarvis`.

## Product Role

- Dave is the top-level personal command layer for Ryan.
- Chad remains the marketing/workspace teammate and reports upward to Dave.
- Specialist bots report status, recommendations, blockers, and next steps through Dave reports.
- Dave aggregates email, calendar, task, bot, file, and workspace signals as connectors come online.

## Current MVP

- Authenticated Dave command page at `/dave`.
- Dave briefing API at `/api/dave-briefing`.
- Dave report intake at `/api/dave-report`.
- Dave speech endpoint at `/api/dave-speak`.
- Separate Dave voice settings:
  - `DAVE_ELEVENLABS_VOICE_ID`
  - `DAVE_ELEVENLABS_VOICE_NAME`
  - `DAVE_ELEVENLABS_TTS_MODEL`
- Local desktop launcher: `Start Dave.command`.

## Daily Briefing

Dave should produce a concise tactical briefing:

- Status: what happened since the last check-in.
- Importance: what needs Ryan's attention.
- Next action: the highest-leverage next move.

The briefing includes:

- emails replied to
- emails waiting on Ryan
- appointments booked or waiting
- open and urgent tasks
- calendar items due today
- Chad and specialist bot signals
- Dave reports
- recent workspace activity

## Voice And Interface

- Product name: Dave.
- Preferred voice profile label: Jarvis 1.1 Voice.
- Fallback voice profile label: Jarvis, used only until ElevenLabs exposes Jarvis 1.1 Voice on the account.
- Voice style: tactical, concise, mission-control, legally original.
- Interface style: cinematic command surface, dark, structured, scannable.
- Fallback: if ElevenLabs is unavailable, Dave uses system/browser voice.

## Authority Model

Dave may summarize, prioritize, draft, and route work automatically.

Dave must review-gate:

- legal matters
- financial/payment matters
- HR/personnel matters
- contracts
- confidential or sensitive messages
- angry or unusual messages
- low-confidence classifications
- unfamiliar recipients
- destructive file/account actions

Dave never deletes, spends money, signs contracts, changes permissions, or sends risky external communication without explicit approval.

## Connector Roadmap

1. Outlook/Microsoft 365 mail sync.
2. Teams calendar availability and meeting creation.
3. Gmail sync and send support.
4. Approved file indexing inside Knight/Hancock folders.
5. Future CRM and business-system connectors.

## Acceptance Criteria

- Dave opens from `/dave` after sign-in.
- Dave can speak its briefing through the Jarvis 1.1 Voice ElevenLabs profile when available.
- Dave briefing API returns counts, next actions, bot status, reports, tasks, calendar, and connector status.
- Chad and future bots can create Dave reports.
- Dave remains separate from Chad's voice and does not overwrite Chad settings.
- The desktop launcher opens Dave locally.
