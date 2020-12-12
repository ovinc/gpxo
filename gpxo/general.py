"""General tools for gpx data processing based on gpxpy."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import gpxpy
from vincenty import vincenty
import mplleaflet

from numbo import smooth


# ========================= Misc. private functions ==========================


# Function to transform array of timedeltas to seoncds
_total_seconds = np.vectorize(lambda dt: dt.total_seconds())


# ============================= Public functions =============================


def closest_pt(pt, trajectory):
    """Finds closest pt to pt (xpt, ypt) in trajectory (xs, ys)"""
    xs, ys = trajectory
    xpt, ypt = pt
    ds = [vincenty((x, y), (xpt, ypt)) for (x, y) in zip(xs, ys)]
    return np.argmin(ds)


def compass(pt1, pt2):
    """
    Calculate the compass bearing between two points.

    Adapted from https://gist.github.com/jeromer/2005586 (public domain) for
    use with numpy arrays.

    The formula used is the following:
        θ = arctan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

    Parameters
    ----------
    pt1, pt2: positions (latitude/longitude in °) of first/second point

    Each pt in (pt1, pt2) can be:
    - a tuple (lat, long) where lat/long are floats or iterables of floats
      (e.g. tuples, lists, arrays)
    - a (2 * N) numpy array where 2 corresponds to (lat, long) and N the number
      of successive points to calculate.
    - any structure equivalent to the structures above in terms of unpacking.

    Output
    ------
    Compass bearing in decimal degrees (°)

    Examples
    --------

    With individual points ---------------------------------------------------

    >>> compass((0, 0), (45, 0))
    0.0

    >>> compass((45, 0), (0, 0))
    180.0

    >>> compass((0, 0), (0, 30))
    90.0

    >>> compass((0, 30), (0, -30))
    270.0

    With multiple points -----------------------------------------------------

    >>> lat1 = (0, 45, 0, 0)

    >>> long1 = (0, 0, 0, 30)

    >>> lat2 = (45, 0, 0, 0)

    >>> long2 = (0, 0, 30, -30)

    >>> pt1 = (lat1, long1)

    >>> pt2 = (lat2, long2)

    >>> compass(pt1, pt2)
    array([  0., 180.,  90., 270.])
    """
    lat1, long1 = np.radians(pt1)
    lat2, long2 = np.radians(pt2)

    d_long = long2 - long1

    x = np.sin(d_long) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(d_long))

    initial_bearing = np.arctan2(x, y)

    # Now we have the initial bearing but np.arctan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = np.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


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

    def _distance(self, position1, position2):
        """Distance between two positions (latitude, longitude)."""
        return vincenty(position1, position2)

    def _resample(self, quantity):
        """Resample quantities (velocity, compass) to fall back on times."""
        # corresponding times (midpoints)
        ts = self.seconds[:-1] + (np.diff(self.seconds) / 2)
        # linear interpolation to fall back to initial times
        qty_resampled = np.interp(self.seconds, ts, quantity)
        return qty_resampled

    @property
    def seconds(self):
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
        """Compass bearing in decimal degrees (°)."""
        lat1, long1 = np.radians((self.latitude[:-1], self.longitude[:-1]))
        lat2, long2 = np.radians((self.latitude[1:], self.longitude[1:]))

        d_long = long2 - long1

        x = np.sin(d_long) * np.cos(lat2)
        y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(d_long))

        # Resample before taking arctan because if not, interpolation fails
        # when the signal fluctuates between 0 and 360° when compass is N
        x_res = self._resample(x)
        y_res = self._resample(y)

        initial_bearing = np.arctan2(x_res, y_res)

        # Now we have the initial bearing but np.arctan2 return values
        # from -180° to + 180° which is not what we want for a compass bearing
        # The solution is to normalize the initial bearing as shown below
        initial_bearing = np.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360

        return compass_bearing


    @property
    def velocity(self):
        """Instantaneous velocity in km/h."""
        dt = np.diff(self.seconds)
        dd = np.diff(self.distance)
        vs = 3600 * dd / dt
        return self._resample(vs)

    @property
    def data(self):
        """pd.DataFrame with all track data (time, position, velocity etc.)"""
        column_names = ['time', 'seconds', 'latitude', 'longitude',
                        'distance', 'velocity', 'compass']
        columns = zip(self.time, self.seconds, self.latitude, self.longitude,
                      self.distance, self.velocity, self.compass)
        data = pd.DataFrame(columns, columns=column_names)
        data['time'] = data['time'].dt.tz_localize(None)
        data.set_index('time', inplace=True)
        return data

    def plot(self, *args, **kwargs):
        """Plot columns of self.data (use pandas DataFrame plot arguments)."""
        return self.data.plot(*args, **kwargs)

    def smooth(self, *args, **kwargs):
        """Smooth position data (and subsequently distance, velocity etc.)

        Parameters
        ----------
        args and kwargs correspond to numbo.smooth() arguments (length of
        window, window type, etc.)
        """
        self.latitude = smooth(self.latitude, *args, **kwargs)
        self.longitude = smooth(self.longitude, *args, **kwargs)

    def map(self, map_type='osm', embed=False, size=(10, 10)):
        """Plot trajectory on map.

        Parameters
        ----------
        - map_type can be e.g. osm, esri_aerial, esri_worldtopo, etc. see:
        https://github.com/jwass/mplleaflet/blob/master/mplleaflet/maptiles.py

        - embed: if True, embed plot in Jupyter. If False (default), open in
        browser.

        - size: when embedded, size of the figure.
        """
        fig, ax = plt.subplots(figsize=size)
        ax.plot(self.longitude, self.latitude, '.-r')
        parameters = {'fig': fig, 'tiles': map_type}
        if embed:
            leaflet = mplleaflet.display(**parameters)
        else:
            leaflet = mplleaflet.show(**parameters)

        return leaflet
