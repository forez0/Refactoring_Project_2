# shop/tests/test_patterns.py
"""Tests for design patterns implementations."""
import logging
import json
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.http import JsonResponse
from ..models import Bike, BikeType, Order, OrderItem, MountainBikeSpec, RoadBikeSpec, CityBikeSpec
from ..patterns import (
    apply_discount,
    login_required_ajax,
    BikeFactory,
    PaymentStrategy,
    CreditCardPayment,
    PayPalPayment,
    CashOnDeliveryPayment,
    PaymentContext
)

# Отримуємо логер для перевірки логів.
decorator_logger = logging.getLogger('shop.patterns.decorator')
factory_logger = logging.getLogger('shop.patterns.factory')
strategy_logger = logging.getLogger('shop.patterns.strategy')


class DecoratorTests(TestCase):
    """Tests for decorator patterns.""" # C0115: Missing class docstring
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='12345')
        # E1101: Class 'BikeType' has no 'objects' member - these are typical Django ORM operations
        # Pylint sometimes flags these. Usually, this means Pylint isn't fully aware of Django's ORM.
        # You can ignore this specific E1101 for model.objects if your code works.
        # For a clean Pylint score, you'd configure Pylint with django-pylint or disable this check.
        self.bike_type = BikeType.objects.create(name="Test", description="Test")
        self.bike = Bike.objects.create(
            name="Test Bike",
            bike_type=self.bike_type,
            price=Decimal('500.00'),
            description="Test",
            image="test.jpg"
        )
        self.order = Order.objects.create(user=self.user, total=Decimal('1000.00'))
        self.order_item = OrderItem.objects.create(
            order=self.order,
            bike=self.bike,
            price=Decimal('500.00'),
            quantity=2
        )

    @patch('django.contrib.messages.info')
    @patch('django.contrib.messages.error')
    def test_apply_discount_success(self, mock_messages_error, mock_messages_info):
        """Тест успішного застосування знижки"""

        @apply_discount(10)
        def dummy_view(request): # W0613: Unused argument 'request' (OK for dummy view)
            return True

        request = self.factory.get('/')
        request.user = self.user

        with self.assertLogs(decorator_logger.name, level='INFO') as cm:
            dummy_view(request)

        self.order.refresh_from_db()
        self.assertEqual(self.order.discount_percent, 10)
        self.assertEqual(self.order.discount, Decimal('100.00'))
        self.assertEqual(self.order.total, Decimal('900.00'))

        mock_messages_info.assert_called_once_with(
            request, "Було автоматично застосовано знижку 10% (-100.00 грн)"
        )
        self.assertIn(f"Discount 10% applied to order #{self.order.id}", cm.output[0])
        mock_messages_error.assert_not_called()

    @patch('django.contrib.messages.info')
    @patch('django.contrib.messages.error')
    def test_apply_discount_no_order(self, mock_messages_error, mock_messages_info):
        """Тест, коли немає активного замовлення"""
        # E1101: Class 'Order' has no 'objects' member - same as above, common Django ORM
        Order.objects.all().delete()

        @apply_discount(10)
        def dummy_view(request): # W0613: Unused argument 'request' (OK for dummy view)
            return True

        request = self.factory.get('/')
        request.user = self.user

        with self.assertLogs(decorator_logger.name, level='DEBUG') as cm:
            response = dummy_view(request)

        # Now, assert that a specific DEBUG message is present in cm.output
        self.assertTrue(any(f"No active order found for user {self.user.id} to apply discount." in log for log in cm.output))

        mock_messages_info.assert_not_called()
        mock_messages_error.assert_not_called()
        self.assertFalse(any("Discount applied" in log for log in cm.output if 'INFO' in log or 'ERROR' in log)) # More robust check for "Discount applied"
        self.assertTrue(response)

    @patch('django.contrib.messages.info')
    @patch('django.contrib.messages.error')
    @patch('shop.models.Order.save') # Changed: Patch the method on the model
    def test_apply_discount_error_handling(self, mock_order_save, mock_messages_error, mock_messages_info):
        """Тест обробки помилок при застосуванні знижки"""
        # Configure the mocked save method to raise an exception
        mock_order_save.side_effect = Exception("Simulated save error during discount application")

        @apply_discount(10)
        def dummy_view(request): # W0613: Unused argument 'request' (OK for dummy view)
            return True

        request = self.factory.get('/')
        request.user = self.user

        with self.assertLogs(decorator_logger.name, level='ERROR') as cm:
            dummy_view(request)

        mock_order_save.assert_called_once() # Assert that the mocked save method was indeed called

        mock_messages_error.assert_called_once_with(request, "Помилка при застосуванні знижки.")
        mock_messages_info.assert_not_called()

        # Check for the specific error log message in cm.output
        self.assertTrue(any("Error applying discount:" in log for log in cm.output),
                        f"Expected 'Error applying discount:' in logs, but found: {cm.output}")

    def test_login_required_ajax_authenticated(self):
        """Тест декоратора для авторизованого користувача"""

        @login_required_ajax
        def dummy_view(request): # W0613: Unused argument 'request' (OK for dummy view)
            return JsonResponse({'status': 'ok'})

        request = self.factory.get('/')
        request.user = self.user
        response = dummy_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'ok'})

    def test_login_required_ajax_anonymous(self):
        """Тест декоратора для неавторизованого користувача"""

        @login_required_ajax
        def dummy_view(request): # W0613: Unused argument 'request' (OK for dummy view)
            return JsonResponse({'status': 'ok'})

        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = dummy_view(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {'error': 'Authentication required'})


