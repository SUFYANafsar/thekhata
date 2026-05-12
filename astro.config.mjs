// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://FBRsoftware.com',
  trailingSlash: 'always',
  output: 'static',
  integrations: [mdx(), sitemap()],
});