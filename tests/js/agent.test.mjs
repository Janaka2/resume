// Tests for the agent capability layer and the WebMCP adapter.
// Run: node --test "tests/js/*.test.mjs"   (no dependencies; uses the generated api/public/v1 files)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

import { createCapabilities, normalizePath, rankResources } from '../../assets/js/agent/capabilities.js';
import { TOOLS, validate, createAgentService } from '../../assets/js/agent/tools.js';
import { connect, start, readPageFrom } from '../../assets/js/agent/webmcp.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const fetchJson = async (p) => JSON.parse(readFileSync(path.join(ROOT, p), 'utf8'));
const fakePage = { path: '/blog/posts/rag-faiss-patterns.html', title: 'RAG with FAISS', description: 'd', headings: ['Why', 'How'] };
const service = () => createAgentService(createCapabilities({ fetchJson, readPage: () => fakePage }));

// --- contract ----------------------------------------------------------------

test('tool surface is small, read-only and within the WebMCP budgets', () => {
  assert.ok(TOOLS.length >= 5 && TOOLS.length <= 10, `${TOOLS.length} tools`);
  const names = new Set();
  for (const t of TOOLS) {
    assert.match(t.name, /^[a-z][a-z0-9_]{2,29}$/, t.name);
    assert.ok(!names.has(t.name), `duplicate ${t.name}`);
    names.add(t.name);
    assert.ok(t.description.length <= 500, `${t.name} description ${t.description.length}`);
    assert.ok(t.title && t.title.length <= 60, `${t.name} title`);
    assert.equal(t.annotations.readOnlyHint, true, `${t.name} must be read-only`);
    assert.equal(t.inputSchema.type, 'object');
    assert.equal(t.inputSchema.additionalProperties, false, `${t.name} must reject unknown parameters`);
    for (const [k, spec] of Object.entries(t.inputSchema.properties)) {
      assert.ok(k.length <= 30, `${t.name}.${k} name`);
      assert.ok(spec.description && spec.description.length <= 150, `${t.name}.${k} description`);
      if (spec.type === 'string') assert.ok(spec.maxLength || spec.enum || spec.pattern, `${t.name}.${k} unbounded string`);
    }
  }
});

test('tools are scoped to the pages where they help', () => {
  const s = service();
  const on = (p) => s.toolsFor(p).map((t) => t.name);
  assert.deepEqual(on('/').sort(), ['get_experience', 'get_page', 'get_profile', 'get_project', 'list_projects', 'search_site']);
  assert.ok(on('/resume/').includes('get_experience'));
  assert.ok(!on('/blog/posts/x.html').includes('get_experience'));
  assert.ok(on('/blog/posts/x.html').includes('list_resources'));
  assert.ok(on('/products/').includes('get_project'));
  assert.ok(!on('/academy/').includes('list_projects'));
  for (const p of ['/', '/blog/', '/academy/modules/2026/FSE/kafka.html', '/products/']) {
    assert.ok(on(p).length <= 7, `${p} registers ${on(p).length}`);
  }
});

// --- validation ----------------------------------------------------------------

test('schema validation rejects malformed and oversized input', () => {
  const search = TOOLS.find((t) => t.name === 'search_site').inputSchema;
  assert.equal(validate(search, { query: 'kafka' }), null);
  assert.match(validate(search, {}), /missing required/);
  assert.match(validate(search, { query: 1 }), /string/);
  assert.match(validate(search, { query: 'x' }), /too short/);
  assert.match(validate(search, { query: 'k'.repeat(101) }), /longer/);
  assert.match(validate(search, { query: 'kafka', limit: 11 }), /<= 10/);
  assert.match(validate(search, { query: 'kafka', limit: 2.5 }), /integer/);
  assert.match(validate(search, { query: 'kafka', section: 'admin' }), /one of/);
  assert.match(validate(search, { query: 'kafka', url: 'x' }), /unknown parameter/);
  assert.match(validate(search, 'kafka'), /object/);
  assert.match(validate(search, { query: 'kafka', constructor: 1 }), /unknown parameter/);
  assert.match(validate(search, JSON.parse('{"query":"kafka","__proto__":{"x":1}}')), /unknown parameter/);
  assert.match(validate(search, [1]), /object/);
  const proj = TOOLS.find((t) => t.name === 'get_project').inputSchema;
  assert.match(validate(proj, { slug: '../../etc/passwd' }), /invalid format/);
});

