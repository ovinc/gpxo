Homemade module to process gpx data.

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

Contents
--------

Load, inspect and plot GPX data using the `Track` class, with the foollowing methods and attributes.

### Methods

- `smooth()`: smooth position data, using arguments for the `numbo.smooth()` function,
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
- `data` (pandas DataFrame): summary of all above attribues.

### Miscellaneous

Outside of the `Track` class, the following standalone function is also available:
- `closest_pt(pt, trajectory)`: closest pt in trajectory (latitude, longitude) to pt (xpt, ypt)

Examples
--------

See Jupyter Notebook **Examples.ipynb**.

Dependencies
------------
- **numbo** (homemade: https://cameleon.univ-lyon1.fr/numbo)
- **gpxpy** (pip available)
- **vincenty** (pip available)
- **mplleaflet** (pip available)
