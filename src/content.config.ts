import { defineCollection, z } from 'astro:content'
import { glob } from 'astro/loaders'

const blog = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    slug: z.string(),
    canonical: z.string(),
    ogImage: z.string().optional(),
    published: z.string().optional(),
    modified: z.string().optional(),
    schemaJson: z.string().optional(),
    /** WP post ID — used to load `/wp-content/et-cache/{id}/*.css` when present in `public/`. */
    wpPostId: z.number().optional(),
    /** LiteSpeed sheet paired with this post (customizer global or et-core-unified cached inline). */
    etInlineCss: z.string().optional(),
  }),
})

const kb = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/kb' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    slug: z.string(),
    canonical: z.string(),
    ogImage: z.string().optional(),
    modified: z.string().optional(),
  }),
})

export const collections = { blog, kb }