test('paths are confined to janaka.me', () => {
  assert.equal(normalizePath('/ai/index.html'), '/ai/');
  assert.equal(normalizePath('/ai'), '/ai/');
  assert.equal(normalizePath('https://janaka.me/blog/posts/rag-faiss-patterns.html#x'), '/blog/posts/rag-faiss-patterns.html');
  for (const bad of ['https://evil.example/', '//evil.example/x', 'javascript:alert(1)', 'file:///etc/passwd', '']) {
    assert.throws(() => normalizePath(bad), /path/, bad);
  }
});

// --- behaviour -----------------------------------------------------------------

test('get_profile returns public identity and nothing private', async () => {
  const r = await service().call('get_profile', {});
  assert.equal(r.ok, true);
  assert.equal(r.data.name, 'Janaka Premathilaka');
  assert.ok(r.data.contact.email.includes('@'));
  const text = JSON.stringify(r);
  assert.doesNotMatch(text, /\+41|tel:|password|AssetCare-Demo/i);
  assert.ok(text.length < 2000, `profile output ${text.length} chars`);
});

test('get_experience lists roles; highlights only on request', async () => {
  const s = service();
  const short = await s.call('get_experience', {});
  assert.equal(short.ok, true);
  assert.ok(short.data.roles.length >= 3);
  assert.equal(short.data.roles[0].highlights, undefined);
  const long = await s.call('get_experience', { include_highlights: true });
  assert.ok(long.data.roles[0].highlights.length > 0);
});

test('projects: list, filter, detail, unknown slug', async () => {
  const s = service();
  const all = await s.call('list_projects', {});
  assert.ok(all.data.some((p) => p.slug === 'assetcare'));
  const products = await s.call('list_projects', { kind: 'product' });
  assert.ok(products.data.every((p) => p.kind === 'product'));
  const one = await s.call('get_project', { slug: 'assetcare' });
  assert.equal(one.ok, true);
  assert.ok(one.data.stack.length > 0);
  const missing = await s.call('get_project', { slug: 'no-such-thing' });
  assert.deepEqual(missing.ok, false);
  assert.equal(missing.error.code, 'not_found');
});

test('search_site finds real content and stays small', async () => {
  const r = await service().call('search_site', { query: 'kafka' });
  assert.equal(r.ok, true);
  assert.ok(r.data.results.length > 0 && r.data.results.length <= 5);
  assert.ok(r.data.results.every((x) => x.url.startsWith('https://janaka.me/')));
  assert.ok(JSON.stringify(r).length < 2500);
  const none = await service().call('search_site', { query: 'zzqqxx nothing' });
  assert.equal(none.data.total, 0);
  const bad = await service().call('search_site', { query: 'x' });
  assert.equal(bad.error.code, 'invalid_input');
});

test('ranking prefers title matches', () => {
  const res = [
    { title: 'Other', description: 'kafka mentioned', tags: [] },
    { title: 'Kafka guide', description: '', tags: [] },
  ];
  assert.equal(rankResources(res, 'kafka')[0].title, 'Kafka guide');
});

test('list_resources pages through a section', async () => {
  const s = service();
  const first = await s.call('list_resources', { section: 'academy', limit: 3 });
  const second = await s.call('list_resources', { section: 'academy', limit: 3, offset: 3 });
  assert.equal(first.data.results.length, 3);
  assert.notEqual(first.data.results[0].url, second.data.results[0].url);
});

test('get_page describes the current page or a given path; rejects off-site', async () => {
  const s = service();
  const here = await s.call('get_page', {});
  assert.equal(here.ok, true);
  assert.deepEqual(here.data.outline, ['Why', 'How']);
  const other = await s.call('get_page', { path: '/lab/assetcare/' });
  assert.equal(other.ok, true);
  assert.match(other.data.title, /AssetCare/);
  const off = await s.call('get_page', { path: 'https://evil.example/' });
  assert.equal(off.error.code, 'invalid_input');
  const missing = await s.call('get_page', { path: '/nope/' });
  assert.equal(missing.error.code, 'not_found');
});

test('a data failure becomes a controlled error, and recovers on retry', async () => {
  let fail = true;
  const caps = createCapabilities({ fetchJson: async (p) => { if (fail) throw new Error('offline'); return fetchJson(p); } });
  const s = createAgentService(caps);
  const r = await s.call('get_profile', {});
  assert.equal(r.ok, false);
  assert.equal(r.error.code, 'unavailable');
  fail = false;
  assert.equal((await s.call('get_profile', {})).ok, true);
});

