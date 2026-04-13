# Mobile Breakpoints Audit

## Responsive Changes Needed

### Breakpoints
- **Mobile**: < 640px (Tailwind `sm:`)
- **Tablet**: 640px - 1024px (Tailwind `md:` - `lg:`)
- **Desktop**: > 1024px (Tailwind `lg:`)

---

## ✅ Implemented (High Impact)

### 1. HeroSection - Mobile Stack (< 768px)
**Status**: ✅ DONE
**Changes**:
- Layout stacks vertically: Content → Heatmap
- HeroHeatmap scales to 100% width with `max-w-full`
- CTA buttons stack vertically (flex-col on mobile)
- Heatmap shows first on mobile with `order-1`, content `order-2`

**File**: `frontend/src/components/hero/HeroSection.tsx`

---

### 2. Navbar - Mobile Hamburger (< 768px)
**Status**: ✅ DONE
**Changes**:
- Desktop nav links hidden: `hidden lg:flex` → `hidden md:flex`
- Right side CTAs hidden: `hidden lg:flex` → `hidden md:flex`
- Mobile hamburger shown: `lg:hidden` → `md:hidden`
- Mobile menu overlay: `lg:hidden` → `md:hidden`
- Breakpoint changed from 1024px to 768px for earlier mobile behavior

**File**: `frontend/src/components/navigation/Navbar.tsx`

---

### 3. ProblemSolutionSection Tabs - Horizontal Scroll (< 640px)
**Status**: ✅ DONE
**Changes**:
- Added `overflow-x-auto snap-x snap-mandatory` for horizontal scroll
- Added `-mx-4 px-4 md:mx-0 md:px-0` for full-width scroll on mobile
- Added `no-scrollbar` utility class (hide scrollbar)
- Changed `flex-wrap justify-center` to `flex md:flex-wrap justify-start md:justify-center`
- Center wrapping on desktop, start on mobile for better UX

**File**: `frontend/src/components/problem-solution/ProblemSolutionSection.tsx`

---

## 📋 TODO (Medium/Low Priority)

### 4. Stat Cards - Horizontal Scroll on Mobile
**Status**: TODO
**File**: `frontend/src/components/hero/HeroSection.tsx`
**Changes**:
- Already has `overflow-x-auto snap-x snap-mandatory` and negative margins
- Verify `no-scrollbar` class is applied
- Ensure touch scrolling is smooth with `-webkit-overflow-scrolling: touch`

### 5. DashboardPreviewSection - Stack Layout on Mobile
**Status**: TODO
**File**: `frontend/src/components/dashboard-preview/DashboardPreviewSection.tsx`
**Changes**:
- Current: `grid lg:grid-cols-12`
- Add: `lg:grid-cols-12 grid-cols-1` or `lg:grid-cols-12 grid-cols-1 gap-12`
- Consider reversing order: Dashboard shows first on mobile

### 6. MiniDashboard - Scale Down on Mobile
**Status**: TODO
**File**: `frontend/src/components/dashboard-preview/MiniDashboard.tsx`
**Changes**:
- Add responsive sizing: `w-full lg:max-w-[680px]`
- Consider simplified view on mobile (hide complex charts)
- Add horizontal scroll for tab navigation

### 7. Final CTA - Padding Reduction on Mobile
**Status**: TODO
**File**: `frontend/src/app/(landing)/page.tsx`
**Changes**:
- Current: `py-32`
- Add: `py-20 md:py-32` or `py-16 lg:py-32`
- Ensure button width: `w-full md:w-auto`

### 8. GlassCard - Padding Reduction on Mobile
**Status**: TODO
**File**: `frontend/src/components/ui/GlassCard.tsx`
**Changes**:
- Consider responsive padding: `p-4 md:p-6 lg:p-8`
- Update `paddingClasses` to include responsive variants

### 9. Gradient Button - Full Width on Mobile
**Status**: TODO
**File**: `frontend/src/components/ui/GradientButton.tsx`
**Changes**:
- Add responsive variant: `w-full md:w-auto` prop or utility
- Useful for CTA buttons in narrow columns

### 10. EmotionBadge - Smaller on Mobile
**Status**: TODO
**File**: `frontend/src/components/ui/EmotionBadge.tsx`
**Changes**:
- Current `sm` size is already small (11px text)
- Consider adding `xs` size for dense mobile grids

### 11. BeforeAfterSlide - Height Reduction on Mobile
**Status**: TODO
**File**: `frontend/src/components/problem-solution/BeforeAfterSlide.tsx`
**Changes**:
- Current: `min-h-[380px]`
- Add: `min-h-[300px] md:min-h-[380px]`
- Reduce font sizes for title/description on mobile

### 12. Footer - Stack Layout on Mobile
**Status**: TODO (Footer not created yet)
**File**: TBD
**Changes**:
- Grid columns: `grid-cols-2 md:grid-cols-4`
- Social links: center on mobile
- Newsletter: full width on mobile

---

## Testing Checklist

- [ ] Test on iPhone SE (375px width)
- [ ] Test on iPhone 12/13 (390px width)
- [ ] Test on iPad (768px width) - verify tablet breakpoint
- [ ] Test on Desktop (1440px+ width)
- [ ] Test touch interactions (scroll, tap, swipe)
- [ ] Test PWA install on mobile
- [ ] Test landscape orientation
- [ ] Test with device emulation in DevTools

---

## Performance Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| Lighthouse Performance | > 90 | Needs audit |
| First Contentful Paint | < 1.5s | Needs audit |
| Largest Contentful Paint | < 2.5s | Needs audit |
| Time to Interactive | < 3.5s | Needs audit |
| Cumulative Layout Shift | < 0.1 | Needs audit |
