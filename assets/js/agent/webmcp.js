/**
 * WebMCP adapter for janaka.me. The ONLY file that touches the browser's
 * WebMCP API; upgrading to a new revision of the standard should mean editing
 * this file and nothing else (docs/ai/webmcp.md).
 *
 * Standard: WebMCP, W3C Web Machine Learning CG draft (checked 2026-09-25):
 *   document.modelContext.registerTool(tool, { signal })   -> Promise<undefined>
 *   tool = { name, title, description, inputSchema, execute(input, { signal }), annotations }
 *   unregistration = aborting the signal passed at registration.
 * Chrome ships it behind an origin trial (Chrome 149-156); without a token
 * document.modelContext is undefined and this module is never even fetched:
 * assets/js/includes.js imports it only when the API exists.
 *
 * Lifecycle: tools are registered for the current page only (tools.js `scope`),
 * and withdrawn on pagehide; a page restored from the back/forward cache
 * registers them again.
 */

import { createCapabilities } from './capabilities.js';
import { createAgentService } from './tools.js';

export function readPageFrom(doc, loc) {
  const meta = doc.querySelector('meta[name="description"]');
  const scope = doc.querySelector('main') || doc.body;
  const headings = scope
    ? Array.from(scope.querySelectorAll('h2')).map((h) => h.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean)
    : [];
  return {
    path: loc.pathname,
    title: (doc.title || '').replace(/\s*[—|–·-]\s*Janaka (Premathilaka|Academy).*$/, '').trim(),
    description: meta ? meta.getAttribute('content') || '' : '',
    headings,
  };
}

async function fetchJsonSameOrigin(path) {
  const res = await fetch(path, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * Register the page's tools with a WebMCP model context.
 * Returns { names, disconnect } or null when the API is unusable.
 */
export function connect({ modelContext, service, pathname }) {
  if (!modelContext || typeof modelContext.registerTool !== 'function') return null;
  const controller = new AbortController();
  const names = [];
  for (const tool of service.toolsFor(pathname)) {
    const descriptor = {
      name: tool.name,
      title: tool.title,
      description: tool.description,
      inputSchema: tool.inputSchema,
      annotations: tool.annotations,
      execute: (input) => service.call(tool.name, input),
    };
    try {
      const pending = modelContext.registerTool(descriptor, { signal: controller.signal });
      if (pending && typeof pending.catch === 'function') {
        pending.catch((err) => console.warn('[webmcp] could not register', tool.name, err));
      }
      names.push(tool.name);
    } catch (err) {
      console.warn('[webmcp] could not register', tool.name, err);
    }
  }
  return { names, disconnect: () => controller.abort() };
}

/** Browser entry point, called by assets/js/includes.js. Safe to call more than once. */
export function start(win = window) {
  const doc = win.document;
  if (win.__jpWebMCP) return win.__jpWebMCP;
  const modelContext = doc.modelContext;
  if (!modelContext) return null;

  const caps = createCapabilities({
    fetchJson: fetchJsonSameOrigin,
    readPage: () => readPageFrom(doc, win.location),
    origin: win.location.origin,
  });
  const service = createAgentService(caps);
  let conn = connect({ modelContext, service, pathname: win.location.pathname });
  if (!conn) return null;

  win.addEventListener('pagehide', () => { if (conn) { conn.disconnect(); conn = null; } });
  win.addEventListener('pageshow', (e) => {
    if (e.persisted && !conn) conn = connect({ modelContext, service, pathname: win.location.pathname });
  });
  win.__jpWebMCP = { get tools() { return conn ? conn.names : []; } };
  return win.__jpWebMCP;
}
