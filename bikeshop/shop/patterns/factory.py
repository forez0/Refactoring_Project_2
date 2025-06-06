# shop/patterns/factory.py
import logging
from decimal import Decimal
from ..models import Bike, BikeType, MountainBikeSpec, RoadBikeSpec, CityBikeSpec

logger = logging.getLogger(__name__)

class BikeFactory:
    """Фабрика для створення велосипедів різного типу"""

    def create_bike(self, bike_type_name: str, name: str, price: Decimal, description: str, image=None,
                    **kwargs) -> Bike:
        bike_type, created = BikeType.objects.get_or_create(name=bike_type_name)
        if created:
            logger.info(f"New BikeType '{bike_type_name}' created.")

        bike = Bike.objects.create(
            name=name,
            bike_type=bike_type,
            price=price,
            description=description,
            image=image,
        )

        bike_type_lower = bike_type_name.lower()

        if bike_type_lower == "mountain":
            suspension = kwargs.get("suspension", "пружинна")
            MountainBikeSpec.objects.create(bike=bike, suspension=suspension)
            logger.info(f"Mountain bike '{name}' created with suspension: {suspension}")

        elif bike_type_lower == "road":
            weight = kwargs.get("weight", 7.5)
            RoadBikeSpec.objects.create(bike=bike, weight=weight)
            logger.info(f"Road bike '{name}' created with weight: {weight}kg")

        elif bike_type_lower == "city":
            has_basket = kwargs.get("has_basket", False)
            CityBikeSpec.objects.create(bike=bike, has_basket=has_basket)
            logger.info(f"City bike '{name}' created with basket: {has_basket}")

        # Якщо тип не входить до відомих — обов’язково логуй
        if bike_type_lower not in ["mountain", "road", "city"]:
            logger.info(
                f"Bike '{name}' created with unknown specific type '{bike_type_name}'. Creating a generic bike (no specific spec applied).")

        return bike
