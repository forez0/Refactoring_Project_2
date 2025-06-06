from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from typing import Optional

from .models import Bike, BikeType, Order, OrderItem
from .forms import SignUpForm
from .patterns.strategy import PaymentContext, CreditCardPayment, PayPalPayment, CashOnDeliveryPayment
from .patterns.decorator import apply_discount


def home(request):
    return render(request, 'shop/home.html')


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрація успішна!')
            return redirect('shop:bike_list')
    else:
        form = SignUpForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def bike_list(request):
    bike_type_id = request.GET.get('type')
    bikes = Bike.objects.filter(in_stock=True)
    active_type: Optional[BikeType] = None

    if bike_type_id and bike_type_id != 'all':
        active_type = get_object_or_404(BikeType, pk=bike_type_id)
        bikes = bikes.filter(bike_type=active_type)

    bike_types = BikeType.objects.all()
    return render(request, 'shop/bike_list.html', {
        'bikes': bikes,
        'bike_types': bike_types,
        'active_type': active_type
    })


def get_payment_strategy(payment_method: str):
    if payment_method == 'paypal':
        return PayPalPayment()
    elif payment_method == 'cod':
        return CashOnDeliveryPayment()
    return CreditCardPayment()


@login_required
@transaction.atomic
@apply_discount(10)
def create_order(request, bike_id):
    bike = get_object_or_404(Bike, pk=bike_id)
    order = request.user.order_set.filter(completed=False).last()

    if not order:
        # Створюємо нове замовлення та одразу додаємо товар
        order = Order.objects.create(user=request.user, total=0)
        OrderItem.objects.create(order=order, bike=bike, quantity=1, price=bike.price)
    else:
        # Якщо товар ще не додано — додаємо
        item_exists = order.items.filter(bike=bike).exists()
        if not item_exists:
            OrderItem.objects.create(order=order, bike=bike, quantity=1, price=bike.price)

    # 🔧 Оновлюємо суму ДО виклику декоратора (він буде після return wrapper(...))
    order.total = sum(item.get_total() for item in order.items.all())
    order.save()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm_order':
            payment_method = request.POST.get('payment', 'credit')
            strategy = get_payment_strategy(payment_method)
            payment_context = PaymentContext(strategy)

            if payment_context.execute_payment(order.total):
                order.completed = True
                order.save()
                messages.success(request, 'Оплата пройшла успішно!')
                return redirect('shop:order_success', order.id)
            else:
                messages.error(request, 'Оплата не пройшла. Спробуйте пізніше.')

        return redirect('shop:create_order', bike_id=bike.id)

    return render(request, 'shop/create_order.html', {'bike': bike, 'order': order})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # Викликаємо функції лише якщо замовлення успішно створене, не повторно
    if not order.success_handled:
        send_order_confirmation_email(order)
        update_inventory(order)
        notify_admin(order)
        order.success_handled = True
        order.save()

    return render(request, 'shop/order_success.html', {'order': order})


def send_order_confirmation_email(order: Order) -> None:
    subject = f'Підтвердження замовлення #{order.id}'
    message = (
        f"Дякуємо за ваше замовлення!\n"
        f"Номер замовлення: {order.id}\n"
        f"Сума: {order.total:.2f} грн\n"
        f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        "Ми зв'яжемося з вами для уточнення деталей."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        fail_silently=False,
    )


def update_inventory(order: Order) -> None:
    for item in order.items.select_related('bike').all():
        bike = item.bike
        bike.in_stock = False
        bike.save()


def notify_admin(order: Order) -> None:
    # TODO: Додати логіку повідомлення адміну (email/telegram/slack)
    pass


@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/profile.html', {'orders': orders})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})
