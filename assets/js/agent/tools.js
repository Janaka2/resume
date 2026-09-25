/**
 * The agent-facing service: janaka.me's capabilities described as tools.
 *
 * Protocol-neutral. Each descriptor has the shape MCP and WebMCP both use
 * (name, title, description, inputSchema, annotations) plus `scope`, the pages
 * where the tool is useful, and `run`, which calls assets/js/agent/capabilities.js.
 * assets/js/agent/webmcp.js registers them with the browser; a future remote MCP
 * server or another agent protocol would wrap the same list.
 *
 * Contract (keep stable; documented in docs/ai/webmcp.md):
 *   - every tool is read-only and returns { ok: true, data } or
 *     { ok: false, error: { code, message } } with code one of
 *     invalid_input | not_found | unavailable | internal
 *   - input is validated against inputSchema before anything runs
 *   - output is JSON and kept near the ~1.5K-character tool budget
 * Budgets (Chrome WebMCP guidance): name <= 30 chars, description <= 500,
 * parameter description <= 150. tests/js/agent.test.mjs enforces them.
 */

import { CapabilityError } from './capabilities.js';

const SECTIONS = ['blog', 'academy', 'lab', 'ai', 'products'];
const READ_ONLY = { readOnlyHint: true };

const EVERYWHERE = () => true;
const CV_PAGES = (p) => p === '/' || p.startsWith('/resume/') || p.startsWith('/cv/');
const PROJECT_PAGES = (p) => p === '/' || /^\/(products|lab|ai)\//.test(p);
const CONTENT_PAGES = (p) => /^\/(blog|academy|lab|ai)\//.test(p);

export const TOOLS = [
  {
    name: 'get_profile',
    title: 'Janaka Premathilaka: profile',
    description:
      'Who Janaka Premathilaka is: job title, positioning, location and work radius, languages, core skills, ' +
      'contact email and profile links. Use it first for any question about the person or how to get in touch.',
    inputSchema: { type: 'object', properties: {}, additionalProperties: false },
    annotations: READ_ONLY,
    scope: EVERYWHERE,
    run: (caps) => caps.getProfile(),
  },
  {
    name: 'get_experience',
    title: 'Career history and credentials',
    description:
      'Employment history (period, role, organisation, location), certifications and education, as published ' +
      'on the CV. Set include_highlights for the achievements and technologies of each role.',
    inputSchema: {
      type: 'object',
      properties: {
        include_highlights: { type: 'boolean', description: 'Add each role\'s achievements and technologies. Longer output.' },
      },
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    scope: CV_PAGES,
    run: (caps, a) => caps.getExperience({ includeHighlights: !!a.include_highlights }),
  },
  {
    name: 'list_projects',
    title: 'Products and reference projects',
    description:
      'The live products (privacy-first web apps open to acquisition or licensing) and reference applications ' +
      'Janaka built, each with a slug, one-line summary, live URL and the janaka.me page that presents it.',
    inputSchema: {
      type: 'object',
      properties: {
        kind: {
          type: 'string',
          enum: ['all', 'product', 'reference-application'],
          description: 'Filter: product (for sale or licence) or reference-application. Default all.',
        },
      },
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    scope: PROJECT_PAGES,
    run: (caps, a) => caps.listProjects({ kind: a.kind || 'all' }),
  },
  {
    name: 'get_project',
    title: 'One product or project in detail',
    description:
      'Full details of one product or reference project by slug (from list_projects): summary, status, ' +
      'availability, technology stack, source repository, privacy model and related articles.',
    inputSchema: {
      type: 'object',
      properties: {
        slug: { type: 'string', pattern: '^[a-z0-9-]{1,40}$', description: 'Project slug, e.g. assetcare or nuechtern.' },
      },
      required: ['slug'],
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    scope: PROJECT_PAGES,
    run: (caps, a) => caps.getProject({ slug: a.slug }),
  },
  {
    name: 'search_site',
    title: 'Search janaka.me',
    description:
      'Keyword search over every article, Academy study page, lab note and case study on janaka.me. Returns ' +
      'the best matches with title, URL, section and a one-line description. All words must match.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', minLength: 2, maxLength: 100, description: 'Keywords, e.g. "kafka retries" or "virtual threads".' },
        section: { type: 'string', enum: SECTIONS, description: 'Limit to one section of the site.' },
        limit: { type: 'integer', minimum: 1, maximum: 10, description: 'Maximum results, 1-10. Default 5.' },
      },
      required: ['query'],
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    scope: EVERYWHERE,
    run: (caps, a) => caps.searchSite({ query: a.query, section: a.section, limit: a.limit || 5 }),
  },
  {
    name: 'list_resources',
    title: 'Browse a section',
    description:
      'Newest-first listing of the pages in one section: blog articles, Academy study pages, lab notes or AI ' +
      'pages. Use it to browse; use search_site to find a topic.',
    inputSchema: {
      type: 'object',
      properties: {
        section: { type: 'string', enum: ['blog', 'academy', 'lab', 'ai'], description: 'Which section to list.' },
        limit: { type: 'integer', minimum: 1, maximum: 20, description: 'Page size, 1-20. Default 10.' },
        offset: { type: 'integer', minimum: 0, maximum: 500, description: 'Skip this many entries for paging.' },
      },
      required: ['section'],
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    scope: CONTENT_PAGES,
    run: (caps, a) => caps.listResources({ section: a.section, limit: a.limit || 10, offset: a.offset || 0 }),
  },
  {
    name: 'get_page',
    title: 'Describe a page',
    description:
      'Title, description, dates and reading time of a janaka.me page. Without a path it describes the page ' +
      'the user is viewing, including its section outline.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', maxLength: 300, description: 'A janaka.me path such as /blog/ or /lab/assetcare/. Omit for the current page.' },
      },
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    scope: EVERYWHERE,
    run: (caps, a) => caps.getPage({ path: a.path }),
  },
];

