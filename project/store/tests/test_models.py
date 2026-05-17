"""Unit-тесты моделей предметной области.

Цель тестов — зафиксировать инварианты модели (`subtotal` корректно вычисляется,
`Cart.total_price` согласован с суммой позиций, `is_paid`/`requires_online_payment`
работают на известных значениях статуса) и тем самым защититься от регрессий
при рефакторинге.
"""

from decimal import Decimal

from django.test import TestCase

from store.models import Cart, CartItem, Order
from .factories import make_category, make_product, make_user


class CartModelTests(TestCase):
    """Тесты корзины и её элементов."""

    def setUp(self) -> None:
        self.category = make_category()
        self.product_a = make_product(
            self.category, name='Вода 0.5', slug='water-05',
            price='40.00', volume='0.5 л',
        )
        self.product_b = make_product(
            self.category, name='Вода 1.5', slug='water-15',
            price='75.00', volume='1.5 л',
        )
        self.user = make_user()

    def test_cart_item_subtotal(self) -> None:
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product_a, quantity=3)
        self.assertEqual(item.subtotal, Decimal('120.00'))

    def test_cart_total_price_sums_all_items(self) -> None:
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_a, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product_b, quantity=1)
        # 40*2 + 75*1 = 155
        self.assertEqual(cart.total_price, Decimal('155.00'))
        self.assertEqual(cart.total_items, 3)

    def test_cart_item_unique_per_product(self) -> None:
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product_a, quantity=1)
        # Повторное добавление той же пары (cart, product) должно падать
        # за счёт unique_together — это сохраняет согласованность данных.
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CartItem.objects.create(cart=cart, product=self.product_a, quantity=1)


class OrderModelTests(TestCase):
    """Тесты заказа — статусы оплаты и вспомогательные свойства."""

    def test_default_payment_state(self) -> None:
        order = Order.objects.create(
            first_name='Иван', last_name='Петров', phone='+996700000000',
            address='Бишкек', total_price=Decimal('500.00'),
        )
        self.assertEqual(order.payment_method, Order.PAYMENT_METHOD_COD)
        self.assertEqual(order.payment_status, Order.PAYMENT_STATUS_PENDING)
        self.assertFalse(order.is_paid)
        self.assertFalse(order.requires_online_payment)
        self.assertEqual(order.transaction_id, '')

    def test_online_paid_order_flags(self) -> None:
        order = Order.objects.create(
            first_name='Иван', last_name='Петров', phone='+996700000000',
            address='Бишкек', total_price=Decimal('500.00'),
            payment_method=Order.PAYMENT_METHOD_ONLINE,
            payment_status=Order.PAYMENT_STATUS_PAID,
            transaction_id='TEST-ABC123',
        )
        self.assertTrue(order.is_paid)
        self.assertTrue(order.requires_online_payment)
        self.assertIn('TEST-ABC123', order.transaction_id)
