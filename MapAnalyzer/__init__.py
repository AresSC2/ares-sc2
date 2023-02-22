# flake8: noqa
from pkg_resources import DistributionNotFound, get_distribution

from .constructs import ChokeArea, MDRamp, VisionBlockerArea
from .MapData import MapData
from .Polygon import Polygon
from .Region import Region

try:
    __version__ = get_distribution("sc2mapanalyzer")
except DistributionNotFound:
    __version__ = "dev"
