"""yt-dlp extractor plugin for ebonybaddies.com.

Without this plugin yt-dlp falls back to its generic extractor, which grabs
every inline <video> tag on the page. On this site those are 30-second hover
previews (medias.ebonybaddies.com/stream/previews/...), so model/tag pages
produce only 30s clips, and a /video/ page produces the real video plus a
pile of 30s previews of "related" videos.

  * EbonyBaddiesIE         /video/<slug>/  -> the full *_source.mp4 only
  * EbonyBaddiesPlaylistIE any other page  -> playlist of the /video/ pages
                                              linked from it (model pages,
                                              tag filters, latest_videos...)
"""

import json
import re
import urllib.parse

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
    parse_duration,
    unescapeHTML,
    unified_timestamp,
    url_or_none,
)

_BASE = 'https://ebonybaddies.com'
_FULL_VIDEO_RE = r'https?://medias\.ebonybaddies\.com/stream/(?!previews/)[^"\'\s<>]+?\.mp4[^"\'\s<>]*'


class EbonyBaddiesIE(InfoExtractor):
    IE_NAME = 'ebonybaddies'
    _VALID_URL = r'https?://(?:www\.)?ebonybaddies\.com/video/(?P<id>[^/?#]+)'

    def _video_object(self, webpage, video_id):
        for raw in re.findall(
                r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                webpage, re.S):
            try:
                data = json.loads(raw, strict=False)
            except ValueError:
                continue
            for item in (data if isinstance(data, list) else [data]):
                if not isinstance(item, dict):
                    continue
                if item.get('@type') == 'VideoObject':
                    return item
                if isinstance(item.get('video'), dict):
                    return item['video']
        return {}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        vo = self._video_object(webpage, video_id)

        video_url = (
            url_or_none(unescapeHTML(vo.get('contentUrl') or ''))
            or self._og_search_video_url(webpage, default=None)
            or self._search_regex(_FULL_VIDEO_RE, webpage, 'video url', default=None))
        if not video_url or '/stream/previews/' in video_url:
            raise ExtractorError('Could not find the full-length video on this page', expected=True)
        video_url = unescapeHTML(video_url)

        title = (
            vo.get('name')
            or self._og_search_title(webpage, default=None)
            or re.sub(r'^Video\s+|\s+-\s+ebonybaddies$', '', self._html_extract_title(webpage) or video_id))

        return {
            'id': video_id,
            'title': title,
            'description': vo.get('description') or self._og_search_description(webpage, default=None),
            'thumbnail': url_or_none(unescapeHTML(vo.get('thumbnailUrl') or '')) or self._og_search_thumbnail(webpage, default=None),
            'duration': parse_duration(vo.get('duration')),
            'timestamp': unified_timestamp(vo.get('uploadDate')),
            'age_limit': 18,
            'formats': [{
                'url': video_url,
                'format_id': 'source',
                'ext': 'mp4',
                'width': int_or_none(self._html_search_meta('og:video:width', webpage, default=None)),
                'height': int_or_none(self._html_search_meta('og:video:height', webpage, default=None)),
                'http_headers': {'Referer': url},
            }],
        }


class EbonyBaddiesPlaylistIE(InfoExtractor):
    IE_NAME = 'ebonybaddies:playlist'
    _VALID_URL = r'https?://(?:www\.)?ebonybaddies\.com/(?!video/)(?P<id>[^#]*)'

    def _real_extract(self, url):
        parsed = urllib.parse.urlparse(url)
        playlist_id = (parsed.path.strip('/') or 'home') + (f'?{parsed.query}' if parsed.query else '')
        webpage = self._download_webpage(url, playlist_id)

        slugs = orderedSet(re.findall(
            r'href=["\'](?:https?://(?:www\.)?ebonybaddies\.com)?/video/([^/"\'?#]+)/?["\']', webpage))
        if not slugs:
            raise ExtractorError('No videos found on this page', expected=True)

        entries = [
            self.url_result(f'{_BASE}/video/{slug}/', EbonyBaddiesIE, slug)
            for slug in slugs]

        title = re.sub(
            r'\s+-\s+ebonybaddies$', '',
            self._og_search_title(webpage, default=None) or self._html_extract_title(webpage) or playlist_id)
        return self.playlist_result(entries, playlist_id, title)
