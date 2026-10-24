# frontend-html

A plain `.html`/`.js` port of `../frontend/` (Vue 3 SFCs + Vite + Pinia + Vue Router)
with **no build step**: Vue 3 is loaded from a CDN `<script>` tag, every component
is a plain JS object instead of a `.vue` file, and there's no router (every page
is a real file, navigated with normal links/full reloads). `../frontend/` itself
is untouched and still works exactly as before.

The point of this folder is that you can open (or serve) any single file and see
that one component or page render, instead of needing the whole Vite app running
to check one piece of UI.

## Layout

```
frontend-html/
  index.html              gallery page linking to everything below
  shared/
    main.css              global design system (buttons, cards, tables, badges, ...)
    layout.css             sidebar + header + app-shell styles
    api.js                 axios client + one function per backend endpoint (window.Api)
    auth.js                login/logout/role helpers + the "is this page allowed" guard (window.Auth)
    nav.js                 sidebar nav item list (window.Nav)
    components.js          MetricCard, RiskBadge, SeverityBadge, LoadingState, ErrorState,
                            EmptyState, Pagination, ConfirmDialog, InterventionForm, Sidebar,
                            Header, AppShell (window.Components)
    charts.js               ProgressionChart, RiskDistributionChart, RiskTrendChart,
                            built directly on Chart.js (window.Charts)
  pages/                   one standalone .html per route in the original app
  components-preview/      one standalone .html per shared component, with sample
                            data, for checking a component in isolation
```

## Running it

This needs the **real backend** running (these pages make real API calls - there
is no mock data), plus any static file server for this folder itself.

1. Start the backend as usual (see the root `README.md`), e.g.:
   ```
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
2. Serve this folder on **port 5530** (already allow-listed in the backend's
   CORS config, see `backend/app/core/config.py` / `.env.example`):
   ```
   cd frontend-html
   npx serve -l 5530
   ```
   or
   ```
   cd frontend-html
   python -m http.server 5530
   ```
   (Don't use port 8000 for this - that's the backend. Port 5500 is a common
   default for tools like VS Code's "Live Server" extension, so 5530 is used
   here instead to avoid clashing with one you might already have running.)
3. Open **http://localhost:5530** and use the gallery, or jump straight to
   `http://localhost:5530/pages/Login.html`.

If you serve this folder on a different port, add that origin to `CORS_ORIGINS`
in your `.env` (copy `.env.example` to `.env` first if you haven't), or the
backend will reject the requests.

Demo accounts are the same as the main app - see the root `README.md`.

### Component previews

Everything under `components-preview/` can be opened directly - no login needed
for most of them, since they're just a component fed sample props. The two
exceptions are `InterventionForm.html` and `AppShell.html`'s notification badge,
which make real API calls and need you to be signed in first (open
`pages/Login.html` in another tab/window, sign in, then reload the preview -
the auth token is shared via `localStorage` on the same origin).

## Why this exists / what's different from `../frontend/`

- **No bundler.** Vue, axios and Chart.js are loaded from a CDN. Components are
  registered as plain JS objects (`{ props, data, methods, template }`) instead
  of `.vue` Single File Components.
- **No Vue Router.** Each "route" is a real `.html` file; "navigation" is a
  normal link or `location.href =`. A page like `StudentProfile.html` reads
  `?id=...` from the query string instead of a route param.
- **No Pinia.** `shared/auth.js` has the same login/role logic as
  `src/stores/auth.js` as plain functions. Since every page is a full reload
  anyway (there's no SPA state to share between "routes"), there's nothing a
  store would buy you here - each page just calls `Auth.requireUser(roles)` on
  mount, which fetches `/auth/me` and redirects to `Login.html` /
  `Unauthorized.html` exactly like the original router guard did.
- **No scoped CSS.** Each component's old `<style scoped>` block became either
  shared CSS (`main.css` for things like `MetricCard`, `layout.css` for the
  sidebar/header) or a page-specific `<style>` block in that page's own
  `<head>` - safe because each page is its own document, so there's no
  cross-page class collision to guard against.
- Backend API shape, request/response fields, and business logic are all
  unchanged - this only replaces how the UI is built and served.

## Known gaps vs. the Vue app

- No client-side route transitions - every link is a full page load.
- No automated tests (the Vue app's Vitest suite doesn't apply here).
- `axios`/Chart.js/Vue versions are pinned to match `frontend/package.json` at
  the time this was generated; bump the CDN URLs in each file's `<head>` if you
  upgrade those in `frontend/`.
