"""Partial tests (pytest) for the gpxo module."""

import numpy as np
import gpxo
from gpxo import compass, closest_pt


def test_loadtrack():
    """Loading/smoothing/velocity calculation from position/distance."""
    track = gpxo.Track('ExampleTrack.gpx')
    track.smooth(n=51)
    assert round(track.data['velocity (km/h)'].iloc[4]) == 14


def test_loadtrack_notime():
    """Loading in situation where GPX does not have time info."""
    track = gpxo.Track('ExampleTrack_NoTime.gpx')
    assert round(track.data['compass (°)'].iloc[3]) == 93


def test_compass_single():
    """Test compass calculation with individual (lat, long) tuples."""
    assert compass((0, 0), (45, 0)) == 0.0
    assert compass((45, 0), (0, 0)) == 180.0
    assert compass((0, 0), (0, 30)) == 90.0
    assert compass((0, 30), (0, -30)) == 270.0


def test_compass_multiple():
    """Test compass calculation with tuples of iterables (lat_list, long_list)."""
    lat1 = (0, 45, 0, 0)
    long1 = (0, 0, 0, 30)
    lat2 = (45, 0, 0, 0)
    long2 = (0, 0, 30, -30)
    pt1 = (lat1, long1)
    pt2 = (lat2, long2)
    assert all(compass(pt1, pt2) == (0, 180, 90, 270))


def test_closest_pt():
    """Test find index of closest point in trajectory to specified pt."""
    lats = [45.011, 45.012, 45.013, 45.014, 45.015, 45.016, 45.017]
    longs = [5.883, 5.886, 5.887, 5.889, 5.891, 5.893, 5.895]
    traj = np.array((lats, longs))
    pt = (45.0133, 5.888)
    i = closest_pt(pt, traj)
    assert i == 2
