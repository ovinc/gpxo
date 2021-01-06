"""General tools for gpx data processing based on gpxpy."""


import numpy as np
from vincenty import vincenty


def closest_pt(pt, trajectory):
    """Finds closest pt to pt (lat, long) in trajectory (lats, longs).

    Parameters
    ----------
    pt is a tuple (lat, long)
    trajectory can be:
    - a tuple (lats, longs) where lats is an iterable of floats (and longs also)
    - a (2 * N) numpy array where N is the length of the trajectory
    - any other structure equivalent in terms of unpacking a, b = trajectory
    """
    lats, longs = trajectory
    ds = [vincenty((x, y), pt) for (x, y) in zip(lats, longs)]
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


def smooth(x, n=5, window='hanning'):
    """Smooth 1-d data with a window of requested size and type.

    Simplified version of numbo.smooth with smaller default window size (n)
    (see https://cameleon.univ-lyon1.fr/ovincent/numbo)

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    INPUT
    -----
    - `x`: the input signal
    - `n`: the dimension of the smoothing window; should be an odd integer
    - `window`: the type of window ('flat', 'hanning', 'hamming', 'bartlett',
    'blackman'); flat window will produce a moving average smoothing.

    OUTPUT
    ------
    - Smoothed signal of same length as input signal

    EXAMPLE
    -------
    npts = 100  # number of data points
    w = 7  # width of window used to smooth
    x = np.linspace(0, 7 * pi, npts)
    y = np.sin(x - 1) + 0.1 * np.random.randn(n)
    y_smooth = smooth(y, w)

    NOTES
    -----
    See also numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman,
    numpy.convolve, scipy.signal.lfilter
    """
    if x.size < n:
        raise ValueError("Input vector needs to be larger than window size.")

    if n == 1:  # no need to apply filter
        return x

    if window not in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        msg = "Only possible windows: 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
        raise ValueError(msg)

    xadd_left = 2 * x[0] - x[n:0:-1]
    xadd_right = 2 * x[-1] - x[-2:-n - 2:-1]
    x_expanded = np.concatenate((xadd_left, x, xadd_right))

    if window == 'flat':  # moving average
        w = np.ones(n, 'd')
    else:
        w = eval('np.' + window + '(n)')

    y = np.convolve(w / w.sum(), x_expanded, mode='valid')

    istart = int(n / 2) + 1

    return y[istart:istart + len(x)]
