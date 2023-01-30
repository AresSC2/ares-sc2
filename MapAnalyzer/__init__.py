# flake8: noqa
from .MapData import MapData
from .Polygon import Polygon
from .Region import Region
from .constructs import ChokeArea, MDRamp, VisionBlockerArea
from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution("sc2mapanalyzer")
except DistributionNotFound:
    __version__ = "dev"
