# EmoraTest — rrweb Session Replay Integration

## HOW TO USE
- Feed these prompts ONE AT A TIME
- Do NOT skip to the next prompt until tests pass
- The agent must run tests and show passing results before pushing

---

## PROMPT 0: Remove Old Replay System Completely

```
We are replacing the old session replay system with rrweb (professional 
DOM recording). Before building the new one, REMOVE all old replay code 
completely so it doesn't conflict.

TASK: Remove ALL old replay code. Specifically:

1. SDK (sdk/src/ and frontend/public/emoratest.js):
   - Remove MousePathTracker class
   - Remove collectMousePath function
   - Remove collectPageChanges function  
   - Remove html2canvas screenshot capture code
   - Remove screenshot upload code
   - Remove all mouse_path related code from EventQueue (setMousePathTracker, 
     getPath, getPageMetadata in flush/flushBeacon)
   - Do NOT remove existing event tracking (mouse_move, clicks, scroll, 
     exit_intent, visibility) — those stay for emotion detection

2. BACKEND (app/api/sdk.py, app/api/dashboard.py):
   - Remove the POST /sessions/{id}/screenshot endpoint
   - Remove mouse_path extraction from /events/batch endpoint
   - Remove session_replay_data INSERT code from /events/batch
   - Remove the GET /sessions/{id}/replay endpoint
   - Remove the GET /sessions/{id}/replay/screenshot endpoint
   - Remove has_replay logic from the sessions list endpoint
   - Remove SessionReplayData model import and usage
   - Do NOT delete the database table or migration files — we'll reuse 
     the table with different columns

3. FRONTEND DASHBOARD:
   - Remove the ReplayViewer component entirely
   - Remove the ▶ Replay button from sessions list
   - Remove replay-related imports from session pages
   - Remove thum.io screenshot code
   - Remove wireframe grid code

4. After removing everything:
   - The app must build and run without errors
   - The sessions list must work (just without replay buttons)
   - Event tracking must still work normally
   - Emotion detection must still work

DO NOT create any new code in this prompt. Only delete old code.

✅ TEST:
- Backend starts without errors
- Frontend builds without errors  
- Sessions page loads and shows sessions (no replay button — that's expected)
- Browse a page with SDK — events still tracked, emotions still detected
- grep -rn "MousePathTracker\|mouse_path\|thum.io\|html2canvas\|wireframe\|ReplayViewer" 
  in frontend/src/ and backend/app/ → ZERO matches (excluding migrations)
- Show me the full list of files modified/deleted
```

---

## PROMPT 1: Database Migration — Replace session_replay_data Schema

```
CONTEXT: We removed the old replay system. Now we're building a new one 
using rrweb (DOM recording library). The session_replay_data table exists 
but has the wrong columns. We need to update it.

TASK: Create alembic migration 027 to update session_replay_data.

The table currently has: id, session_id, mouse_path, page_url, page_title, 
page_width, page_height, device_pixel_ratio, page_screenshot, created_at

We need it to have:
- id: UUID PRIMARY KEY (keep as is)
- session_id: UUID REFERENCES sessions(id) ON DELETE CASCADE (keep as is)
- rrweb_events: JSONB NOT NULL — stores the rrweb event array
- events_count: INTEGER DEFAULT 0 — number of rrweb events
- compressed_size_bytes: INTEGER DEFAULT 0 — size of the compressed data
- recording_duration_ms: INTEGER DEFAULT 0 — duration in milliseconds
- page_url: TEXT (keep as is)
- created_at: TIMESTAMPTZ DEFAULT NOW() (keep as is)

Migration steps:
1. DROP columns: mouse_path, page_title, page_width, page_height, 
   device_pixel_ratio, page_screenshot
2. ADD columns: rrweb_events (JSONB NOT NULL DEFAULT '[]'), events_count 
   (INTEGER DEFAULT 0), compressed_size_bytes (INTEGER DEFAULT 0), 
   recording_duration_ms (INTEGER DEFAULT 0)
3. DELETE all existing rows (old data is incompatible)

Also update the SQLAlchemy model (SessionReplayData) to match.

IMPORTANT:
- down_revision must be the current head (check with: alembic heads)
- Keep the session_id index and foreign key
- The UNIQUE constraint on session_id should stay

✅ TEST:
- alembic upgrade head → succeeds
- \d session_replay_data → shows new columns, no old columns
- SELECT count(*) FROM session_replay_data → 0 (old data deleted)
- Backend starts without errors
- Show me the migration file and updated model
```

