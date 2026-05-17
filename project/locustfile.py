"""Нагрузочный тест для DrinkShop.

Запуск (headless):
    locust -f locustfile.py --host http://127.0.0.1:8000 \\
        --users 50 --spawn-rate 10 --run-time 30s --headless \\
        --csv=load_report_50

Сценарий имитирует поведение посетителя магазина:
    1. Открывает главную (каталог) — 60% запросов.
    2. Заходит в карточку случайного товара — 25%.
    3. Добавляет товар в корзину (AJAX) — 10%.
    4. Открывает корзину — 5%.

Веса соответствуют распределению, характерному для витрин: подавляющее
большинство запросов приходится на каталог (хит-листы, категории).
"""

from __future__ import annotations

import random

from locust import HttpUser, task, between


PRODUCT_SLUGS = [
    'aktual-peach', 'kumys', 'bishkek-sut-ayran', 'monster-energy',
    'red-bull', 'nescafe-latte', 'burn-macchiato', 'adrenaline-rush',
]


class DrinkShopUser(HttpUser):
    """Виртуальный пользователь магазина."""

    wait_time = between(0.5, 2.0)
    product_ids: list[int] = []

    def on_start(self) -> None:
        # Первый запрос — главная, заодно собираем session cookie.
        self.client.get('/', name='/ (warmup)')

    @task(60)
    def browse_catalog(self) -> None:
        params = random.choice([
            {},
            {'sort': 'price_asc'},
            {'sort': 'price_desc'},
            {'q': 'вода'},
        ])
        self.client.get('/', params=params, name='/')

    @task(25)
    def product_detail(self) -> None:
        slug = random.choice(PRODUCT_SLUGS)
        self.client.get(f'/product/{slug}/', name='/product/<slug>/')

    @task(10)
    def add_to_cart(self) -> None:
        # В реальной нагрузке у нас должны быть продукты с id 1..N,
        # сгенерированные populate_data.py. Для простоты берём id 1.
        product_id = random.choice([1, 2, 3, 4])
        with self.client.post(
            f'/cart/add/{product_id}/',
            headers={'X-Requested-With': 'XMLHttpRequest'},
            name='/cart/add/<id>/',
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 302, 403):  # 403 — нет CSRF, ок
                resp.success()
            else:
                resp.failure(f'status {resp.status_code}')

    @task(5)
    def view_cart(self) -> None:
        self.client.get('/cart/', name='/cart/')
