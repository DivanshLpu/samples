# Link Tree

A simple, responsive collapsible link tree built with plain HTML, CSS, and JavaScript.

## Features

- Light background with dark text and a clean blue accent
- Responsive design that looks good on mobile and desktop
- Collapsible tree branches with smooth expand/collapse animations
- No dependencies or build step required
- Multiple themes with a built-in theme switcher

## Themes

| Theme | File | Description |
|-------|------|-------------|
| Default | `style.css` | Clean professional look with blue accents |
| Cherry Blossom | `theme-cherry-blossom.css` | Soft pinkish theme with rose accents |
| Techie | `theme-techie.css` | Dark theme with neon cyan accents and monospace font |

### Switching Themes

**Via dropdown (recommended):**
- Use the theme selector dropdown at the top of the page
- Your choice is saved in `localStorage` and persists across reloads

**Via HTML:**
- Change the `href` attribute on the stylesheet link in `index.html`:
  ```html
  <link rel="stylesheet" href="theme-techie.css" id="theme-link" />
  ```

## Files

- `index.html` – page structure with theme selector
- `style.css` – default theme styling
- `theme-cherry-blossom.css` – cherry blossom pinkish theme
- `theme-techie.css` – dark techie theme
- `theme-switcher.js` – handles theme switching and persistence
- `script.js` – renders the tree from a data array

## Usage

1. Open `index.html` in any browser.
2. Edit the `links` array in `script.js` to add your own groups and links.

### Editing links

```js
const links = [
  {
    label: "Projects",
    children: [
      { label: "Portfolio", url: "https://example.com" },
      { label: "Blog", url: "https://example.com/blog" }
    ]
  },
  { label: "Website", url: "https://example.com" }
];
```

- An item with a `children` array renders as a collapsible branch.
- An item with only a `url` renders as a single link card.

## License

Free to use and modify.