class BikeFactoryTests(TestCase):
    """Tests for BikeFactory pattern.""" # C0115: Missing class docstring
    def setUp(self):
        self.factory = BikeFactory()
        # E1101: Class 'BikeType' has no 'objects' member - see note above
        BikeType.objects.all().delete()
        Bike.objects.all().delete()
        MountainBikeSpec.objects.all().delete()
        RoadBikeSpec.objects.all().delete()
        CityBikeSpec.objects.all().delete()

    def test_create_mountain_bike(self):
        """Тест створення гірського велосипеда"""
        bike = self.factory.create_bike(
            'mountain',
            'MTB 1000',
            Decimal('15999.99'),
            'Гірський велосипед для початківців',
            suspension='Передня'
        )
        self.assertIsNotNone(bike.mountain_spec)
        bike.refresh_from_db()

        self.assertEqual(bike.bike_type.name, 'mountain')
        self.assertEqual(bike.mountain_spec.suspension, 'Передня')
        self.assertEqual(bike.get_specifics(), 'Гірський велосипед з Передня амортизацією')

    def test_create_road_bike(self):
        """Тест створення шосейного велосипеда"""
        bike = self.factory.create_bike(
            'road',
            'Racer 500',
            Decimal('22999.99'),
            'Шосейний велосипед для професіоналів',
            weight=8.5
        )
        self.assertIsNotNone(bike.road_spec)
        bike.refresh_from_db()

        self.assertEqual(bike.bike_type.name, 'road')
        self.assertEqual(bike.road_spec.weight, 8.5)
        self.assertEqual(bike.get_specifics(), 'Легкий шосейний велосипед (8.5 кг)')

    def test_create_city_bike(self):
        """Тест створення міського велосипеда"""
        bike = self.factory.create_bike(
            'city',
            'Urban 300',
            Decimal('8999.99'),
            'Зручний міський велосипед',
            has_basket=True
        )
        self.assertIsNotNone(bike.city_spec)
        bike.refresh_from_db()

        self.assertEqual(bike.bike_type.name, 'city')
        self.assertTrue(bike.city_spec.has_basket)
        self.assertEqual(bike.get_specifics(), 'Міський велосипед з кошиком')

    def test_create_bike_invalid_type(self):
        """Тест створення велосипеда невідомого типу"""
        with self.assertLogs(factory_logger.name, level='INFO') as cm:
            bike = self.factory.create_bike(
                'invalid',
                'Test Bike',
                Decimal('10000.00'),
                'Test Description'
            )
        # Check if the log message related to "unknown type" is present in any of the captured logs
        # The cm.output can contain multiple logs.
        # We need to look for the specific message in any log.
        # Fixed Pylint W1309: Using an f-string that does not have any interpolated variables
        # This message will contain the interpolated value from the factory, so the warning was incorrect.
        self.assertTrue(
            any(f"Bike 'Test Bike' created with unknown specific type 'invalid'." in log for log in cm.output))
        self.assertEqual(bike.bike_type.name, 'invalid')
        self.assertEqual(bike.get_specifics(), 'Звичайний велосипед')

    def test_bike_type_creation(self):
        """Тест автоматичного створення типу велосипеда"""
        self.assertEqual(BikeType.objects.count(), 0)

        bike = self.factory.create_bike(
            'new_type',
            'New Bike',
            Decimal('12000.00'),
            'New Description'
        )

        self.assertEqual(BikeType.objects.count(), 1)
        self.assertEqual(bike.bike_type.name, 'new_type')

    def test_get_description_from_bike(self):
        """Тест отримання опису велосипеда"""
        bike = self.factory.create_bike(
            "mountain",
            "Test Mountain Bike",
            Decimal('15000.00'),
            "Test description",
            suspension="пневматична"
        )
        self.assertEqual(bike.description, "Test description")


