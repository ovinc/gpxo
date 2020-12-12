"""General tools for gpx data processing based on gpxpy."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import gpxpy
from vincenty import vincenty
import mplleaflet

from numbo import smooth


# Function to transform array of timedeltas to seoncds
_total_seconds = np.vectorize(lambda dt: dt.total_seconds())


def closest_pt(pt, trajectory):
    """Finds closest pt to pt (xpt, ypt) in trajectory (xs, ys)"""
    xs, ys = trajectory
    xpt, ypt = pt
    ds = [vincenty((x, y), (xpt, ypt)) for (x, y) in zip(xs, ys)]
    return np.argmin(ds)


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

    @property
    def seconds(self):
        return _total_seconds(self.time - self.time[0])

    @property
    def distance(self, method='vincenty'):
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
    def velocity(self):
        """Instantaneous velocity in km/h."""

        # derivative of distance vs time
        dt = np.diff(self.seconds)
        dd = np.diff(self.distance)
        vs = 3600 * dd / dt

        # corresponding times (midpoints)
        ts = self.seconds[:-1] + np.diff(self.seconds)

        # linear interpolation to fall back to initial times
        v = np.interp(self.seconds, ts, vs)

        return v

    @property
    def data(self):
        """pd.DataFrame with all track data (time, position, velocity etc.)"""
        column_names = ['time', 'seconds', 'latitude', 'longitude', 'distance', 'velocity']
        columns = zip(self.time, self.seconds, self.latitude, self.longitude, self.distance, self.velocity)
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
