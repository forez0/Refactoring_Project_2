"""Адміністративна конфігурація для моделей магазину велосипедів."""

from django.contrib import admin
from .models import BikeType, Bike, MountainBikeSpec, RoadBikeSpec, CityBikeSpec

admin.site.register(BikeType)
admin.site.register(Bike)
admin.site.register(MountainBikeSpec)
admin.site.register(RoadBikeSpec)
admin.site.register(CityBikeSpec)
