"""General tools for gpx data processing based on gpxpy."""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import gpxpy
from vincenty import vincenty

try:
    import mplleaflet
except ModuleNotFoundError:
    mplleaflet_installed = False
else:
    mplleaflet_installed = True

from .general import smooth, closest_pt, compass


# =============================== Misc. Config ===============================

# short names for plots

SHORTNAMES = {
    't': 'time',
    's': 'duration (s)',
    'd': 'distance (km)',
    'v': 'velocity (km/h)',
    'z': 'elevation (m)',
    'c': 'compass (°)',
    'x': 'longitude (°)',
    'y': 'latitude (°)',
}


# ============================ Main class (Track) ============================

class Track:
    """Representation of GPX track data"""

    def __init__(self, filename, track=0, segment=0):
        """Init Track object

        Parameters
        ----------
        filename : str or pathlib.Path
            GPX file to load

        track : int, optional
            track to consider if the gpx file contains several tracks

        segment : int, optional
            segment to consider if the gpx file contains several segments
        """
        self.file = Path(filename)
        self.track = track
        self.segment = segment

        if not self.file.exists():
            raise FileNotFoundError(f'{self.file} does not exist')

        with open(self.file, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        pts = gpx.tracks[track].segments[segment].points

        # Missing data will be converted to np.nan with the dtype=float option
        self.latitude = np.array([pt.latitude for pt in pts], dtype=float)
        self.longitude = np.array([pt.longitude for pt in pts], dtype=float)
        self.elevation = np.array([pt.elevation for pt in pts], dtype=float)

        # If no time data (all elements in time will be None), self.time = None
        time = np.array([pt.time for pt in pts])
        self.time = None if not any(time) else time.astype('datetime64')

    def __repr__(self):
        return (
            f"gpxo.Track {self.file.name}, track {self.track}, "
            f"segment {self.segment}"
        )

    @staticmethod
    def _distance(position1, position2):
        """Distance between two positions (latitude, longitude)."""
        return vincenty(position1, position2)

    @staticmethod
    def _resample(quantity, reference, period=None):
        """Resample derived quantities (velocity, compass) to time or distance."""
        # midpoints correponding to derived quantity (e.g. velocity)
        midpts = reference[:-1] + (np.diff(reference) / 2)
        raw_data = (midpts, quantity)

        # linear interpolation to fall back to initial times
        qty_resampled = np.interp(reference, *raw_data, period=period)

        return qty_resampled

    @property
    def seconds(self):
        if self.time is not None:
            # microseconds timedelta to floats
            return ((self.time - self.time[0]) / 1e6).astype(float)

    @property
    def distance(self):
        """Travelled distance in kilometers."""

        ds = [0]

        x1s = self.latitude[:-1]
        x2s = self.latitude[1:]

        y1s = self.longitude[:-1]
        y2s = self.longitude[1:]

        for x1, x2, y1, y2 in zip(x1s, x2s, y1s, y2s):
            dd = self._distance((x1, y1), (x2, y2))
            ds.append(dd)

        return np.cumsum(ds)

    @property
    def compass(self):
        """Compass bearing in decimal degrees (°). See gpxo.compass"""
        pts1 = np.radians((self.latitude[:-1], self.longitude[:-1]))
        pts2 = np.radians((self.latitude[1:], self.longitude[1:]))
        bearing = compass(pts1, pts2)
        reference = self.distance if self.seconds is None else self.seconds
        return self._resample(bearing, reference=reference, period=360)

    @property
    def velocity(self):
        """Instantaneous velocity in km/h."""
        if self.time is None:
            return
        dt = np.diff(self.seconds)
        dd = np.diff(self.distance)
        vs = 3600 * dd / dt
        reference = self.distance if self.seconds is None else self.seconds
        return self._resample(vs, reference=reference)

    @property
    def data(self):
        """pd.DataFrame with all track data (time, position, velocity etc.)"""

        names = [
            'latitude (°)',
            'longitude (°)',
            'distance (km)',
            'compass (°)',
            'elevation (m)'
        ]
        columns = [
            self.latitude,
            self.longitude,
            self.distance,
            self.compass,
            self.elevation,
        ]

        if self.time is not None:
            names += ['time', 'duration (s)', 'velocity (km/h)']
            columns += [self.time, self.seconds, self.velocity]

        data = pd.DataFrame(dict(zip(names, columns)))

        return data

    def _get_column_names(self, mode):
        """mode to column names in self.data."""
        try:
            xname, yname = mode
        except ValueError:
            raise ValueError(
                'Invalid plot mode (should be two letters, e.g. '
                f"'tv', not {mode}"
            )

        column_names = []

        for name in xname, yname:

            try:
                column_name = SHORTNAMES[name]
            except KeyError:
                raise ValueError(f'Invalid short name: {name}. ')
            else:
                column_names.append(column_name)

            try:
                self.data[column_name]
            except KeyError:
                raise KeyError(f'{column_name} Data unavailable in current track. ')

        return column_names

    def plot(self, mode, ax=None, *args, **kwargs):
        """Plot columns of self.data (use pandas DataFrame plot arguments).

        Parameters
        ----------
        mode : str
            2 letters that define short names for x and y axis, e.g. 'tv'

        ax : matplotlib.Axes or None, optional
            axes in which to plot the graph

        *args: any additional argument for matplotlib ax.plot()
        **kwargs: any additional keyword argument for matplotlib ax.plot()

        Returns
        -------
        matplotlib.Axes

        Short names
        -----------
        't': 'time'
        's': 'duration (s)'
        'd': 'distance (km)'
        'v': 'velocity (km/h)'
        'z': 'elevation (m)'
        'c': 'compass (°)'
        """
        xcol, ycol = self._get_column_names(mode)

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        ax.plot(self.data[xcol], self.data[ycol], *args, **kwargs)

        if xcol == 'time':
            fig.autofmt_xdate()

        ax.set_xlabel(xcol)
        ax.set_ylabel(ycol)

        return ax

    def smooth(self, n=5, window='hanning'):
        """Smooth position data (and subsequently distance, velocity etc.)

        Parameters
        ----------
        n : int
            size of moving window for smoothing

        window : str
            type of window (e.g. 'hanning' or 'flat', see gpxo.smooth())
        """
        self.latitude = smooth(self.latitude, n=n, window=window)
        self.longitude = smooth(self.longitude, n=n, window=window)
        self.elevation = smooth(self.elevation, n=n, window=window)

    def closest_to(self, pt):
        """Find index of point in trajectory that is closest to pt=(lat, long)."""
        return closest_pt(pt, (self.latitude, self.longitude))

    def map(
        self,
        map_type='osm',
        embed=False,
        ax=None,
        size=(10, 10),
        plot='plot',
        **kwargs,
    ):
        """Plot trajectory on map.

        Parameters
        ----------
        - map_type can be e.g. osm, esri_aerial, esri_worldtopo, etc. see:
        https://github.com/jwass/mplleaflet/blob/master/mplleaflet/maptiles.py

        - embed: if True, embed plot in Jupyter. If False (default), open in
        browser.

        - ax: if not None, use provided matplotlib axes.

        - size: when embedded, size of the figure.

        - plot: 'plot' or 'scatter'

        - **kwargs: any plt.plot or plt.scatter keyword arguments
        """
        if not mplleaflet_installed:
            raise ValueError('Map unavailable beacuse mplleaflet not installed.')

        if ax is None:
            fig, ax = plt.subplots(figsize=size)
        else:
            fig = ax.figure

        if plot == 'plot':
            ax.plot(self.longitude, self.latitude, '.-r', **kwargs)
        elif plot == 'scatter':
            ax.scatter(self.longitude, self.latitude, **kwargs)
        else:
            raise ValueError(f'Unrecognized plot type: {plot}')

        parameters = {'fig': fig, 'tiles': map_type}
        if embed:
            leaflet = mplleaflet.display(**parameters)
        else:
            leaflet = mplleaflet.show(**parameters)

        return leaflet