---

## PROMPT 2: SDK — Add rrweb Recording (60-second limit)

```
CONTEXT: We're integrating rrweb for professional DOM-based session replay.
The SDK source is at: sdk/src/
The SDK builds with: cd sdk && npm run build
The built output goes to: frontend/public/emoratest.js

IMPORTANT BUILD NOTE: The server has Node v18. If the build fails with 
rollup errors, you MUST fix the build issues before proceeding. The 
previous developer left broken imports. Make sure every import in 
sdk/src/index.ts actually exists and is exported from its source file.

TASK: Add rrweb recording to the SDK with a 60-second time limit.

1. INSTALL rrweb in the SDK:
   cd sdk && npm install rrweb@2.0.0-alpha.13

2. In sdk/src/, create a new file: rrweb-recorder.ts
   
   This file should:
   - Import { record } from 'rrweb'
   - Export a class RRWebRecorder with methods:
     * start() — begins recording DOM events
     * stop() — stops recording
     * getEvents() — returns the recorded events array
     * getDuration() — returns recording duration in ms
     * isRecording() — returns boolean
   - Max recording duration: 60 seconds (auto-stops after 60s)
   - Max events: 10000 (auto-stops if too many events)
   - After stopping, the events are available via getEvents()

3. In sdk/src/index.ts:
   - Import RRWebRecorder
   - After session starts, create a new RRWebRecorder and call start()
   - When session ends (beforeunload, visibility hidden, or 60s timer), 
     call stop() and send the events to the backend
   - Send rrweb events as a SEPARATE request:
     POST /api/v1/sessions/{session_id}/rrweb
     Body: { events: [...], duration_ms: 60000, events_count: 5000 }
   - If recording fails or rrweb doesn't load, skip silently — 
     don't break event tracking

4. In sdk/src/event-queue.ts (or wherever transport is):
   - Add a new method: sendRRWebEvents(sessionId, events, durationMs)
   - This sends the POST request to /api/v1/sessions/{session_id}/rrweb

5. BUILD the SDK:
   cd sdk && npm run build
   cp sdk/dist/emoratest.umd.js frontend/public/emoratest.js

IMPORTANT:
- rrweb recording must NOT interfere with existing event tracking
- The 60-second limit is HARD — stop recording after exactly 60 seconds
- If the events payload is > 5MB, don't send it (too large)
- rrweb events are sent ONCE when recording stops, not with every flush
- On beforeunload, use navigator.sendBeacon for the rrweb data
- Make sure the SDK build succeeds with ZERO errors

✅ TEST:
- cd sdk && npm run build → completes with NO errors
- grep "rrweb\|record" frontend/public/emoratest.js → matches found
- Open a test page with the SDK, check Network tab:
  * After 60 seconds OR when leaving the page, a POST to /rrweb fires
  * The payload contains events array with rrweb event objects
  * Events include type 2 (FullSnapshot) and type 3 (IncrementalSnapshot)
- Existing event tracking still works (mouse_move, clicks, etc.)
- Show me the build output and a network request screenshot
```

---

## PROMPT 3: Backend — Store rrweb Events

