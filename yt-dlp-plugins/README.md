# yt-dlp plugins

Extractor plugins bundled into the Docker image at `/etc/yt-dlp/plugins`
(yt-dlp's system plugin directory), so every yt-dlp call the web UI makes
picks them up automatically.

Layout: `<package>/yt_dlp_plugins/extractor/<module>.py` — one folder per plugin.

| Plugin | Why |
| --- | --- |
| `ebonybaddies` | yt-dlp has no extractor for the site, so the generic one grabbed the inline `<video>` tags, which are 30-second hover previews. `/video/<slug>/` pages now return only the full `*_source.mp4`; model, tag and listing pages return a playlist of their `/video/` pages. |

## Using with the stock image (no rebuild)

Bind-mount this folder read-only into the container:

```yaml
volumes:
  - /path/to/yt-dlp-plugins:/etc/yt-dlp/plugins:ro
```

## Testing locally

```sh
yt-dlp --plugin-dirs ./yt-dlp-plugins -J "https://ebonybaddies.com/video/<slug>/"
```
