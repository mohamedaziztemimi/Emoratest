# Semantic Event Enrichment — Before vs After

## Overview

Transforms raw DOM tracking into meaningful business events.

Instead of: `click → div.flex-1 > button.btn-primary`
We get: `click → [Button] "Start Free Trial" in hero section`

---

## Before: Raw DOM Event (Legacy)

```json
{
  "type": "click",
  "ts": "2026-04-22T10:30:45.123Z",
  "x": 250,
  "y": 400,
  "element_id": "button.btn-primary",
  "metadata": {
    "rage_click": false
  }
}
```

**Problems:**
- ❌ Element ID is cryptic (CSS selector)
- ❌ No human-readable label
- ❌ Unknown element type
- ❌ No section context
- ❌ Cannot tell what user clicked on

---

## After: Semantic Business Event (New)

```json
{
  "type": "click",
  "ts": "2026-04-22T10:30:45.123Z",
  "x": 250,
  "y": 400,
  "element_id": "button.btn-primary",
  "label": "Start Free Trial",
  "element_type": "button",
  "section": "hero",
  "selector": "button.btn-primary",
  "metadata": {
    "role": "cta",
    "rage_click": false
  }
}
```

**Benefits:**
- ✅ Human-readable label: "Start Free Trial"
- ✅ Element type: "button"
- ✅ Section context: "hero"
- ✅ CTA role detected
- ✅ Backward compatible: element_id preserved

---

## Example Enriched Events

### Example 1: CTA Button Click

**HTML:**
```html
<section data-section="hero">
  <button class="btn-primary">Start Free Trial</button>
</section>
```

**Event:**
```json
{
  "type": "click",
  "label": "Start Free Trial",
  "element_type": "button",
  "section": "hero",
  "selector": "button.btn-primary",
  "metadata": {
    "role": "cta"
  }
}
```

---

### Example 2: Pricing Plan Selection

**HTML:**
```html
<section class="pricing-section">
  <div class="plan" data-plan="pro" data-price="$49">
    <button>Choose Pro Plan</button>
  </div>
</section>
```

**Event:**
```json
{
  "type": "click",
  "label": "Choose Pro Plan",
  "element_type": "button",
  "section": "pricing",
  "selector": "button",
  "metadata": {
    "role": "cta",
    "plan": "pro",
    "price": "$49"
  }
}
```

**Note:** Data attributes (`data-plan`, `data-price`) are automatically extracted and included in metadata.

---

### Example 3: Navigation Link

**HTML:**
```html
<nav class="navbar">
  <a href="/pricing">Pricing</a>
</nav>
```

**Event:**
```json
{
  "type": "click",
  "label": "Pricing",
  "element_type": "link",
  "section": "navbar",
  "selector": "a"
}
```

---

### Example 4: Product Card Click

**HTML:**
```html
<div class="product-card" data-product-id="123" data-category="electronics">
  <img src="product.jpg" alt="Wireless Headphones">
  <h3>Wireless Headphones</h3>
  <button>Add to Cart</button>
</div>
```

**Clicking "Add to Cart":**
```json
{
  "type": "click",
  "label": "Add to Cart",
  "element_type": "button",
  "section": "content",
  "selector": "button",
  "metadata": {
    "role": "cta",
    "product_id": "123",
    "category": "electronics"
  }
}
```

---

### Example 5: Image Click

**HTML:**
```html
<figure data-section="hero">
  <img src="hero-image.jpg" alt="Person using the app">
</figure>
```

**Event:**
```json
{
  "type": "click",
  "label": "Person using the app",
  "element_type": "image",
  "section": "hero",
  "selector": "img"
}
```

---

### Example 6: Form Input Focus

**HTML:**
```html
<form data-section="signup" class="signup-form">
  <input type="email" placeholder="Enter your email" name="email">
</form>
```

**Event:**
```json
{
  "type": "click",
  "label": "Enter your email",
  "element_type": "input",
  "section": "signup",
  "selector": "input[name='email']"
}
```

