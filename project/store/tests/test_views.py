"""Интеграционные тесты представлений.

Эти тесты проходят весь слой HTTP (URL-диспетчер → view → ORM → шаблон),
что ловит регрессии в маршрутизации и контрактах шаблонов.
"""

from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from store.models import Cart, CartItem, Order
from .factories import make_category, make_product, make_user


class CatalogViewTests(TestCase):

    def setUp(self) -> None:
        self.category = make_category()
        self.product = make_product(self.category)
        self.client = Client()

    def test_index_returns_200_and_lists_product(self) -> None:
        response = self.client.get(reverse('store:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_detail_returns_200(self) -> None:
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)


class CartViewTests(TestCase):

    def setUp(self) -> None:
        self.category = make_category()
        self.product = make_product(self.category)

    def test_cart_add_creates_item(self) -> None:
        client = Client()
        response = client.post(
            reverse('store:cart_add', kwargs={'product_id': self.product.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(response.json()['cart_count'], 1)

    def test_cart_add_increments_quantity_on_repeat(self) -> None:
        client = Client()
        url = reverse('store:cart_add', kwargs={'product_id': self.product.pk})
        client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(CartItem.objects.first().quantity, 2)


class CheckoutViewTests(TestCase):
    """Тесты оформления заказа с разными способами оплаты."""

    def setUp(self) -> None:
        self.category = make_category()
        self.product = make_product(self.category, price='100.00')
        self.client = Client()
        # Кладём товар в корзину анонимного пользователя
        self.client.post(
            reverse('store:cart_add', kwargs={'product_id': self.product.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def _checkout_payload(self, **overrides):
        data = {
            'first_name': 'Иван',
            'last_name': 'Петров',
            'phone': '+996700000000',
            'address': 'Бишкек, Чуй 1',
            'comment': '',
            'payment_method': Order.PAYMENT_METHOD_COD,
            'card_number': '',
        }
        data.update(overrides)
        return data

    def test_checkout_cod_creates_pending_order(self) -> None:
        response = self.client.post(reverse('store:checkout'),
                                    data=self._checkout_payload())
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.payment_method, Order.PAYMENT_METHOD_COD)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_PENDING)
        self.assertEqual(order.total_price, Decimal('100.00'))
        # Корзина очищена
        self.assertEqual(CartItem.objects.count(), 0)

    def test_checkout_online_marks_order_as_paid(self) -> None:
        response = self.client.post(reverse('store:checkout'),
                                    data=self._checkout_payload(
                                        payment_method=Order.PAYMENT_METHOD_ONLINE,
                                        card_number='4242 4242 4242 4242',
                                    ))
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.payment_method, Order.PAYMENT_METHOD_ONLINE)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_PAID)
        self.assertTrue(order.transaction_id.startswith('TEST-'))
        self.assertEqual(order.status, 'processing')

    def test_checkout_online_declined_card_marks_failed(self) -> None:
        response = self.client.post(reverse('store:checkout'),
                                    data=self._checkout_payload(
                                        payment_method=Order.PAYMENT_METHOD_ONLINE,
                                        card_number='4000000000000002',
                                    ))
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_FAILED)
        self.assertEqual(order.transaction_id, '')
        # Статус доставки не должен смениться на "в обработке"
        self.assertEqual(order.status, 'new')


class MergeCartOnLoginTests(TestCase):
    """Проверяет ключевой бизнес-сценарий: анонимная корзина объединяется с
    пользовательской после входа/регистрации."""

    def setUp(self) -> None:
        self.category = make_category()
        self.product_a = make_product(self.category, slug='a', name='A')
        self.product_b = make_product(self.category, slug='b', name='B', price='30.00')

    def test_anon_cart_merges_into_user_cart_on_register(self) -> None:
        client = Client()
        # Анонимное добавление A
        client.post(
            reverse('store:cart_add', kwargs={'product_id': self.product_a.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        # Регистрация
        response = client.post(reverse('store:register'), data={
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        # Корзина пользователя должна содержать товар A
        from django.contrib.auth.models import User
        user = User.objects.get(username='newbie')
        user_cart = Cart.objects.get(user=user)
        self.assertEqual(user_cart.items.count(), 1)
        self.assertEqual(user_cart.items.first().product, self.product_a)

    def test_anon_and_user_cart_merge_quantities(self) -> None:
        """При логине количества одинаковых товаров суммируются."""
        user = make_user('existing')
        # В существующей корзине пользователя — товар A (2 шт)
        user_cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=user_cart, product=self.product_a, quantity=2)

        # Аноним добавляет тот же товар 1 шт и ещё товар B 1 шт
        client = Client()
        client.post(
            reverse('store:cart_add', kwargs={'product_id': self.product_a.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        client.post(
            reverse('store:cart_add', kwargs={'product_id': self.product_b.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        # Логин
        response = client.post(reverse('store:login'), data={
            'username': 'existing',
            'password': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)

        user_cart.refresh_from_db()
        items = {item.product_id: item.quantity for item in user_cart.items.all()}
        self.assertEqual(items[self.product_a.pk], 3)  # 2 + 1
        self.assertEqual(items[self.product_b.pk], 1)
        # Анонимная корзина удалена
        self.assertFalse(Cart.objects.filter(user__isnull=True).exists())
