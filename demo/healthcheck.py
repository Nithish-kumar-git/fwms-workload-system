"""Loopback-only health probe; does not inspect or log database configuration."""
import json
import os
import sys
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def check_health(env, opener=None):
    port = int(env.get('PORT', '8000'))
    if not 1 <= port <= 65535:
        raise ValueError('Invalid PORT')
    opener = opener or urllib.request.build_opener(NoRedirect)
    with opener.open(f'http://127.0.0.1:{port}/api/health', timeout=3) as response:
        data = json.load(response)
        return response.status == 200 and data.get('status') == 'ok' and data.get('environment') == 'synthetic-demo'


if __name__ == '__main__':
    try:
        sys.exit(0 if check_health(os.environ) else 1)
    except Exception:
        sys.exit(1)
