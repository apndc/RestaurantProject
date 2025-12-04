from sqlalchemy.orm import declarative_base

Base = declarative_base()

# import all tables (models) so they get registered with Base.metadata
from .Account import Account
from .CardInfo import CardInfo
from .Events import Events
from .Location import Location
from .Reservation import Reservation
from .RestaurantInfo import RestaurantInfo
from .Menu import Menu
from .EP_Verification import EP_Verification
from .RO_Verification import RO_Verification
from .EP_Reservation import EP_Reservation

# make tables (models) available when importing from schema package
__all__ = ['Account', 'CardInfo', 'Events', 'Location', 'Reservation', 'RestaurantInfo', 'Menu', 'EP_Verification', 'RO_Verification', 'EP_Reservation']