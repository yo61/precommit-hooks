// Inlined at build time from next.config.mjs `env.NEXT_PUBLIC_BASE_PATH`.
// Prepended to OG-image and markdown-content URLs so the rendered meta
// tags and "view as markdown" links resolve against the basePath-mounted
// site (e.g. `/precommit-hooks/og/docs/...`) rather than the host root.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? '';

export const appName = 'precommit-hooks';
export const docsRoute = '/';
export const docsImageRoute = `${basePath}/og/docs`;
export const docsContentRoute = `${basePath}/llms.mdx/docs`;

export const gitConfig = {
  user: 'yo61',
  repo: 'precommit-hooks',
  branch: 'main',
};