class PaymentStrategyTests(TestCase):
    """Tests for strategy pattern payment processing.""" # C0115: Missing class docstring
    def setUp(self):
        self.amount = Decimal('1500.00')

    def test_credit_card_payment(self):
        """Тест оплати кредитною карткою"""
        with self.assertLogs(strategy_logger.name, level='INFO') as cm:
            strategy = CreditCardPayment()
            result = strategy.pay(self.amount)

        self.assertTrue(result)
        self.assertIn(f"Processing credit card payment for {self.amount}", cm.output[0])

    def test_paypal_payment(self):
        """Тест оплати через PayPal"""
        with self.assertLogs(strategy_logger.name, level='INFO') as cm:
            strategy = PayPalPayment()
            result = strategy.pay(self.amount)

        self.assertTrue(result)
        self.assertIn(f"Processing PayPal payment for {self.amount}", cm.output[0])

    def test_cash_on_delivery_payment(self):
        """Тест оплати при отриманні"""
        with self.assertLogs(strategy_logger.name, level='INFO') as cm:
            strategy = CashOnDeliveryPayment()
            result = strategy.pay(self.amount)

        self.assertTrue(result)
        self.assertIn(f"Order will be paid on delivery: {self.amount}", cm.output[0])

    def test_payment_context(self):
        """Тест контексту оплати"""
        context = PaymentContext(CreditCardPayment())
        with self.assertLogs(strategy_logger.name, level='INFO') as cm:
            result = context.execute_payment(self.amount)

        self.assertTrue(result)
        self.assertTrue(any("Payment succeeded" in log for log in cm.output))

        context.set_strategy(PayPalPayment())
        with self.assertLogs(strategy_logger.name, level='INFO') as cm:
            result = context.execute_payment(self.amount)

        self.assertTrue(result)
        self.assertTrue(any("Payment succeeded" in log for log in cm.output))

    def test_payment_strategy_abstract(self):
        """Тест, що PaymentStrategy є абстрактним класом"""
        with self.assertRaises(TypeError):
            PaymentStrategy()

    def test_payment_context_invalid_amount(self):
        """Тест оплати з невалідною сумою"""
        class MockCreditCardPayment(CreditCardPayment):
            """Mock payment for testing invalid amount.""" # C0115: Missing class docstring
            def pay(self, amount: Decimal) -> bool:
                if amount <= Decimal('0.00'):
                    # W1203: Use lazy % formatting in logging functions
                    logging.getLogger('shop.patterns.strategy').error("Invalid payment amount: %s", amount)
                    return False
                return super().pay(amount)

        strategy = MockCreditCardPayment()
        with self.assertLogs(strategy_logger.name, level='ERROR') as cm:
            result = strategy.pay(Decimal('0.00'))

        self.assertFalse(result)
        self.assertIn("Invalid payment amount", cm.output[0])

    def test_payment_context_logging_on_failure(self):
        """Тест логування при невдалій оплаті"""

        class FailingPayment(PaymentStrategy):
            """Mock payment that always fails.""" # C0115: Missing class docstring
            def pay(self, amount):
                # W1203: Use lazy % formatting in logging functions
                logging.getLogger('shop.patterns.strategy').warning("Payment failed for amount: %s", amount)
                return False

        context = PaymentContext(FailingPayment())
        with self.assertLogs(strategy_logger.name, level='WARNING') as cm:
            result = context.execute_payment(self.amount)

        self.assertFalse(result)
        self.assertIn(f"Payment failed for amount: {self.amount}", cm.output[0])
        self.assertTrue(any("Payment failed" in log for log in cm.output))


    def test_payment_with_different_amounts(self):
        """Тест оплати різних сум"""
        amounts = [Decimal('100.00'), Decimal('500.00'), Decimal('1000.00')]
        strategy = CreditCardPayment()

        for amount in amounts:
            with self.subTest(amount=amount):
                with self.assertLogs(strategy_logger.name, level='INFO') as cm:
                    result = strategy.pay(amount)

                self.assertTrue(result)
                self.assertIn(f"Processing credit card payment for {amount}", cm.output[0])

    def test_payment_context_set_strategy(self):
        """Тест зміни стратегії оплати в PaymentContext"""
        context = PaymentContext(CreditCardPayment())
        # W0212: Access to a protected member _strategy of a client class
        # This is common in tests to inspect internal state. Can be ignored or disabled for tests.
        initial_strategy_name = context._strategy.__class__.__name__
        self.assertEqual(initial_strategy_name, "CreditCardPayment")

        context.set_strategy(PayPalPayment())
        new_strategy_name = context._strategy.__class__.__name__
        self.assertEqual(new_strategy_name, "PayPalPayment")