# import all tables (models) so they get registered with Base.metadata
from .Account import Account
from .CardInfo import CardInfo
from .Events import Events
from .Location import Location
from .Reservation import Reservation
from .RestaurantInfo import RestaurantInfo
from .Menu import Menu

# make tables (models) available when importing from schema package
__all__ = ['Account', 'CardInfo', 'Events', 'Location', 'Reservation', 'RestaurantInfo', 'Menu']