"""Сервисный слой оплаты.

Модуль инкапсулирует работу с платёжным шлюзом. В учебном проекте используется
детерминированный эмулятор, который возвращает успех/ошибку по заданному
правилу, но интерфейс `PaymentGateway.charge` совместим с API большинства
реальных провайдеров (Stripe, YooKassa, FreedomPay): на вход принимается
сумма, заказ и опциональные параметры карты, на выход — объект
`PaymentResult` с `success`, `transaction_id`, `message`.

Такая изоляция полезна сразу с двух сторон: (а) код представления `checkout`
не зависит от конкретного шлюза; (б) в unit-тестах эмулятор подменяется
детерминированной заглушкой без каких-либо моков HTTP-клиента.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PaymentResult:
    """Результат попытки списания средств.

    `success` — булев флаг, `transaction_id` — идентификатор транзакции
    (в реальном шлюзе это ID платежа у провайдера), `message` — пояснение
    для пользователя и лога.
    """

    success: bool
    transaction_id: str
    message: str


class PaymentGateway:
    """Интерфейс шлюза оплаты."""

    def charge(
        self,
        amount: Decimal,
        order_id: int,
        card_number: Optional[str] = None,
    ) -> PaymentResult:  # pragma: no cover - интерфейс
        raise NotImplementedError


class FakePaymentGateway(PaymentGateway):
    """Детерминированный эмулятор платёжного шлюза.

    Правила приёма:
      * сумма должна быть положительной;
      * если передан номер карты, он должен содержать 12–19 цифр и иметь
        корректную контрольную сумму по алгоритму Луна;
      * тестовая карта `4000 0000 0000 0002` всегда отклоняется —
        это позволяет писать детерминированные отрицательные тесты.
    """

    DECLINED_TEST_CARD = '4000000000000002'

    def charge(
        self,
        amount: Decimal,
        order_id: int,
        card_number: Optional[str] = None,
    ) -> PaymentResult:
        if amount is None or Decimal(amount) <= 0:
            return PaymentResult(
                success=False,
                transaction_id='',
                message='Сумма платежа должна быть положительной.',
            )

        if card_number:
            digits = ''.join(ch for ch in card_number if ch.isdigit())
            if not 12 <= len(digits) <= 19:
                return PaymentResult(
                    success=False,
                    transaction_id='',
                    message='Некорректный номер карты.',
                )
            if digits == self.DECLINED_TEST_CARD:
                return PaymentResult(
                    success=False,
                    transaction_id='',
                    message='Карта отклонена эмитентом (тестовый отказ).',
                )
            if not _luhn_ok(digits):
                return PaymentResult(
                    success=False,
                    transaction_id='',
                    message='Номер карты не проходит проверку по алгоритму Луна.',
                )

        transaction_id = f'TEST-{uuid.uuid4().hex[:16].upper()}'
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            message=f'Оплата по заказу #{order_id} принята.',
        )


def _luhn_ok(digits: str) -> bool:
    """Проверка номера карты по алгоритму Луна."""
    total = 0
    reverse_digits = digits[::-1]
    for i, ch in enumerate(reverse_digits):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def get_default_gateway() -> PaymentGateway:
    """Фабрика шлюза по умолчанию. В реальном проекте здесь читался бы
    settings.PAYMENT_GATEWAY и возвращалась конкретная реализация."""
    return FakePaymentGateway()