test('unknown tools and internal errors never throw', async () => {
  const s = createAgentService({ getProfile: () => { throw new TypeError('boom'); } });
  assert.equal((await s.call('nope', {})).error.code, 'not_found');
  const r = await s.call('get_profile', {});
  assert.equal(r.error.code, 'internal');
  assert.doesNotMatch(r.error.message, /boom/);
});

// --- adapter -------------------------------------------------------------------

function fakeModelContext() {
  const registered = new Map();
  return {
    registered,
    registerTool(tool, { signal }) {
      assert.ok(signal instanceof AbortSignal, 'registerTool must receive an AbortSignal');
      registered.set(tool.name, tool);
      signal.addEventListener('abort', () => registered.delete(tool.name));
      return Promise.resolve();
    },
  };
}

function fakeWindow(pathname, modelContext) {
  const listeners = {};
  return {
    listeners,
    location: { pathname, origin: 'https://janaka.me' },
    document: { modelContext, title: 'T', querySelector: () => null, body: null },
    addEventListener: (type, fn) => { (listeners[type] ||= []).push(fn); },
    dispatch(type, ev = {}) { (listeners[type] || []).forEach((fn) => fn(ev)); },
  };
}

test('unsupported browser: nothing registers and nothing throws', () => {
  assert.equal(connect({ modelContext: undefined, service: service(), pathname: '/' }), null);
  assert.equal(connect({ modelContext: {}, service: service(), pathname: '/' }), null);
  assert.equal(start(fakeWindow('/', undefined)), null);
});

test('supported browser: page tools register, execute, and unregister on teardown', async () => {
  const mc = fakeModelContext();
  const conn = connect({ modelContext: mc, service: service(), pathname: '/products/' });
  assert.ok(conn.names.includes('get_project'));
  assert.ok(!conn.names.includes('get_experience'));
  const tool = mc.registered.get('get_project');
  for (const k of ['name', 'title', 'description', 'inputSchema', 'annotations', 'execute']) assert.ok(k in tool, k);
  const out = await tool.execute({ slug: 'loop' }, { signal: new AbortController().signal });
  assert.equal(out.ok, true);
  assert.equal(out.data.name, 'Loop');
  const bad = await tool.execute({ slug: 42 });
  assert.equal(bad.error.code, 'invalid_input');
  conn.disconnect();
  assert.equal(mc.registered.size, 0);
});

test('start(): withdraws tools on pagehide and restores them from the back/forward cache', () => {
  const mc = fakeModelContext();
  const win = fakeWindow('/', mc);
  const handle = start(win);
  assert.ok(handle.tools.length > 0);
  assert.equal(start(win), handle, 'idempotent');
  win.dispatch('pagehide');
  assert.equal(mc.registered.size, 0);
  win.dispatch('pageshow', { persisted: true });
  assert.ok(mc.registered.size > 0);
});

test('a registerTool failure does not break the page', () => {
  const mc = { registerTool: () => { throw new Error('denied'); } };
  const warn = console.warn;
  console.warn = () => {};
  try {
    const conn = connect({ modelContext: mc, service: service(), pathname: '/' });
    assert.deepEqual(conn.names, []);
  } finally {
    console.warn = warn;
  }
});

test('readPageFrom reads title, description and h2 outline', () => {
  const doc = {
    title: 'Kafka — Janaka Academy',
    querySelector: (sel) => (sel.startsWith('meta') ? { getAttribute: () => 'desc' } : { querySelectorAll: () => [{ textContent: ' A \n b ' }] }),
  };
  assert.deepEqual(readPageFrom(doc, { pathname: '/x.html' }), { path: '/x.html', title: 'Kafka', description: 'desc', headings: ['A b'] });
});

test('includes.js runs cleanly in a browser without WebMCP', () => {
  const src = readFileSync(path.join(ROOT, 'assets/js/includes.js'), 'utf8');
  const events = [];
  const sandbox = {
    console,
    window: { isSecureContext: true, dispatchEvent() {} },
    document: { addEventListener: (t) => events.push(t), querySelector: () => null, head: { appendChild() {} } },
  };
  vm.runInNewContext(src, sandbox);
  assert.deepEqual(events, ['DOMContentLoaded']);
});
