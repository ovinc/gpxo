About
=====

Load GPS data from GPX files into Python as a *pandas* DataFrames.
Initial parsing done using the *gpxpy* package.
Trajectory plotting on a map available using *folium* or *mplleaflet* (optional).


Quick Start
===========

Install
-------

```bash
pip install gpxo
```

Load Track
----------

```python
import gpxo
track = gpxo.Track('ExampleTrack.gpx')
```
`track.data` is a *pandas* DataFrame containing time, position, elevation etc.; usual *pandas* methods can be used to analyze, manipulate and plot data.


Detailed Contents
=================

Track class
-----------

Load, inspect and plot GPX data using the `Track` class, with the following methods and attributes.

### Methods

- `smooth()`: smooth position and elevation data (see `gpxo.smooth()` below),
- `plot()`: plot trajectory data using a combination of shortnames (see shortnames below); also takes `matplotlib.pyplot.plot()` arguments/kwargs,
- `closest_to()`: find index of point in trajectory closest to a (lat, long) point.
- `folium_map()`: plot trajectory on a map, using the `folium` package,
- `mplleaflet_map()`: plot trajectory on a map, using `mplleaflet.show()`,

### Attributes

- `file`: `pathlib.Path` from which data originates
- `data` (pandas DataFrame): containing at least the keys `'latitude (°)'`, `'longitude (°)'`, and if available `'elevation (m)'`, `'time'`; by default, the table will also include `'distance (km)'`, `'compass (°)'`, `'duration (s)'`, `'velocity (km/h)'`, calculated if possible during instantiation.

## Miscellaneous

Outside of the `Track` class, the following standalone function is also available:
- `compass(pt1, pt2)`: compass bearing (°) between pt1 (lat1, long1) and pt2 (lat2, long2),
- `closest_pt(pt, trajectory)`: index of closest pt in trajectory (latitudes, longitudes) to specified pt (lat, long),
- `smooth(x, n, window)`: smooth 1-d array with a moving window of size n and type *window*.

## Short names

| Short name | Corresponding data
| :--------: | :----------------:
|     t      |  time
|     s      |  duration (s)
|     d      |  distance (km)
|     v      |  velocity (km/h)
|     z      |  elevation (m)
|     c      |  compass (°)
|     x      |  longitude (°)
|     y      |  latitude (°)

Examples
========

See Jupyter Notebook **Examples.ipynb** (https://github.com/ovinc/gpxo/blob/master/Examples.ipynb) for a detailed example using real GPX data.

**Quick example 1**: Plot distance versus time and velocity versus position for a given track:

```python
import gpxo
track = gpxo.Track('ExampleTrack.gpx')
track.plot('td', '--k')    # matplotlib styles can be given
track.plot('dv', c='red')  # matplotlib kwargs can be passed
track.data  # pandas dataframe with all data
```

**Quick example 2**: show the path of a GPX file on a map using the `folium` package:

```python
import gpxo
track = gpxo.Track('ExampleTrack.gpx')
mymap = track.folium_map(color='red', tiles='OpenTopoMap')
mymap.show_in_browser()
```

![](https://raw.githubusercontent.com/ovinc/gpxo/master/media/map-folium.jpg)


**Quick example 3**: show the path of a GPX file on a map with color-coding corresponding to elevation, using `mplleaflet` (*see Troubleshooting section below in case of error*):

```python
import gpxo
track = gpxo.Track('ExampleTrack.gpx')
track.map(plot='scatter', c=track.elevation, cmap='plasma')
```

![](https://raw.githubusercontent.com/ovinc/gpxo/master/media/map-elev.png)

Troubleshooting
===============

In case of the following error:
```
'XAxis' object has no attribute '_gridOnMajor
```

when using the `mplleaflet_map()` method, try downgrading Matplotlib to version <= 3.3.2 or install a forked version of mplleaflet (see https://github.com/jwass/mplleaflet/issues/75).

Information
===========

Requirements
------------

Python >= 3.6

Dependencies
------------

(automatically installed by pip if necessary)

- *numpy*
- *pandas*
- *matplotlib*
- *importlib-metadata*
- *gpxpy* (https://github.com/tkrajina/gpxpy)
- *vincenty* (https://github.com/maurycyp/vincenty)

Optional:
- *folium*
- *mplleaflet* (https://github.com/jwass/mplleaflet)

Author
------

Olivier Vincent

(ovinc.py@gmail.com)

License
-------

BSD 3-Clause (see *LICENCE* file)
