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
