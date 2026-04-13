# EmoraTest Landing Page Rules

## Page structure
Single scrollable page. 6 sections with anchor IDs.
NO router navigation between sections — smooth scroll only.

Section order in page.tsx:
1. <HeroSection id="hero" />
2. <FeaturesSection id="features" />
3. <HowItWorksSection id="how-it-works" />
4. <IntegrationsSection id="integrations" />
5. <PricingSection id="pricing" />
6. <FinalCTASection />

## Absolute rules
- ZERO API calls on any landing component
- ALL content is hardcoded static — no useEffect fetching
- NO LazySection wrappers on any section
- Every section accepts id prop → <section id={id}>
- All section components have "use client" at top

## Hero section
- paddingTop: 120px minimum (fixed navbar is 80px tall)
- 2 columns: 55% text / 45% heatmap
- H1: clamp(36px, 4.5vw, 56px) — never bigger
- Stat cards go BELOW 2-col grid in normal document flow
- NEVER position:absolute on stat cards
- +32% card: absolute inside heatmap column only, width 180px max
- CTA buttons: flexWrap wrap + whiteSpace nowrap

## Navbar scroll behavior
Links scroll to section IDs — never navigate to new pages:
- Features → #features
- How It Works → #how-it-works
- Integrations → #integrations
- Pricing → #pricing
Use: document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
Active link detection via IntersectionObserver.

## Colors (light mode — landing is light)
- Backgrounds: #FFFFFF and #F8F9FF alternating
- Headings: #111318
- Body: #4B5563
- Muted: #9CA3AF
- Cards: white, 1px solid #E5E7EB, radius 16px
- Gradient: linear-gradient(135deg, #007BFF, #7C3AED)

## Bugs fixed — never reintroduce
- Stat cards with position:absolute → overlap everything
- isVisible useState(false) → content disappears after 2s
- LazySection without disconnect → content flickers off
- H1 clamp too large → text overflows on small screens
- +32% card too wide → overflows hero column
- "use client" on page.tsx → breaks metadata export