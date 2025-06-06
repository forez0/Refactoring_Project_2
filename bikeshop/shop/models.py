from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

"""
Моделі додатку shop: велосипеди, їх специфікації та замовлення.
"""

# ===== ВЕЛОСИПЕДИ =====

class BikeType(models.Model):
    """Тип велосипеда, наприклад: гірський, шосейний, міський."""
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self) -> str:
        return self.name


class Bike(models.Model):
    """Модель велосипеда з основними параметрами."""
    name = models.CharField(max_length=100)
    bike_type = models.ForeignKey(BikeType, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='bikes/')
    in_stock = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.bike_type.name})"

    def get_specifics(self) -> str:
        """Повертає специфіку велосипеда залежно від типу."""
        if hasattr(self, 'mountain_spec'):
            return self.mountain_spec.get_specifics()
        if hasattr(self, 'road_spec'):
            return self.road_spec.get_specifics()
        if hasattr(self, 'city_spec'):
            return self.city_spec.get_specifics()
        return "Звичайний велосипед"


class MountainBikeSpec(models.Model):
    """Специфікації для гірського велосипеда."""
    bike = models.OneToOneField(Bike, on_delete=models.CASCADE, related_name='mountain_spec')
    suspension = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"Гірський ({self.bike.name})"

    def get_specifics(self) -> str:
        return f"Гірський велосипед з {self.suspension} амортизацією"


class RoadBikeSpec(models.Model):
    """Специфікації для шосейного велосипеда."""
    bike = models.OneToOneField(Bike, on_delete=models.CASCADE, related_name='road_spec')
    weight = models.FloatField()

    def __str__(self) -> str:
        return f"Шосейний ({self.bike.name})"

    def get_specifics(self) -> str:
        return f"Легкий шосейний велосипед ({self.weight} кг)"


class CityBikeSpec(models.Model):
    """Специфікації для міського велосипеда."""
    bike = models.OneToOneField(Bike, on_delete=models.CASCADE, related_name='city_spec')
    has_basket = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Міський ({self.bike.name})"

    def get_specifics(self) -> str:
        basket_text = " з кошиком" if self.has_basket else ""
        return "Міський велосипед" + basket_text


# ===== ЗАМОВЛЕННЯ =====

class Order(models.Model):
    """Модель замовлення велосипеда користувачем."""
    STATUS_CHOICES = [
        ('new', 'Нове'),
        ('processing', 'В обробці'),
        ('shipped', 'Відправлено'),
        ('delivered', 'Доставлено'),
        ('canceled', 'Скасовано'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.PositiveIntegerField(default=0)
    success_handled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Замовлення #{self.pk} ({self.user.username})"

    def get_status_display(self) -> str:
        """Повертає текстове представлення статусу замовлення."""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def total_before_discount(self) -> Decimal:
        """Обчислює суму замовлення до застосування знижки."""
        return sum(item.quantity * item.price for item in self.items.all())

    def calculate_total(self) -> None:
        """
        Оновлює поля total і discount, розподіляючи знижку по позиціях замовлення.
        """
        total_before = self.total_before_discount
        discount_amount = total_before * Decimal(self.discount_percent) / Decimal(100)

        # Пропорційно розподілити discount по items
        for item in self.items.all():
            item_share = (item.quantity * item.price) / total_before if total_before else 0
            item_discount = discount_amount * item_share
            item.discount = item_discount
            item.save()

        self.discount = discount_amount
        self.total = total_before - discount_amount
        self.save()


class OrderItem(models.Model):
    """Позиція (рядок) у замовленні."""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.bike.name}"

    def get_total(self) -> Decimal:
        """Обчислює суму позиції з урахуванням знижки."""
        return self.quantity * self.price - self.discount
