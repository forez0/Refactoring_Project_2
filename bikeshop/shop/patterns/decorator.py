# shop/patterns/decorator.py
from functools import wraps
from decimal import Decimal # Ensure Decimal is imported for proper calculations
from django.contrib import messages
from django.http import JsonResponse
import logging
# Assuming Order model is accessible via request.user.order_set
# If Order is in ..models, you might also need to import it explicitly for clarity
# from ..models import Order

logger = logging.getLogger(__name__)

def apply_discount(percent):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                logger.debug("User is authenticated.")

                order = request.user.order_set.filter(completed=False).last()
                logger.debug(f"Found order: {order}")

                if order and order.total and not order.discount_percent:
                    try:
                        discount_amount = order.total * Decimal(str(percent)) / Decimal('100')
                        order.discount = discount_amount
                        order.discount_percent = percent
                        order.total -= discount_amount
                        logger.debug(f"Applied order discount: {discount_amount}")

                        for item in order.items.all():
                            item_discount = item.get_total() * Decimal(str(percent)) / Decimal('100')
                            item.discount = item_discount
                            item.save()
                            logger.debug(f"Item {item.id} discount: {item_discount}")

                        order.save()
                        messages.info(request, f"Було автоматично застосовано знижку {percent}% (-{discount_amount} грн)")
                        logger.info(f"Discount {percent}% applied to order #{order.id} for user {request.user.id}")
                    except Exception as e:
                        logger.error(f"Error applying discount: {e}", exc_info=True)
                        messages.error(request, "Помилка при застосуванні знижки.")
                else:
                    logger.debug("Discount conditions not met.")
                    if not order:
                        logger.debug(f"No active order found for user {request.user.id} to apply discount.")
                    elif not order.total:
                        logger.debug(f"Order #{order.id} has no total.")
                    elif order.discount_percent:
                        logger.debug(f"Order #{order.id} already has discount.")
            else:
                logger.debug("Unauthenticated user.")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator



def login_required_ajax(view_func):
    """
    Декоратор для захисту AJAX-запитів від неавторизованих користувачів.
    Якщо користувач не увійшов — повертає JSON з помилкою.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning(f"Anonymous user attempted to access {view_func.__name__} (AJAX protected).")
            return JsonResponse({'error': 'Authentication required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper