/**
 * Domain capabilities over janaka.me's public data. Protocol-neutral and DOM-free.
 *
 * Reads only the static, generated, public JSON under /api/public/v1/
 * (scripts/gen-public-data.py). Nothing here knows about WebMCP, MCP or any
 * agent protocol; assets/js/agent/tools.js describes these functions as tools
 * and assets/js/agent/webmcp.js hands them to the browser.
 *
 * Dependencies are injected so the module runs unchanged in a browser, in Node
 * tests and behind any future adapter:
 *   fetchJson(path)  -> Promise<object>   same-origin fetch of an /api/public/v1 file
 *   readPage()       -> { path, title, description, headings[] }  the page being viewed
 */

export const API = '/api/public/v1/';

export class CapabilityError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

/** '/ai/index.html', '/ai', 'https://janaka.me/ai/' -> '/ai/' ; rejects anything off-site. */
export function normalizePath(input, origin = 'https://janaka.me') {
  let p = String(input || '').trim();
  if (!p) throw new CapabilityError('invalid_input', 'path is empty');
  for (const o of [origin, 'https://janaka.me']) {
    if (p.startsWith(o + '/')) p = p.slice(o.length);
  }
  if (!p.startsWith('/') || p.startsWith('//')) {
    throw new CapabilityError('invalid_input', 'path must be a janaka.me path such as /blog/ or /lab/assetcare/');
  }
  p = p.split('#')[0].split('?')[0];
  try { p = decodeURIComponent(p); } catch (e) { /* keep raw */ }
  p = p.replace(/\/index\.html$/, '/');
  if (!/\.[a-z0-9]+$/i.test(p) && !p.endsWith('/')) p += '/';
  return p;
}

function samePath(a, b) {
  const norm = (x) => { try { x = decodeURIComponent(x); } catch (e) { /* raw */ } return x.replace(/\/index\.html$/, '/'); };
  return norm(a) === norm(b);
}

function brief(r) {
  return { title: r.title, url: r.url, section: r.section, description: r.description };
}

export function rankResources(resources, query) {
  const tokens = String(query).toLowerCase().split(/\s+/).filter(Boolean);
  const hits = [];
  for (const r of resources) {
    const title = r.title.toLowerCase();
    const tags = (r.tags || []).join(' ').toLowerCase();
    const desc = (r.description || '').toLowerCase();
    let score = 0;
    let ok = true;
    for (const t of tokens) {
      const inTitle = title.includes(t), inTags = tags.includes(t), inDesc = desc.includes(t);
      if (!inTitle && !inTags && !inDesc) { ok = false; break; }
      score += (inTitle ? 10 : 0) + (inTags ? 3 : 0) + (inDesc ? 1 : 0);
    }
    if (ok) hits.push({ r, score });
  }
  hits.sort((a, b) => b.score - a.score || (b.r.published || '').localeCompare(a.r.published || ''));
  return hits.map((h) => h.r);
}

export function createCapabilities({ fetchJson, readPage = null, origin = 'https://janaka.me' }) {
  const cache = new Map();
  const load = (file) => {
    if (!cache.has(file)) {
      cache.set(file, Promise.resolve(fetchJson(API + file)).catch((err) => {
        cache.delete(file);
        throw new CapabilityError('unavailable', `could not load ${API + file}: ${err && err.message ? err.message : err}`);
      }));
    }
    return cache.get(file);
  };

  return {
    async getProfile() {
      const { person } = await load('profile.json');
      return {
        name: person.name,
        jobTitle: person.jobTitle,
        positioning: person.positioning,
        summary: person.description,
        location: `${person.location.locality}, ${person.location.country}`,
        workRadius: person.location.workRadius,
        languages: person.languages.map((l) => `${l.name}: ${l.level}`),
        skills: person.knowsAbout,
        contact: { email: person.contact.email, page: person.contact.page },
        links: { site: person.url, cv: person.cv.page, cvPdf: person.cv.pdf, profiles: person.sameAs },
      };
    },

    async getExperience({ includeHighlights = false } = {}) {
      const doc = await load('profile.json');
      return {
        source: doc.person.cv.page,
        roles: doc.experience.map((r) => ({
          period: r.period,
          title: r.title,
          organisation: r.organisation,
          location: r.location,
          ...(includeHighlights ? { highlights: r.highlights, technologies: r.technologies } : {}),
        })),
        certifications: doc.certifications.map((c) => c.name + (c.issuer ? ` (${c.issuer})` : '')),
        education: doc.education.map((e) => `${e.degree}, ${e.institution}, ${e.period}`),
      };
    },

    async listProjects({ kind = 'all' } = {}) {
      const { projects } = await load('projects.json');
      return projects
        .filter((p) => kind === 'all' || p.kind === kind)
        .map((p) => ({ slug: p.slug, name: p.name, kind: p.kind, summary: p.summary, url: p.url, page: p.page }));
    },

    async getProject({ slug }) {
      const { projects } = await load('projects.json');
      const p = projects.find((x) => x.slug === slug);
      if (!p) {
        throw new CapabilityError('not_found', `no project "${slug}"; known: ${projects.map((x) => x.slug).join(', ')}`);
      }
      const { api, ...rest } = p;
      return rest;
    },

    async searchSite({ query, section, limit = 5 }) {
      const { resources } = await load('resources.json');
      const pool = section ? resources.filter((r) => r.section === section) : resources;
      const hits = rankResources(pool, query);
      return { query, total: hits.length, results: hits.slice(0, limit).map(brief) };
    },

    async listResources({ section, limit = 10, offset = 0 }) {
      const { resources } = await load('resources.json');
      const pool = resources.filter((r) => r.section === section);
      return {
        section,
        total: pool.length,
        offset,
        results: pool.slice(offset, offset + limit).map((r) => ({ ...brief(r), published: r.published })),
      };
    },

    async getPage({ path } = {}) {
      const current = readPage ? readPage() : null;
      const wanted = path ? normalizePath(path, origin) : (current && current.path);
      if (!wanted) throw new CapabilityError('invalid_input', 'path is required outside a browser page');
      const { resources } = await load('resources.json');
      const r = resources.find((x) => samePath(x.path, wanted));
      const isCurrent = current && samePath(current.path, wanted);
      if (!r && !isCurrent) {
        throw new CapabilityError('not_found', `no indexed page at ${wanted}; use search_site to find one`);
      }
      return {
        path: wanted,
        url: r ? r.url : origin + wanted,
        title: r ? r.title : current.title,
        section: r ? r.section : undefined,
        description: r ? r.description : current.description,
        tags: r ? r.tags : undefined,
        published: r ? r.published : undefined,
        updated: r ? r.updated : undefined,
        readingMinutes: r ? r.readingMinutes : undefined,
        outline: isCurrent ? current.headings.slice(0, 25) : undefined,
      };
    },
  };
}
