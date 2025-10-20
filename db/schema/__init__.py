# import all tables (models) so they get registered with Base.metadata
from .account import Account
from .cardinfo import CardInfo
from .events import Events
from .locaction import Locaction
from .reservation import Reservation
from .restuarant import Restuarant

# make tables (models) available when importing from schema package
__all__ = ['Account', 'CardInfo', 'Events', 'Location', 'Reservation', 'Restuarant']