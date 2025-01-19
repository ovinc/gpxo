"""General tools for gpx data processing based on gpxpy."""

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
}


# ========================= Misc. private functions ==========================


# Function to transform array of timedeltas to seoncds
_total_seconds = np.vectorize(lambda dt: dt.total_seconds())


# ============================ Main class (Track) ============================

class Track:

    def __init__(self, filename, track=0, segment=0):

        with open(filename, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        pts = gpx.tracks[track].segments[segment].points

        self.latitude = np.array([pt.latitude for pt in pts])
        self.longitude = np.array([pt.longitude for pt in pts])
        self.elevation = np.array([pt.elevation for pt in pts])
        self.time = np.array([pt.time for pt in pts])

        # If some elevation or time data is missing, just set attribute to None

        if any(self.time == None):
            self.time = None

        if any(self.elevation == None):
            self.elevation = None

    @staticmethod
    def _distance(position1, position2):
        """Distance between two positions (latitude, longitude)."""
        return vincenty(position1, position2)

    def _resample(self, quantity, reference, period=None):
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
            return _total_seconds(self.time - self.time[0])

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
        return self._resample(bearing, reference=self.seconds, period=360)

    @property
    def velocity(self):
        """Instantaneous velocity in km/h."""
        if self.time is None:
            return
        dt = np.diff(self.seconds)
        dd = np.diff(self.distance)
        vs = 3600 * dd / dt
        return self._resample(vs, reference=self.seconds)

    @property
    def data(self):
        """pd.DataFrame with all track data (time, position, velocity etc.)"""

        names = ['latitude (°)', 'longitude (°)', 'distance (km)', 'compass (°)']
        columns = [self.latitude, self.longitude, self.distance, self.compass]

        if self.time is not None:
            names += ['time', 'duration (s)', 'velocity (km/h)']
            columns += [self.time, self.seconds, self.velocity]

        if self.elevation is not None:
            names.append('elevation (m)')
            columns.append(self.elevation)

        data = pd.DataFrame(dict(zip(names, columns)))

        if self.time is not None:
            data['time'] = data['time'].dt.tz_localize(None)
            data.set_index('time', inplace=True)

        return data

    def _shortname_to_column(self, name):
        """shorname to column name in self.data."""
        try:
            cname = SHORTNAMES[name]
        except KeyError:
            raise ValueError(f'Invalid short name: {name}. ')

        if cname == 'time':
            column = self.data.index
        else:
            try:
                column = self.data[cname]
            except KeyError:
                raise KeyError(f'{cname} Data unavailable in current track. ')

        return {'name': cname, 'column': column}

    def plot(self, mode, *args, **kwargs):
        """Plot columns of self.data (use pandas DataFrame plot arguments).

        Parameters
        ----------
        - mode (str): 2 letters that define short names for x and y axis
        - *args: any additional argument for matplotlib ax.plot()
        - **kwargs: any additional keyword argument for matplotlib ax.plot()

        Output
        ------
        - matplotlib axes

        Short names
        -----------
        't': 'time'
        's': 'duration (s)'
        'd': 'distance (km)'
        'v': 'velocity (km/h)'
        'z': 'elevation (m)'
        'c': 'compass (°)'
        """
        try:
            xname, yname = mode
        except ValueError:
            raise ValueError('Invalid plot mode (should be two letters, e.g. '
                             f"'tv', not {mode}")

        xinfo = self._shortname_to_column(xname)
        xlabel = xinfo['name']
        x = xinfo['column']

        yinfo = self._shortname_to_column(yname)
        ylabel = yinfo['name']
        y = yinfo['column']

        fig, ax = plt.subplots()
        ax.plot(x, y, *args, **kwargs)

        if xlabel == 'time':
            fig.autofmt_xdate()

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        return ax

    def smooth(self, n=5, window='hanning'):
        """Smooth position data (and subsequently distance, velocity etc.)

        Parameters
        ----------
        - n: size of moving window for smoothing
        - window: type of window (e.g. 'hanning' or 'flat', see gpxo.smooth())
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
