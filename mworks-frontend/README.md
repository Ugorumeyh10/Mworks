# Mworks — Frontend

A trust-verified marketplace for RPA automations, AI prompts, jobs, and
training-partner showcases. This is the working frontend, built from the
approved Deep Indigo & Brass design system.

## Stack

- React 18 + Vite
- React Router (client-side routing)
- Plain CSS (design tokens in `src/index.css`, no framework) — matches the
  brand system exactly without pulling in Tailwind's own defaults.

## Getting started

```bash
npm install
npm run dev       # local dev server
npm run build     # production build -> dist/
```

## Structure

```
src/
  index.css            design tokens (colors, fonts) + shared base styles
  App.jsx              routes
  components/
    AppShell.jsx/.css   responsive nav shell (sidebar desktop / bottom bar mobile)
    Icon.jsx            <Icon name="heart" /> wrapper around the sprite
    IconSprite.jsx       all SVG icon symbols, defined once
    PostCard.jsx/.css    feed post card (automation / prompt / job / training)
  pages/
    DiscoverFeed.jsx     social feed, tabs: For You / Following / Jobs / Training
    Listing.jsx          listing detail — verification log, metrics, buy flow
    JobAgent.jsx         AI Job Agent — auto-apply toggle, fit-scored job list
    Messages.jsx         buyer/seller/employer conversations
    Assistant.jsx        Mworks Assistant chat (scoped to the user's own data)
  data/
    sampleData.js        mock content — swap for real API calls
```

## Design system

Colors and type live entirely in `src/index.css` as CSS custom properties:

- `--brass` (#C9A24B) — reserved for trust signals only: verified badges,
  the verification log, escrow-release states, ratings, primary CTAs.
- `--steel` (#6F92C4) — everyday actions: follow, browse, secondary buttons.
- `--panel` / `--panel-2` / `--panel-3` — the indigo surface hierarchy.
- Fonts: Manrope (headings) + Inter (body), loaded via Google Fonts in
  `index.css`.

Keep that brass/steel discipline when adding new screens — brass should
never decorate something the platform hasn't actually verified.

## What's stubbed vs real

Everything here runs on `src/data/sampleData.js` — no backend calls yet.
The natural next slice of work:

1. Replace `sampleData.js` reads with real API calls (React Query or
   similar) once the backend exists.
2. Wire `Assistant.jsx`'s canned reply to a real assistant endpoint.
3. Wire the Job Agent's auto-apply toggle to a real user-preference API,
   and the job list to whatever job-sourcing service replaces the
   scraping/API integration discussed in the BRD.
4. Add auth (currently the sidebar just shows a static "Henry" profile).
