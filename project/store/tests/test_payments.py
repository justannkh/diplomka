"""Тесты сервисного слоя оплаты."""

from decimal import Decimal

from django.test import SimpleTestCase

from store.payments import FakePaymentGateway


class FakePaymentGatewayTests(SimpleTestCase):

    def setUp(self) -> None:
        self.gateway = FakePaymentGateway()

    def test_positive_amount_valid_card_succeeds(self) -> None:
        result = self.gateway.charge(
            amount=Decimal('100.00'), order_id=1,
            card_number='4242424242424242',
        )
        self.assertTrue(result.success)
        self.assertTrue(result.transaction_id.startswith('TEST-'))

    def test_declined_test_card_is_rejected(self) -> None:
        result = self.gateway.charge(
            amount=Decimal('100.00'), order_id=2,
            card_number=FakePaymentGateway.DECLINED_TEST_CARD,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.transaction_id, '')
        self.assertIn('отклонена', result.message.lower())

    def test_zero_amount_rejected(self) -> None:
        result = self.gateway.charge(
            amount=Decimal('0.00'), order_id=3,
            card_number='4242424242424242',
        )
        self.assertFalse(result.success)

    def test_invalid_card_number_rejected(self) -> None:
        result = self.gateway.charge(
            amount=Decimal('100.00'), order_id=4,
            card_number='12',  # слишком короткая
        )
        self.assertFalse(result.success)
