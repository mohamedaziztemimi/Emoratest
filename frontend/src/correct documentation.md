# Prompt — Fix Documentation Page (22 issues)

Paste the RULES block at the top, then this prompt:

```
READ the docs page completely. Find it:
find frontend/src -name "*.tsx" -path "*doc*"

Also READ the SDK source to verify which methods actually exist:
- Read sdk/src/ — every file
- List every public method on the EmoraTest object
- For each method listed in the docs, confirm it exists in the SDK code

Now fix ALL of the following issues:

═══ BUGS (will cause customer errors) ═══

1. A/B TESTING SECTION — Step 3 says:
   "Make sure you have EmoraTest.track('purchase')"
   This method DOES NOT EXIST. Change to:
   "Make sure you call EmoraTest.reportOutcome('purchase')"

2. REACT INSTALLATION SNIPPET has this cleanup:
   return () => { document.body.removeChild(script); };
   REMOVE this cleanup return entirely. It removes the SDK script
   when the component unmounts, killing all tracking on route changes.
   The useEffect should NOT return a cleanup function.

3. SDK REFERENCE TABLE — check EVERY method listed:
   - EmoraTest.init() → exists in SDK? If yes keep, if no remove
   - EmoraTest.reportOutcome() → exists?
   - EmoraTest.detectOutcomeFromUrl() → exists?
   - EmoraTest.evaluateFlag() → exists?
   - EmoraTest.getVariant() → exists?
   - EmoraTest.getSessionId() → exists?
   - EmoraTest.getVisitorId() → exists?
   - EmoraTest.isInitialized() → exists?
   - EmoraTest.destroy() → exists?
   If a method is in the docs but NOT in the SDK → REMOVE it from docs.
   If a method is in the SDK but NOT in the docs → ADD it to docs.
   Report which methods were added/removed.

═══ WRONG / OUTDATED CONTENT ═══

4. NPM SECTION — shows "npm install emoratest" but this package
   doesn't exist on npm. Remove the install command. Change to:
   "NPM Package — Coming soon. Use the script tag method for now."
   No code block. Just that one line.

5. ACCURACY CLAIM — "86%+ accuracy" → change to "80%+ accuracy"
   This appears in the "Understanding Your Dashboard" section
   under Emotion Analysis.

6. HARDCODED DOMAIN — find every instance of "https://emoratest.com"
   in the docs content and replace:
   - In installation snippets: already uses YOUR_DOMAIN — good
   - In SDK reference: "apiUrl defaults to https://emoratest.com"
     → change to "apiUrl is optional — defaults to the domain
     serving the SDK script"
   - In troubleshooting "Check that the script src URL is correct:
     https://emoratest.com/static/sdk/emoratest.umd.js"
     → change to "Check that the script src URL matches your
     EmoraTest instance URL"
   - In CSP troubleshooting: "Add https://emoratest.com to your CSP"
     → change to "Add your EmoraTest instance URL to your CSP
     script-src directive"

7. ANALYZING STATE — Troubleshooting section "Emotion showing as
   'Analyzing...'" → change title to "Emotion not showing yet"
   Change body to: "Emotions are predicted after the session ends
   (when the user closes the tab or navigates away). If a session
   shows 'No data', it means not enough behavioral signals were
   collected. Sessions under 5 seconds typically don't generate
   enough data for prediction."

8. OUTCOME STRING — SDK reference lists outcome 'abandon' but
   check the backend code: is the actual value 'abandon' or 'abandoned'?
   grep -r "abandon" backend/app/ --include="*.py"
   Use whatever the backend actually stores. Update docs to match.

9. AB TEST EXAMPLE — The multi-variant example shows:
   hero.innerHTML = '<h1>Join 10,000+ Customers</h1>'
   Change to a neutral example:
   hero.innerHTML = '<h1>Start your free trial</h1><p>No credit card required</p>'

10. INSTALLATION POSITION — HTML snippet says "Add this before the
    closing </body> tag" — keep this (it's correct for performance).
    Make sure no other place in the docs says </head>.

═══ OLD FEATURE NAMES ═══

11. "Understanding Your Dashboard" section — rename ALL of these:
    - "Why-Analysis" → "Diagnosis"
    - "Heatmap" → "Page Insights"
    - "Feature Flags" → "Experiments"

12. Update the descriptions to match reality:
    - Diagnosis: "Automatically detects issues on your pages — rage clicks,
      hesitation spikes, high drop-offs — and shows you why users struggle
      with recommended actions."
    - Page Insights: "See which pages cause the most emotional friction.
      Pages ranked by negative emotion percentage with element-level
      breakdown of interactive elements."
    - Experiments: "Create A/B tests, assign variants, and track which
      version performs better. Combined with emotion data to show not
      just which variant wins, but WHY it wins."
    - Sessions: "Every user visit with emotion detected, behavioral
      signals, and session outcome. Filter by emotion to find all
      frustrated or confused sessions."
    - Emotion Analysis: change "86%+ accuracy" to "80%+ accuracy"
      and change emotion list to include all 8:
      "frustration, confusion, delight, anxiety, hesitation, focus,
      boredom, and satisfaction"

13. A/B Testing section:
    - Step 1: "Go to Feature Flags" → "Go to Experiments"
    - Step 4: "Go to Feature Flags → click View Results" →
      "Go to Experiments → click your experiment to see results"

═══ MISSING CONTENT ═══

14. Add a privacy note after "What Gets Tracked Automatically":
    "Privacy & Compliance: All tracking is cookieless and GDPR-friendly.
    EmoraTest does not collect personal data, record keystrokes, take
    screenshots, or access cameras. Only anonymous behavioral patterns
    (mouse movements, clicks, scrolls) are analyzed."

15. Add to the "Getting Started" requirements:
    Change "Access to edit your website's HTML or JavaScript files"
    to "Access to edit your website's HTML, JavaScript, or build
    configuration"

After ALL changes, report:
1. Every text change made (old → new)
2. Every method added/removed from the SDK reference
3. Confirm no hardcoded "emoratest.com" remains in the docs content
   (run: grep the component for "emoratest.com")
```

## Validation:
```bash
cd frontend && npm run build
# Open docs page in browser and verify:
# 1. No "Feature Flags" text — should say "Experiments"
# 2. No "Heatmap" text — should say "Page Insights"
# 3. No "Why-Analysis" text — should say "Diagnosis"
# 4. No "86%" — should say "80%+"
# 5. No "EmoraTest.track()" — should say "EmoraTest.reportOutcome()"
# 6. No hardcoded "emoratest.com" in the docs content
# 7. React snippet has NO cleanup return in useEffect
# 8. NPM section has no install command
# 9. Privacy note visible after tracking section
# 10. All methods in SDK reference actually exist in SDK source

# Run these searches on the docs component file:
grep -n "emoratest.com" PATH_TO_DOCS_COMPONENT
grep -n "track(" PATH_TO_DOCS_COMPONENT
grep -n "86%" PATH_TO_DOCS_COMPONENT
grep -n "Feature Flag" PATH_TO_DOCS_COMPONENT
grep -n "Heatmap" PATH_TO_DOCS_COMPONENT
grep -n "Why-Analysis" PATH_TO_DOCS_COMPONENT
grep -n "Analyzing" PATH_TO_DOCS_COMPONENT
# ALL should return zero results
```