# SigriCo — Everyday Fresh

Marketing site for **SigriCo**, a Mexican offshore-aquaculture company raising premium
*Seriola* (yellowtail) in the open Pacific.

Single-page, immersive deep-ocean design: animated bioluminescent light shafts, a
particle field, and scroll-reveal motion. Static HTML/CSS/JS — no build step.

> Design language adapted from the aura.build "Oceans of Andromeda" template.
> Currently **English only** — a Spanish version is planned once this is approved.

## Run locally

Any static server works, e.g.:

```bash
npx serve .          # then open the printed URL
# or
python3 -m http.server 4361
```

## Structure

```
index.html      Markup (single page)
styles.css      All styles + design tokens (brand colors, type)
js/main.js      Light-shaft/particle canvas, scroll reveals, nav state, contact form
images/         Logos, favicon, and web-optimized photography (ph-*.jpg)
assets/         Source logo art (.ai / .pdf)
```

## Configuration TODO before / after launch

- **Contact form email** — the form uses [FormSubmit](https://formsubmit.co) (no signup).
  In `index.html`:
  - set the primary inbox: replace `YOUR_EMAIL` in the form `action`
  - optional 2nd recipient(s): set the `_cc` hidden field (comma-separate for more)
  - submit once to receive FormSubmit's one-time activation email, then click it.
- **Photography** — `images/ph-*.jpg` are atmospheric ocean stand-ins pulled from the
  current site. Swap in real farm / pens / Seriola / harvest / product photos when available.
- **Spanish (ES) version** — on hold until the English version is approved.

## Deploy (GitHub Pages)

Push to GitHub and enable Pages on the default branch (root). For the custom domain,
add a `CNAME` file containing `sigrico.com` and point DNS at GitHub Pages.

## Credits

- Type: [Jost](https://fonts.google.com/specimen/Jost) (Futura substitute) + [Caudex](https://fonts.google.com/specimen/Caudex), via Google Fonts
- Brand colors: teal `#16A4B0`, gold `#BB922E`
