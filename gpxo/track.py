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

try:
    import folium
except ModuleNotFoundError:
    folium_installed = False
else:
    folium_installed = True

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

    def __init__(self, filename, track=0, segment=0, raw=False):
        """Init Track object

        Parameters
        ----------
        filename : str or pathlib.Path
            GPX file to load

        track : int, optional
            track to consider if the gpx file contains several tracks

        segment : int, optional
            segment to consider if the gpx file contains several segments

        raw : bool
            if True, keep only data present in the gpx file
            (longitude, latitude, elevation, time etc.)
            if False (default), calculate extra quantities
            (velocity, compass, etc.)
        """
        self.file = Path(filename)
        self.track = track
        self.segment = segment
        self.raw = raw

        pts = self._load_points()
        self.data = self._create_dataframe(pts)
        if not raw:
            self._expand_dataframe()

    # ----------------------------- Init methods -----------------------------

    def __repr__(self):
        return (
            f"gpxo.Track {self.file.name}, track {self.track}, "
            f"segment {self.segment}"
        )

    def _load_points(self):
        """Load individual points using gpxpy"""

        if not self.file.exists():
            raise FileNotFoundError(f'{self.file} does not exist')

        with open(self.file, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        return gpx.tracks[self.track].segments[self.segment].points

    # --------------- Dataframe creation and expansion methods ---------------

    def _create_dataframe(self, pts):
        """Make pandas dataframe from points spit out by gpxpy"""

        df = pd.DataFrame()

        df['latitude (°)'] = [pt.latitude for pt in pts]
        df['longitude (°)'] = [pt.longitude for pt in pts]

        times = ([pt.time for pt in pts])
        if any(times):
            df['time'] = np.array(times).astype('datetime64')
            self._time_data_present = True
        else:
            self._time_data_present = False

        elevations = [pt.elevation for pt in pts]
        if any(elevations):
            df['elevation (m)'] = elevations
            self._elevation_data_present = True
        else:
            self._elevation_data_present = False

        return df

    def _expand_dataframe(self):
        """pd.DataFrame with all track data (time, position, velocity etc.)"""
        self.data['distance (km)'] = self._calculate_distance()
        self.data['compass (°)'] = self._calculate_compass()
        if self._time_data_present:
            self.data['duration (s)'] = self._calculate_seconds()
            self.data['velocity (km/h)'] = self._calculate_velocity()

    # ---------------- Methods to calculate extra quantities -----------------

    def _calculate_seconds(self):
        """Elapsed time in seconds"""
        return (self.data['time'] - self.data['time'].iloc[0]).dt.total_seconds()

    def _calculate_distance(self):
        """Travelled distance in kilometers."""
        latitude = self.data['latitude (°)'].values
        longitude = self.data['longitude (°)'].values

        ds = [0]

        lat_1s = latitude[:-1]
        lat_2s = latitude[1:]

        long_1s = longitude[:-1]
        long_2s = longitude[1:]

        for lat_1, lat_2, long_1, long_2 in zip(lat_1s, lat_2s, long_1s, long_2s):
            dd = vincenty((lat_1, long_1), (lat_2, long_2))
            ds.append(dd)

        return np.cumsum(ds)

    def _calculate_velocity(self):
        """Instantaneous velocity in km/h."""
        dd = self.data['distance (km)'].diff()
        dt = self.data['duration (s)'].diff() / 3600
        return dd / dt

    def _calculate_compass(self):
        """Compass bearing in decimal degrees (°). See gpxo.compass"""
        latitude = self.data['latitude (°)'].values
        longitude = self.data['longitude (°)'].values

        pts1 = np.radians((latitude[:-1], longitude[:-1]))
        pts2 = np.radians((latitude[1:], longitude[1:]))

        bearing = compass(pts1, pts2)

        # Put np.nan at beginning similar to velocity
        return np.insert(bearing, 0, np.nan)

    # --------------------------- Plotting methods ---------------------------

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

    def plot(self, mode, *args, ax=None, **kwargs):
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

    # ------------------------- Misc. public methods -------------------------

    def smooth(self, n=5, window='hamming'):
        """Smooth position data (and subsequently distance, velocity etc.)

        Parameters
        ----------
        n : int
            size of moving window for smoothing

        window : str
            type of window (e.g. 'hanning' or 'flat', see gpxo.smooth())

        **kwargs
            any keyword arguments to pass to pandas.DataFrame.rolling().mean()
        """
        # Only smooth raw data
        names = 'latitude (°)', 'longitude (°)'
        if self._elevation_data_present:
            names += 'elevation (m)',

        for name in names:
            old_vals = self.data[name].values
            self.data[name] = smooth(old_vals, n=n, window=window)

        # Then recalculate others
        self._expand_dataframe()

    def closest_to(self, pt):
        """Find index of point in trajectory that is closest to pt=(lat, long)."""
        return closest_pt(pt, (self.data['latitude (°)'], self.data['longitude (°)']))

    # ----------------------------- Mapping tools ----------------------------

    def folium_map(self, color='red', alpha=0.7, **kwargs):
        """Make map using folium

        **kwargs
            - zoom_start : int
                starting zoom level, 14 is typically good for a city

            - tiles : str
                e.g. "OpenStreetMap", "OpenTopoMap", "CartoDB Positron",
                "CartoDB Voyager" et.
        """
        mean_lat = self.data['latitude (°)'].mean()
        mean_long = self.data['longitude (°)'].mean()
        mymap = folium.Map(location=[mean_lat, mean_long], **kwargs)  # tiles='OpenTopoMap',

        pts = zip(self.data['latitude (°)'], self.data['longitude (°)'])
        line = folium.PolyLine(pts, color=color, alpha=alpha)
        line.add_to(mymap)

        return mymap

    def mplleaflet_map(
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

        latitude = self.data['latitude (°)'].values
        longitude = self.data['longitude (°)'].values

        if plot == 'plot':
            ax.plot(longitude, latitude, '.-r', **kwargs)
        elif plot == 'scatter':
            ax.scatter(longitude, latitude, **kwargs)
        else:
            raise ValueError(f'Unrecognized plot type: {plot}')

        parameters = {'fig': fig, 'tiles': map_type}
        if embed:
            leaflet = mplleaflet.display(**parameters)
        else:
            leaflet = mplleaflet.show(**parameters)

        return leaflet
