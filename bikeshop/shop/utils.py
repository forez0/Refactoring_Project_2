from django.core.mail import send_mail
from django.conf import settings
from .models import Order  # Імпортуй модель Order для типізації


def send_order_confirmation(order: Order) -> None:
    subject = f'Підтвердження замовлення #{order.id}'
    message = (
        f'Дякуємо за ваше замовлення #{order.id}!\n\n'
        f'Сума: {order.total} грн\n'
        f'Дата: {order.created_at.strftime("%d.%m.%Y %H:%M")}\n\n'
        'Ми зв\'яжемося з вами для уточнення деталей.'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        fail_silently=False,
    )
