/**
 * Semantic event enrichment — transforms raw DOM tracking into business events.
 *
 * Instead of "click → div.flex-1 > button.btn-primary", we get:
 * "click → [Button] 'Start Free Trial' in hero section"
 *
 * This enables:
 * - Business-readable timelines
 * - Meaningful funnel analysis
 * - CTA performance tracking
 * - Section-based engagement metrics
 */

// ── Types ────────────────────────────────────────────────────────────

export type ElementType =
  | "button"
  | "link"
  | "input"
  | "image"
  | "container";

export type SectionType =
  | "hero"
  | "navbar"
  | "footer"
  | "pricing"
  | "features"
  | "testimonials"
  | "cta"
  | "form"
  | "sidebar"
  | "content"
  | "unknown";

export interface SemanticInfo {
  /** Human-readable label from element */
  label: string | null;
  /** Type of element (button, link, input, image, container) */
  element_type: ElementType;
  /** Section where element is located */
  section: SectionType | string | null;
  /** All data-* attributes from element */
  data_attrs: Record<string, string>;
  /** Full CSS selector for backward compatibility */
  selector: string | null;
  /** CTA role if detected */
  role?: "cta";
}

// ── Label Extraction ──────────────────────────────────────────────────

/**
 * Extract human-readable label from element.
 * Priority order: innerText > aria-label > alt > title > placeholder
 */
export function extractLabel(el: Element | null): string | null {
  if (!el) return null;

  // 1. innerText (trimmed)
  const text = el.textContent?.trim();
  if (text && text.length > 0 && text.length < 200) {
    return text;
  }

  // 2. aria-label
  const ariaLabel = el.getAttribute("aria-label");
  if (ariaLabel) {
    return ariaLabel.trim();
  }

  // 3. alt (for images)
  const alt = el.getAttribute("alt");
  if (alt) {
    return alt.trim();
  }

  // 4. title attribute
  const title = el.getAttribute("title");
  if (title) {
    return title.trim();
  }

  // 5. placeholder (for inputs)
  const placeholder = el.getAttribute("placeholder");
  if (placeholder) {
    return placeholder.trim();
  }

  return null;
}

// ── Element Type Detection ────────────────────────────────────────────

/**
 * Classify element into semantic type.
 */
export function detectElementType(el: Element | null): ElementType {
  if (!el) return "container";

  const tag = el.tagName.toLowerCase();

  // Button detection
  if (tag === "button") return "button";
  if (tag === "input") {
    const type = (el as HTMLInputElement).type?.toLowerCase();
    if (type === "submit" || type === "button") return "button";
    return "input";
  }

  // Link detection
  if (tag === "a") return "link";

  // Image detection
  if (tag === "img" || tag === "svg") return "image";

  // Check for button-like elements via role
  const role = el.getAttribute("role");
  if (role === "button") return "button";

  // Check common button patterns
  if (el.classList.contains("btn") ||
      el.classList.contains("button") ||
      /\bbtn\b|\bbutton\b/i.test(el.className)) {
    return "button";
  }

  return "container";
}

// ── Data Attribute Extraction ─────────────────────────────────────────

/**
 * Extract all data-* attributes from element.
 * Returns object with 'data-' prefix removed.
 */
export function extractDataAttrs(el: Element | null): Record<string, string> {
  if (!el) return {};

  const result: Record<string, string> = {};
  const attrs = el.attributes;

  for (let i = 0; i < attrs.length; i++) {
    const attr = attrs[i];
    if (attr.name.startsWith("data-")) {
      // Remove 'data-' prefix and convert kebab to snake_case for backend
      const key = attr.name.slice(5).replace(/-/g, "_");
      result[key] = attr.value;
    }
  }

  return result;
}

// ── Section Detection ─────────────────────────────────────────────────

/**
 * Detect which section the element belongs to.
 * First checks data-section attribute, then semantic tags, then class names.
 */
export function detectSection(el: Element | null): SectionType | string | null {
  if (!el) return null;

  // 1. Check for data-section attribute on element or ancestors
  const withSection = el.closest("[data-section]");
  if (withSection) {
    const sectionValue = withSection.getAttribute("data-section");
    if (sectionValue) return sectionValue;
  }

  // 2. Check semantic tags
  const semanticTags: Record<string, SectionType> = {
    "header": "navbar",
    "nav": "navbar",
    "footer": "footer",
    "main": "content",
    "aside": "sidebar",
    "article": "content",
    "section": "unknown",
  };

  for (const [tag, section] of Object.entries(semanticTags)) {
    const found = el.closest(tag);
    if (found) {
      // For generic section, try to infer from classes
      if (section === "unknown") {
        return inferSectionFromClass(found);
      }
      return section;
    }
  }

  // 3. Infer from class names on closest container
  const container = el.closest("div, section");
  if (container) {
    return inferSectionFromClass(container);
  }

  return "unknown";
}

/**
 * Infer section from common class name patterns.
 */
