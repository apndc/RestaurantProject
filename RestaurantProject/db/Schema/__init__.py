# import all tables (models) so they get registered with Base.metadata
from .Location import Location
from .RestaurantInfo import RestaurantInfo
# make tables (models) available when importing from schema package
__all__ = ['Location', 'RestaurantInfo']