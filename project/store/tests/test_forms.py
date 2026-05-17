"""Тесты форм.

Фокус — на валидации бизнес-правил:
    * при выборе онлайн-оплаты обязательно указание номера карты;
    * при выборе оплаты при получении номер карты игнорируется;
    * формат номера карты ограничен 12–19 цифрами.
"""

from django.test import TestCase

from store.forms import OrderForm
from store.models import Order


class OrderFormValidationTests(TestCase):

    def _base_data(self, **overrides):
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

    def test_cod_does_not_require_card(self) -> None:
        form = OrderForm(data=self._base_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_online_requires_card(self) -> None:
        form = OrderForm(data=self._base_data(
            payment_method=Order.PAYMENT_METHOD_ONLINE,
            card_number='',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('card_number', form.errors)

    def test_online_rejects_too_short_card(self) -> None:
        form = OrderForm(data=self._base_data(
            payment_method=Order.PAYMENT_METHOD_ONLINE,
            card_number='1234',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('card_number', form.errors)

    def test_online_accepts_formatted_card_number(self) -> None:
        """Номер карты допускает пробелы и дефисы — главное, цифр 12–19."""
        form = OrderForm(data=self._base_data(
            payment_method=Order.PAYMENT_METHOD_ONLINE,
            card_number='4242 4242 4242 4242',
        ))
        self.assertTrue(form.is_valid(), form.errors)