function inferSectionFromClass(el: Element): SectionType | string {
  const className = el.className.toLowerCase();
  const classList = Array.from(el.classList);

  // Direct matches
  for (const cls of classList) {
    const lower = cls.toLowerCase();
    if (/^(hero|hero-section|banner)$/.test(lower)) return "hero";
    if (/^(nav|navbar|navigation|header)$/.test(lower)) return "navbar";
    if (/^(footer|foot)$/.test(lower)) return "footer";
    if (/^(pricing|price)$/.test(lower)) return "pricing";
    if (/^(feature|features)$/.test(lower)) return "features";
    if (/^(testimonial|testimonials|review|reviews)$/.test(lower)) return "testimonials";
    if (/^(cta|call-to-action)$/.test(lower)) return "cta";
    if (/^(form|signup|subscribe|contact)$/.test(lower)) return "form";
    if (/^(sidebar|aside|menu)$/.test(lower)) return "sidebar";
  }

  // Pattern matching
  if (/\bhero\b/.test(className)) return "hero";
  if (/\bnav\b|\bnavbar\b/.test(className)) return "navbar";
  if (/\bfooter\b/.test(className)) return "footer";
  if (/\bpricing\b/.test(className)) return "pricing";
  if (/\bfeature\b/.test(className)) return "features";
  if (/\btestimonial\b|\breview\b/.test(className)) return "testimonials";
  if (/\bcta\b|\bcall.to.action\b/.test(className)) return "cta";
  if (/\bform\b|\bsignup\b|\bsubscribe\b/.test(className)) return "form";

  return "unknown";
}

// ── CTA Detection ─────────────────────────────────────────────────────

/**
 * Detect if element is a Call-To-Action button.
 * Checks text content for CTA keywords.
 */
export function detectCTA(el: Element | null, label: string | null): boolean {
  if (!el || !label) return false;

  const type = detectElementType(el);
  if (type !== "button" && type !== "link") return false;

  const text = label.toLowerCase();

  // CTA keywords
  const ctaPatterns = [
    /\bbuy\b/,
    /\bstart\b/,
    /\bsign\s*up\b/,
    /\bsign\s*in\b/,
    /\bregister\b/,
    /\bsubscribe\b/,
    /\btry\b/,
    /\bget\s*started\b/,
    /\bjoin\b/,
    /\border\s*now\b/,
    /\bshop\s*now\b/,
    /\bbook\b/,
    /\bschedule\b/,
    /\bclaim\b/,
    /\bdownload\b/,
    /\bfree\s*trial\b/,
    /\bapply\b/,
  ];

  return ctaPatterns.some(pattern => pattern.test(text));
}

// ── Full Selector Generation ───────────────────────────────────────────

/**
 * Generate a CSS selector for the element.
 * More detailed than getElementId for backward compatibility.
 */
export function getFullSelector(el: Element | null): string | null {
  if (!el) return null;

  // If has ID, that's enough
  if (el.id) {
    return `#${el.id}`;
  }

  const parts: string[] = [];
  let current: Element | null = el;

  // Walk up the tree, max 5 levels
  let depth = 0;
  while (current && depth < 5) {
    const tag = current.tagName.toLowerCase();

    if (current.id) {
      parts.unshift(`#${current.id}`);
      break;
    }

    let selector = tag;

    // Add classes if meaningful (not utility classes)
    const meaningfulClasses = Array.from(current.classList)
      .filter(c => !(/^[:,\[\]()\\/.|-]/.test(c)) && c.length < 20)
      .slice(0, 2);

    if (meaningfulClasses.length > 0) {
      selector += "." + meaningfulClasses.join(".");
    }

    // Add nth-child if no ID or classes
    if (!current.id && meaningfulClasses.length === 0) {
      const siblings = current.parentElement?.children;
      if (siblings && siblings.length > 1) {
        const index = Array.from(siblings).indexOf(current) + 1;
        selector += `:nth-child(${index})`;
      }
    }

    parts.unshift(selector);

    current = current.parentElement;
    depth++;

    // Stop at body
    if (current?.tagName.toLowerCase() === "body") {
      break;
    }
  }

  return parts.join(" > ");
}

// ── Main Enrichment Function ───────────────────────────────────────────

/**
 * Extract all semantic information from an element.
 * This is the main entry point for event enrichment.
 */
export function enrichEventElement(el: Element | null): SemanticInfo {
  if (!el) {
    return {
      label: null,
      element_type: "container",
      section: null,
      data_attrs: {},
      selector: null,
    };
  }

  const label = extractLabel(el);
  const elementType = detectElementType(el);
  const section = detectSection(el);
  const dataAttrs = extractDataAttrs(el);
  const selector = getFullSelector(el);
  const isCTA = detectCTA(el, label);

  const result: SemanticInfo = {
    label,
    element_type: elementType,
    section,
    data_attrs: dataAttrs,
    selector,
  };

  if (isCTA) {
    result.role = "cta";
  }

  return result;
}
