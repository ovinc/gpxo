About
=====

Load GPS data from GPX files into Python as a numpy arrays and *pandas* DataFrames. Initial parsing done using the *gpxpy* package. Trajectory plotting on a map available using *mplleaflet*.

Quick Start
===========

Install
-------

From anywhere:
```bash
pip install git+https://cameleon.univ-lyon1.fr/ovincent/gpxo
```

From root of module:
```bash
pip install .
```

Load Track
----------

```python
track = gpxo.Track('ExampleTrack.gpx')
```
(it is possible to indicate which track or segment to consider during instantiation, by default it is the first one).

`track.data` is a *pandas* DataFrame containing time, position, elevation etc.; usual *pandas* methods can be used to analyze, manipulate and plot data. Individual columns are also available as numpy arrays as attributes of the class (see below).


Detailed Contents
=================

Track class
-----------

Load, inspect and plot GPX data using the `Track` class, with the foollowing methods and attributes.

### Methods

- `smooth()`: smooth position and elevation data (see `gpxo.smooth()` below),
- `plot()`: plot trajectory data using columns of `data` attribute (shortcut for `data.plot()`); takes `pandas.DataFrame.plot()` arguments,
- `map()`: plot trajectory on a map, using `mplleaflet.show()`.

### Basic Attributes

- `latitude` (numpy array): latitude in °,
- `longitude` (numpy array): longitude in °,
- `elevation` (numpy array): elevation in meters,
- `time` (numpy array): local time expressed as a datetime.datetime.

### Property attributes

(Read-only, and calculated/updated from basic attributes),
- `seconds` (numpy array): total number of seconds since beginning of track,
- `distance` (numpy array): total distance (km) since beginning of track,
- `velocity` (numpy array): instantaneous velocity (km/h),
- `compass` (numpy array): instantaneous compass bearing (°),
- `data` (pandas DataFrame): summary of all above attribues.

## Miscellaneous

Outside of the `Track` class, the following standalone function is also available:
- `compass(pt1, pt2)`: compass bearing (°) between pt1 (lat1, long1) and pt2 (lat2, long2),
- `closest_pt(pt, trajectory)`: closest pt in trajectory (latitude, longitude) to pt (xpt, ypt),
- `smooth(x, n, window)`: smooth 1-d array with a moving window of size n and type *window*.

Examples
=======

See Jupyter Notebook **Examples.ipynb** for a detailed example using real GPX data.


Information
===========

Requirements
------------

Python >= 3.6

Dependencies
------------

(automatically installed by pip if necessary)

- pandas
- matplotlib < 3.3.3 (due to bug in mplleaflet in 3.3.3)
- *gpxpy* (https://github.com/tkrajina/gpxpy)
- *vincenty* (https://github.com/maurycyp/vincenty)
- *mplleaflet* (https://github.com/jwass/mplleaflet)

Author
------

Olivier Vincent

(ovinc.py@gmail.com)

License
-------

BSD 3-Clause (see *LICENCE* file)