```
CONTEXT: The SDK now sends rrweb events via:
POST /api/v1/sessions/{session_id}/rrweb
Body: { events: [...], duration_ms: 60000, events_count: 5000 }

TASK: Create the backend endpoint to receive and store rrweb events.

1. In app/api/sdk.py, add a new endpoint:
   POST /sessions/{session_id}/rrweb

   - Accept JSON body with: events (list), duration_ms (int), events_count (int)
   - Validate session_id exists in sessions table
   - Validate SDK key (same auth as other SDK endpoints)
   - Calculate compressed_size_bytes = len(json.dumps(events))
   - Reject if compressed_size_bytes > 5MB (5242880 bytes)
   - Insert into session_replay_data:
     session_id, rrweb_events, events_count, compressed_size_bytes, 
     recording_duration_ms, page_url (from the session)
   - If a record already exists for this session_id, UPDATE it (replace)
   - Return 200 OK

2. Also support sendBeacon (URL query param auth):
   The SDK may send via navigator.sendBeacon on page unload, which 
   sends to: /api/v1/sessions/{session_id}/rrweb?sdk_key=KEY
   Handle this case — accept sdk_key from query param if not in header.

3. Add a Pydantic model for the request body:
   class RRWebEventsRequest(BaseModel):
       events: List[dict]
       duration_ms: int = 0
       events_count: int = 0

4. Error handling:
   - 404 if session not found
   - 413 if payload too large (>5MB)
   - 401 if invalid SDK key
   - Log errors, don't swallow them

✅ TEST:
- Send a test POST with sample rrweb events:
  curl -X POST https://emoratest.com/api/v1/sessions/SESSION_ID/rrweb \
  -H "Content-Type: application/json" \
  -H "X-SDK-Key: YOUR_KEY" \
  -d '{"events": [{"type": 2, "data": {"test": true}, "timestamp": 1715100000}], "duration_ms": 5000, "events_count": 1}'
- Check DB: SELECT session_id, events_count, recording_duration_ms 
  FROM session_replay_data; → must have a row
- Send without auth → 401
- Send with invalid session → 404
- Send >5MB payload → 413
- Show me all test results
```

---

## PROMPT 4: Backend — Serve rrweb Events for Replay

```
CONTEXT: rrweb events are stored in session_replay_data.rrweb_events. 
The dashboard needs an endpoint to fetch them for replay.

TASK: Create endpoints for the dashboard to get replay data.

1. GET /api/v1/dashboard/sessions/{session_id}/replay
   - Requires dashboard auth (merchant auth, not SDK key)
   - Returns:
     {
       "has_replay": true,
       "events": [...rrweb events array...],
       "duration_ms": 60000,
       "events_count": 5000,
       "emotions": [...emotion events for this session...],
       "page_url": "https://example.com/"
     }
   - Include emotion data from emotion_events table for this session
     (timestamp + emotion label) — we'll overlay this on the replay
   - If no replay data exists, return: {"has_replay": false}

2. Update the sessions list endpoint to include has_replay:
   - For each session, check if session_replay_data has a row
   - Add has_replay: bool to the response
   - Use an efficient EXISTS subquery, not N+1

✅ TEST:
- Create a session with rrweb data (from Prompt 3 test)
- GET /api/v1/dashboard/sessions/{id}/replay → must return events array
- GET for session WITHOUT replay → {"has_replay": false}
- Sessions list must include has_replay field
- Auth required — no token returns 401
- Show me API response samples
```

---

## PROMPT 5: Frontend — rrweb Player with Emotion Overlay

