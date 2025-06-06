import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


class PaymentStrategy(ABC):
    """Абстрактна стратегія оплати"""

    @abstractmethod
    def pay(self, amount: Decimal) -> bool:
        """Виконати платіж на задану суму.
        Повертає True у разі успіху, False — інакше."""
        pass


class CreditCardPayment(PaymentStrategy):
    """Оплата кредитною карткою"""

    def pay(self, amount: Decimal) -> bool:
        logger.info(f"Processing credit card payment for {amount}")
        # TODO: додати реальну інтеграцію з платіжним шлюзом
        # Якщо оплата неуспішна — повертати False
        return True


class PayPalPayment(PaymentStrategy):
    """Оплата через PayPal"""

    def pay(self, amount: Decimal) -> bool:
        logger.info(f"Processing PayPal payment for {amount}")
        # TODO: інтеграція з PayPal API
        return True


class CashOnDeliveryPayment(PaymentStrategy):
    """Оплата при отриманні"""

    def pay(self, amount: Decimal) -> bool:
        logger.info(f"Order will be paid on delivery: {amount}")
        # Можна додати логіку перевірки або підтвердження при доставці
        return True


class PaymentContext:
    """Контекст для використання стратегії оплати"""

    def __init__(self, strategy: PaymentStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: PaymentStrategy) -> None:
        self._strategy = strategy

    def execute_payment(self, amount: Decimal) -> bool:
        success = self._strategy.pay(amount)
        if success:
            logger.info("Payment succeeded")
        else:
            logger.warning("Payment failed")
        return success
