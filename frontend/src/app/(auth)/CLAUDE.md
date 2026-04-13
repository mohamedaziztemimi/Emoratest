# EmoraTest Auth Pages Rules

## Layout
- No navbar or sticky bar on auth pages
- Centered card layout, max-width 440px
- Gradient background: `linear-gradient(135deg, #F0F4FF 0%, #F8F0FF 100%)`

## Components
- Both login and signup pages are "use client" components
- Each page has EmoraTest logo + name at top (gradient text)
- White card with border-gray-200, rounded-2xl, shadow-sm

## API Integration
- API base URL from `process.env.NEXT_PUBLIC_API_URL`
- POST `/api/auth/login` → `{ email, password }`
- POST `/api/auth/signup` → `{ name, email, password, workspace_name }`
- Use `credentials: 'include'` for httpOnly cookies
- On success → `window.location.href = '/dashboard'`
- On error → show error in red banner above submit button

## Validation (signup only)
- All fields required
- Email must contain @
- Password must be min 8 characters
- Show inline error below each field in red if invalid

## Security Rules
- **Never** store JWT in localStorage — httpOnly cookie only
- **Never** log passwords to console
- **Never** include password in error messages

## Redirects
- `/login` → link to `/signup` for "Start free"
- `/signup` → link to `/login` for "Sign in"
- `/dashboard/*` protected by middleware (redirect to `/login` if no session)
