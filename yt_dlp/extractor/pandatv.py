import functools
import urllib.parse

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    UserNotLive,
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PandaLiveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)pandalive\.co\.kr/live/play/(?P<id>[a-z0-9]+)'
    _TESTS = [{
        'url': 'https://www.pandalive.co.kr/live/play/foryoung65',
        'info_dict': {
            'id': 'foryoung65',
            'ext': 'mp4',
            'title': str,
            'live_status': 'is_live',
        },
        'skip': 'The channel is not currently live',
    }]

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        form_data = {
            'action': 'watch',
            'userId': channel_id,
            'password': '',
            'shareLinkType': '',
        }
        try:
            live_detail = self._download_json(
                'https://api.pandalive.co.kr/v1/live/play', channel_id, data=urllib.parse.urlencode(form_data).encode('utf-8'),
                note='Downloading channel info', errnote='Unable to download channel info')
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 400:
                raise UserNotLive(video_id=channel_id)
            raise

        m3u8_url = traverse_obj(live_detail, ('PlayList', 'hls', 0, 'url'))
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(m3u8_url, channel_id, 'mp4', live=True, m3u8_id='hls', entry_protocol='m3u8_native')

        return {
            'id': channel_id,
            'is_live': True,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(live_detail.get('media'), {
                'title': ('title', {str}),
                'timestamp': ('startTime', {functools.partial(parse_iso8601, delimiter=' ')}),
                'thumbnail': ('thumbUrl', {url_or_none}),
                'view_count': ('user', {int_or_none}),
                'play_count': ('playCnt', {int_or_none}),
                'like_count': ('likeCnt', {int_or_none}),
                'user_id': ('userId', {str}),
                'user_idx': ('userIdx', {int_or_none}),
                'user_nickname': ('userNick', {str}),
            }),
        }
