#!/usr/bin/env python
"""Быстрая проверка Integration API без Telegram."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carsales.settings')

import django
import requests

django.setup()

from django.contrib.auth.models import User
from cars.models import Profile, Auto

BASE = os.getenv('SITE_BASE_URL', 'http://127.0.0.1:8000')
KEY = os.getenv('INTEGRATION_API_KEY', 'dev-integration-key-change-me')
HEADERS = {'X-Integration-Key': KEY}


def check(name, ok, detail=''):
    status = 'OK' if ok else 'FAIL'
    print(f'[{status}] {name}' + (f' — {detail}' if detail else ''))
    return ok


def main():
    results = []

    # 1. Search without auth user
    r = requests.get(f'{BASE}/api/integration/autos/search/', headers=HEADERS, params={'q': ''}, timeout=5)
    payload = r.json()
    count = len(payload.get('results', payload)) if isinstance(payload, dict) else len(payload)
    results.append(check('GET /api/integration/autos/search/', r.status_code == 200, f'{count} авто'))

    auto = Auto.objects.available().first()
    if auto:
        r2 = requests.get(f'{BASE}/api/integration/autos/{auto.id}/', headers=HEADERS, timeout=5)
        results.append(check('GET /api/integration/autos/{id}/', r2.status_code == 200, str(auto)))

    # 2. Link flow
    user = User.objects.first()
    if user:
        profile, _ = Profile.objects.get_or_create(user=user)
        token = profile.regenerate_telegram_link_token()
        r3 = requests.post(
            f'{BASE}/api/integration/link/',
            headers=HEADERS,
            json={'token': token, 'telegram_chat_id': 999888777, 'telegram_username': 'test_user'},
            timeout=5,
        )
        results.append(check('POST /api/integration/link/', r3.status_code == 200, r3.json().get('username', '')))

        r4 = requests.get(
            f'{BASE}/api/integration/favorites/',
            headers=HEADERS,
            params={'telegram_chat_id': 999888777},
            timeout=5,
        )
        results.append(check('GET /api/integration/favorites/', r4.status_code == 200))

        if auto:
            r5 = requests.post(
                f'{BASE}/api/integration/messages/',
                headers=HEADERS,
                json={'telegram_chat_id': 999888777, 'auto_id': auto.id, 'message': 'Тест из integration test'},
                timeout=5,
            )
            ok = r5.status_code in (201, 400)
            results.append(check('POST /api/integration/messages/', ok, r5.json().get('detail', r5.json().get('message', ''))))

    # 3. Wrong key
    r_bad = requests.get(f'{BASE}/api/integration/autos/search/', headers={'X-Integration-Key': 'wrong'}, timeout=5)
    results.append(check('Security: wrong API key rejected', r_bad.status_code == 403))

    passed = sum(results)
    total = len(results)
    print(f'\nИтого: {passed}/{total}')
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