/** Validate input against the small JSON Schema subset the tools use. Returns an error string or null. */
export function validate(schema, input) {
  if (input === undefined || input === null) input = {};
  if (typeof input !== 'object' || Array.isArray(input)) return 'input must be an object';
  const props = schema.properties || {};
  for (const key of Object.keys(input)) {
    if (!Object.prototype.hasOwnProperty.call(props, key) && schema.additionalProperties === false) {
      return `unknown parameter "${key}"`;
    }
  }
  for (const key of schema.required || []) {
    if (input[key] === undefined) return `missing required parameter "${key}"`;
  }
  for (const [key, spec] of Object.entries(props)) {
    const v = input[key];
    if (v === undefined) continue;
    if (spec.type === 'string') {
      if (typeof v !== 'string') return `"${key}" must be a string`;
      if (spec.minLength !== undefined && v.trim().length < spec.minLength) return `"${key}" is too short`;
      if (spec.maxLength !== undefined && v.length > spec.maxLength) return `"${key}" is longer than ${spec.maxLength}`;
      if (spec.pattern && !new RegExp(spec.pattern).test(v)) return `"${key}" has an invalid format`;
    } else if (spec.type === 'integer') {
      if (!Number.isInteger(v)) return `"${key}" must be an integer`;
      if (spec.minimum !== undefined && v < spec.minimum) return `"${key}" must be >= ${spec.minimum}`;
      if (spec.maximum !== undefined && v > spec.maximum) return `"${key}" must be <= ${spec.maximum}`;
    } else if (spec.type === 'boolean') {
      if (typeof v !== 'boolean') return `"${key}" must be true or false`;
    }
    if (spec.enum && !spec.enum.includes(v)) return `"${key}" must be one of ${spec.enum.join(', ')}`;
  }
  return null;
}

/** The agent service: which tools apply to a page, and a safe way to call one. */
export function createAgentService(caps) {
  return {
    toolsFor(pathname) {
      return TOOLS.filter((t) => t.scope(pathname || '/'));
    },
    async call(name, input) {
      const tool = TOOLS.find((t) => t.name === name);
      if (!tool) return { ok: false, error: { code: 'not_found', message: `unknown tool "${name}"` } };
      const problem = validate(tool.inputSchema, input);
      if (problem) return { ok: false, error: { code: 'invalid_input', message: problem } };
      try {
        return { ok: true, data: await tool.run(caps, input || {}) };
      } catch (err) {
        if (err instanceof CapabilityError) return { ok: false, error: { code: err.code, message: err.message } };
        return { ok: false, error: { code: 'internal', message: 'the tool failed; the page itself is unaffected' } };
      }
    },
  };
}
