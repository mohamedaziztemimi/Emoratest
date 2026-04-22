# SDK Scalability Validation — Collection vs Storage

## Summary

The SDK now separates **EVENT COLLECTION** from **EVENT STORAGE** to ensure behavioral analytics quality even after hitting the event limit (1000 events).

## Key Principle

| Component | What it does | Affected by limit? |
|-----------|--------------|-------------------|
| **Collectors** | Listen to DOM events, compute signals | ❌ Never affected |
| **Internal Buffers** | Track rage clicks, velocity | ❌ Never affected |
| **EventQueue** | Store events for backend | ✅ Filters by priority |

## Event Priority

### HIGH PRIORITY (always stored, even after 1000 events)
- `click` — Rage click detection MUST work
- `exit_intent` — Critical for abandonment
- `visibility` — Tab switching = exit
- `mouse_summary` — Aggregated velocity data (NEW)

### LOW PRIORITY (dropped after 1000 events)
- `mouse_move` — Raw mouse movement (voluminous)
- `scroll` — Raw scroll events (voluminous)

## Proof: Behavioral Analytics Still Work After Limit

### 1. Rage Click Detection ✅

```ts
// In collectors.ts
const recentClicks: { x: number; y: number; time: number }[] = [];
// ↑ This buffer is LOCAL to the collector, NOT in EventQueue
// ↑ It is NEVER affected by event limit

const handler = (e: MouseEvent) => {
  // ALWAYS track for rage-click detection
  recentClicks.push({ x: e.clientX, y: e.clientY, time: now });

  // Detect rage click
  const isRageClick = nearby.length >= 3;

  // Create event with metadata
  const event = { type: "click", metadata: { rage_click: isRageClick } };

  // Click is HIGH PRIORITY - ALWAYS stored
  queue.push(event);
};
```

**After 1000 events:**
- Listener still active ✅
- Buffer still tracking ✅
- Rage clicks still detected ✅
- Events still stored (high priority) ✅

### 2. Velocity Calculation ✅

```ts
// In collectors.ts
let lastX = 0, lastY = 0, lastTime = 0;
const velocitySamples: number[] = [];
// ↑ These are LOCAL to the collector, NEVER affected by limit

const handler = throttle((e: MouseEvent) => {
  const velocity = computeVelocity(lastX, lastY, lastTime);

  // ALWAYS update internal state
  velocitySamples.push(velocity);

  // Try to store raw mousemove (may be dropped after limit)
  queue.push({ type: "mouse_move", velocity });

  // Emit summary every 5 seconds (HIGH PRIORITY - always stored)
  if (shouldEmitSummary()) {
    queue.push({
      type: "mouse_summary",
      metadata: { avg_velocity: avg(velocitySamples), ... }
    });
  }
}, throttleMs);
```

**After 1000 events:**
- Listener still active ✅
- Velocity still computed ✅
- Raw mousemove dropped (low priority) ✅
- `mouse_summary` still stored (high priority) ✅

### 3. Example: Dropped vs Kept Events

```
Event #999: mouse_move (x=100, y=200, velocity=450)  → STORED ✅
Event #1000: mouse_move (x=105, y=205, velocity=460) → STORED ✅
Event #1001: mouse_move (x=110, y=210, velocity=470) → DROPPED (limit reached)
Event #1002: scroll (direction=down, delta=50)        → DROPPED (low priority)
Event #1003: click (x=300, y=400, rage_click=true)   → STORED ✅ (high priority)
Event #1004: mouse_summary (avg_velocity=520)        → STORED ✅ (high priority)
Event #1005: exit_intent (trigger=mouse_leave)       → STORED ✅ (high priority)
```

## Internal Buffers (Not Affected by Limit)

### Rage Click Buffer
- **Location**: `collectClicks()` closure
- **Size**: Last 2 seconds of clicks
- **Purpose**: Detect 3+ clicks within 50px radius
- **Affected by limit**: NO

### Mouse Tracking Buffer
- **Location**: `collectMouseMove()` closure
- **Size**: Up to 100 velocity samples
- **Purpose**: Compute avg/max velocity for summary
- **Affected by limit**: NO

### Scroll State
- **Location**: `collectScroll()` closure
- **Variables**: `lastScrollY`, `lastDirection`
- **Purpose**: Detect retreat patterns
- **Affected by limit**: NO

## Files Modified

1. **sdk/src/types.ts**
   - Added `mouse_summary` event type
   - Added `mouse_summary` to HIGH_PRIORITY_EVENTS
   - Added documentation explaining priority system

2. **sdk/src/collectors.ts**
   - Added `mouse_summary` emission every 5 seconds
   - Added velocity samples buffer for aggregation
   - Added comprehensive documentation about collection vs storage

3. **sdk/src/event-queue.ts**
   - Added documentation explaining separation
   - Updated fallback priority sets to include `mouse_summary`

## Validation Checklist

- [x] Rage click detection works after 1000 events
- [x] Velocity still computed correctly after limit
- [x] Event storage is limited (low priority dropped)
- [x] High priority events still stored after limit
- [x] Internal buffers not affected by limit
- [x] Mouse summary provides aggregated velocity data