---

### Example 7: Rage Click on Button

**HTML:**
```html
<button class="submit-btn">Submit</button>
```

**After 3 rapid clicks:**
```json
{
  "type": "click",
  "label": "Submit",
  "element_type": "button",
  "section": "form",
  "selector": "button.submit-btn",
  "metadata": {
    "role": "cta",
    "rage_click": true,
    "click_count": 3
  }
}
```

---

## Label Extraction Priority

The system extracts labels in this priority order:

1. **innerText** (trimmed) — visible text content
2. **aria-label** — accessibility label
3. **alt** — image alternative text
4. **title** — tooltip attribute
5. **placeholder** — input placeholder text

---

## Element Type Classification

| HTML Tag/Pattern | element_type |
|------------------|--------------|
| `<button>` | button |
| `<input type="submit">` | button |
| `<input type="button">` | button |
| `[role="button"]` | button |
| `.btn`, `.button` (class) | button |
| `<a>` | link |
| `<input>` (other) | input |
| `<img>`, `<svg>` | image |
| Other | container |

---

## Section Detection

Sections are detected in this priority order:

1. **`data-section` attribute** — explicit markup
2. **Semantic tags** — `<header>`, `<nav>`, `<footer>`, `<main>`, `<aside>`, `<article>`
3. **Class patterns** — `.hero`, `.navbar`, `.footer`, `.pricing`, `.features`, `.testimonials`, `.cta`, `.form`, `.sidebar`

---

## CTA Detection

Elements with these text patterns are marked as CTA:

- buy, start, signup*, register, subscribe
- try, get started, join, order now, shop now
- book, schedule, claim, download
- free trial, apply

---

## Data Attribute Extraction

All `data-*` attributes are extracted and included in metadata:

```html
<button data-product="premium" data-variant="annual" data-referral="partner">
  Buy Premium
</button>
```

```json
{
  "type": "click",
  "label": "Buy Premium",
  "element_type": "button",
  "metadata": {
    "role": "cta",
    "product": "premium",
    "variant": "annual",
    "referral": "partner"
  }
}
```

---

## Validation Checklist

- [x] Events show human-readable labels
- [x] Element type detected (button, link, etc.)
- [x] Section context included (hero, navbar, etc.)
- [x] CTA buttons marked with role="cta"
- [x] Data attributes captured (product_id, etc.)
- [x] Backward compatibility maintained (element_id, selector)
- [x] Rage click detection still works

---

## Timeline View Example

Before semantic enrichment:
```
10:30:45 - click on button.btn-primary
10:30:50 - click on a.nav-link
10:31:02 - click on button.submit
```

After semantic enrichment:
```
10:30:45 - click [Button] "Start Free Trial" in hero
10:30:50 - click [Link] "Pricing" in navbar
10:31:02 - click [Button] "Submit" in signup form
```

---

## Business Value

### For Product Teams
- Understand what users click (not just where)
- Track CTA performance across sections
- Analyze user journey by section transitions

### For Marketing
- Measure which CTAs drive conversions
- Compare performance of different button labels
- Track engagement by page section

### For Support
- Reproduce user issues with readable steps
- Understand context of rage clicks (which button frustrated the user)

---

## Files Modified

1. **sdk/src/semantic.ts** (NEW) — Semantic enrichment functions
2. **sdk/src/types.ts** — Added label, element_type, section, selector to RawEvent
3. **sdk/src/collectors.ts** — Integrated semantic enrichment into click and mousemove collectors

---

## Migration Notes

### Backward Compatibility

Old fields are preserved:
- `element_id` — Original CSS selector
- `metadata` — All behavioral signals

New fields are additive:
- `label` — Human-readable label
- `element_type` — Semantic type
- `section` — Page section
- `selector` — Full CSS path

### Database Impact

The backend database schema may need updates to handle the new fields. Consider:
- Adding indexed columns for `label`, `element_type`, `section`
- Storing `data_attrs` as JSONB
- Updating analytics queries to use semantic fields
