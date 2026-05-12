/** Set `PUBLIC_SHOW_VIDEO_EMBEDS=true` in `.env` to render real YouTube iframes; otherwise placeholders / disabled watch links. On `/video/`, embed-off also removes YouTube thumbnail images (no i.ytimg.com requests). */
export function isVideoEmbedsEnabled(): boolean {
  return import.meta.env.PUBLIC_SHOW_VIDEO_EMBEDS === 'true'
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

function escapeText(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export interface VideoEmbedOptions {
  src: string
  title: string
  width?: number
  height?: number
}

export function videoEmbedHtml({
  src,
  title,
  width = 1080,
  height = 608,
}: VideoEmbedOptions): string {
  if (isVideoEmbedsEnabled()) {
    return `<div class="et_pb_video_box"><iframe title="${escapeAttr(title)}" width="${width}" height="${height}" src="${escapeAttr(
      src
    )}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>`
  }
  const aspect = `${width} / ${height}`
  return `<div class="et_pb_video_box et-video-placeholder-wrap" style="aspect-ratio:${aspect};max-width:100%"><div class="et-video-placeholder-inner"><p class="et-video-placeholder-title">Video coming soon</p><p class="et-video-placeholder-sub">${escapeText(
    title
  )}</p></div></div>`
}

/** YouTube watch URL for lightbox triggers; `#` when embeds are disabled so popups do not open missing videos. */
export function youTubeWatchHref(url: string): string {
  return isVideoEmbedsEnabled() ? url : '#'
}
