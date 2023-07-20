import pytest

from cjdb.modules.exceptions import InvalidLodException
from cjdb.modules.geometric import (get_geometry_with_minimum_lod)

geometry_1 = dict()
geometry_1['boundaries'] = [[[[121099.937, 485192.14, 0.0],
                            [121099.444, 485194.594, 0.0],
                            [121094.05500000001, 485193.087, 0.0],
                            [121093.329, 485196.32399999996, 0.0],
                            [121083.838, 485194.19399999996, 0.0],
                            [121084.52900000001, 485190.83999999997, 0.0],
                            [121083.901, 485190.697, 0.0],
                            [121086.12700000001, 485180.77999999997, 0.0],
                            [121096.30500000001, 485183.064, 0.0],
                            [121100.3, 485165.266, 0.0],
                            [121105.697, 485166.477, 0.0]],
                           [[121483.808, 484844.936, 0.0],
                            [121483.808, 484844.936, 0.0],
                            [121483.808, 484844.936, 0.0],
                            [121483.808, 484844.936, 0.0]]]]
geometry_1['lod'] = '1.2'
geometry_1['type'] = 'MultiSurface'

geometry_2 = dict()
geometry_2['boundaries'] = []
geometry_2['lod'] = '0.0'
geometry_2['type'] = 'MultiSurface'

geometry_3 = dict()
geometry_3['boundaries'] = []
geometry_3['lod'] = '2.1'
geometry_3['type'] = 'MultiSurface'

geometry_4 = dict()
geometry_4['boundaries'] = []
geometry_4['lod'] = 'foo'
geometry_4['type'] = 'MultiSurface'


def test_get_geometry_with_minimum_lod_no_geom():
    res = get_geometry_with_minimum_lod([])
    assert res is None


def test_get_geometry_with_minimum_lod_single_geom():
    res = get_geometry_with_minimum_lod([geometry_1])
    assert res['lod'] == '1.2'


def test_get_geometry_with_minimum_lod_multiple_geom():
    res = get_geometry_with_minimum_lod([geometry_1, geometry_2, geometry_3])
    assert res['lod'] == '0.0'


def test_get_geometry_with_minimum_lod_wrong_value():
    with pytest.raises(InvalidLodException):
        _ = get_geometry_with_minimum_lod([geometry_1,
                                           geometry_2,
                                           geometry_4])

# def test_get_ground_geometry():
#     ground_geometry = get_ground_geometry([geometry_1], "test")
#     pass
#     assert ground_geometry is not None
