"""Init file for gpxo module."""

from .general import closest_pt, compass, smooth
from .track import Track

from importlib.metadata import version

__version__ = version('gpxo')
