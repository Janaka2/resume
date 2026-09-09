---
name: i18n-add
description: Mechanics for adding or changing translatable text on the hub page (index.html and partials) - data-i18n attributes, the DE dictionary in assets/js/i18n.js, HTML-in-values rules, and verification. Load whenever hub copy changes.
---

# Adding or changing hub copy (EN/DE)

The hub captures English from the markup at boot and swaps in German from `window.JP_I18N`'s `DE` object keyed by `data-i18n`.

## Add a new string

1. Put the English text in the element and give it a unique key: `<p data-i18n="pjLede">English text</p>`. Key convention: section prefix + camelCase (`hero*`, `about*`, `c*` contact cards, `wh*` work history, `p1*`/`p2*` products, `pj*` projects, `nav*`, `btn*`).
2. Add the German entry in the matching section comment block of `assets/js/i18n.js`: `pjLede: 'Deutscher Text',`.
3. If the element contains inline HTML (`<b>`, `<span class="badge">`, `<li>`), the DE value must contain the same tags and classes; the whole innerHTML is replaced.
4. Escape single quotes inside values or use double quotes for that entry. Keep `&amp;` entities as in the markup.

## Change an existing string

Edit the English in the partial and the German in the dictionary in the same commit. Never leave one side stale.

## Remove a string

Delete the attribute and the dictionary entry.

## Verify

```bash
node --check assets/js/i18n.js
# keys in markup
grep -rhoE 'data-i18n="[^"]+"' index.html partials/*.html | grep -v BK | sort -u | sed 's/data-i18n="//;s/"//' > /tmp/keys.txt
# keys in dictionary
grep -oE '^\s+[a-zA-Z0-9]+:' assets/js/i18n.js | tr -d ' :' | sort -u > /tmp/de.txt
comm -23 /tmp/keys.txt /tmp/de.txt   # missing in DE
comm -13 /tmp/keys.txt /tmp/de.txt   # unused DE keys
```

Then open the site, press DE, and read the changed section. Hand off to the `i18n-translator` agent for language quality when the change is more than a line.