```
CONTEXT: The backend serves rrweb events at:
GET /api/v1/dashboard/sessions/{session_id}/replay

We need to build a replay viewer using rrweb-player that shows the 
actual recorded page with our behavioral state overlay.

TASK: Build the new replay viewer.

1. INSTALL rrweb-player in the frontend:
   npm install rrweb-player@2.0.0-alpha.13

2. Create component: frontend/src/components/dashboard/SessionReplay.tsx

   The component should:
   a. Fetch replay data from GET /api/v1/dashboard/sessions/{id}/replay
   b. If has_replay is false, show "No replay available" message
   c. If has_replay is true:
      - Render rrweb-player with the events array
      - Player dimensions: width 100% of container, height auto (16:9 ratio)
      - Import rrweb-player CSS: import 'rrweb-player/dist/style.css'
   
   d. EMOTION OVERLAY — on top of the rrweb player, show:
      - A colored bar along the bottom showing behavioral states over time:
        * frustrated: #EF4444 (red)
        * confused: #F59E0B (amber)
        * hesitating: #EAB308 (yellow)
        * engaged: #22C55E (green)
        * disengaged: #6B7280 (gray)
      - Current behavioral state badge that updates as replay plays
      - Use rrweb-player's event listener to sync with playback time

   e. KEY MOMENTS panel below the player:
      - Detect from emotion data: frustration spikes, state changes
      - Show as clickable cards with timestamp and description
      - Clicking a key moment seeks the player to that timestamp

   f. CONTROLS:
      - Play/Pause (rrweb-player has built-in controls)
      - Speed: 1x, 2x, 4x
      - "Skip to frustration" button — jumps to first frustrated moment
      - Session info sidebar: duration, page URL, dominant state

3. Add ▶ Replay button back to sessions list:
   - Show only when has_replay is true
   - Opens the SessionReplay component (modal or full page)

IMPORTANT:
- The rrweb-player handles all the DOM reconstruction — don't try to 
  rebuild the page yourself
- The emotion overlay is ADDITIONAL — it goes on top of what rrweb shows
- Match the existing dashboard design (colors, fonts, spacing)
- Loading state while fetching replay data
- Handle errors gracefully

BEHAVIORAL STATES — only these 5 exist:
frustrated (#EF4444), confused (#F59E0B), hesitating (#EAB308), 
engaged (#22C55E), disengaged (#6B7280)

✅ TEST:
- Open a session with replay data
- The ACTUAL PAGE must appear (not a wireframe, not a screenshot — 
  the real reconstructed page with real elements)
- You can see the mouse moving, clicks happening, scrolling
- Emotion color bar shows at the bottom of the player
- Current state badge updates during playback
- Key moments are clickable and seek the player
- Speed controls work (1x, 2x, 4x)
- Sessions without replay show "No replay available"
- Take a screenshot of the working replay with emotion overlay
```

---

## PROMPT 6: Polish and Edge Cases

```
CONTEXT: rrweb replay with emotion overlay is working. Final polish pass.

TASK:

1. PERFORMANCE:
   - If rrweb events are > 5000, show a warning but still play
   - Lazy load replay data — don't fetch until user clicks ▶
   - Show loading spinner while fetching

2. EDGE CASES:
   - Session shorter than 2 seconds → "Session too short for replay"
   - rrweb events corrupted or invalid → show error with retry button
   - Mobile sessions → player should scale responsively
   - If emotion data is empty → hide emotion overlay, just show replay

3. RECORDING INDICATOR (SDK):
   - Do NOT show any recording indicator to the end user
   - rrweb recording must be completely invisible

4. PRIVACY:
   - rrweb has built-in masking. Enable it:
     * Mask all input values (passwords, emails, etc.)
     * Use rrweb's maskAllInputs: true option in the SDK recorder
     * Also mask elements with class "emoratest-mask" or data-emoratest-mask

5. STORAGE MANAGEMENT:
   - Add a note in the dashboard settings about replay storage
   - Old replay data should auto-delete after 30 days
   - Add this as a comment/TODO in the code for now

6. CLEANUP:
   - Remove any console.log statements
   - Remove test data
   - Verify no old replay code remains (grep for wireframe, thum.io, 
     MousePathTracker, mouse_path in active code)

✅ TEST:
- Replay works smoothly for a 60-second recording
- Input fields show masked values (asterisks or [masked])
- No recording indicator visible on the recorded site
- No console.log in production
- grep for old code (wireframe, thum.io, MousePathTracker) → zero matches
- Show me final screenshot of the complete replay experience
```

---

## BUILD & DEPLOY CHECKLIST

After each prompt, the agent MUST:

```
1. cd sdk && npm run build                              # Build SDK
2. cp sdk/dist/emoratest.umd.js frontend/public/emoratest.js  # Copy to frontend
3. git add -A                                           # Stage all changes
4. git commit -m "descriptive message"                  # Commit
5. git push                                             # Push

Then on the server:
6. cd /opt/emoratest && git pull                        # Pull changes
7. docker compose -f docker-compose.prod.yml up -d --build  # Rebuild
8. docker compose -f docker-compose.prod.yml exec backend alembic upgrade head  # Migrations
```

If the SDK build fails (step 1), DO NOT PROCEED. Fix the build first.
If step 1 is not needed (backend-only change), skip steps 1-2.