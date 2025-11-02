"""Init file for gpxo module."""

from .general import closest_pt, compass
from .track import Track

# from importlib.metadata import version  # only for python 3.8+
from importlib_metadata import version

__version__ = version('gpxo')
__author__ = 'Olivier Vincent'
__license__ = '3-Clause BSD'
