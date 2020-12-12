"""Partial tests (pytest) for the gpxo module."""

from gpxo import compass


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
