import pytest
from pytest import approx
from shapely.geometry import MultiPolygon, Polygon

from cjdb.modules.exceptions import InvalidLodException
from cjdb.modules.geometric import (
    get_flattened_polygons_from_boundaries,
    get_geometry_with_minimum_lod,
    get_ground_geometry,
    get_ground_surfaces,
)

boundary_multipoint_single_point = [[121483.808, 484844.936, 0.0]]
boundary_multipoint_many_points = [
    [121483.808, 484844.936, 0.0],
    [121099.937, 485192.14, 0.0],
]
boundary_multiline_string = [
    [[121483.808, 484844.936, 0.0], [121099.937, 485192.14, 0.0]],
    [[121099.444, 485194.594, 0.0], [121093.329, 485196.323, 0.0]],
]
boundary_multisurface = [
    [
        [
            [121099.937, 485192.14, 0.0],
            [121099.444, 485194.594, 0.0],
            [121094.05500000001, 485193.087, 0.0],
            [121093.329, 485196.32399999996, 0.0],
            [121083.838, 485194.19399999996, 0.0],
            [121084.52900000001, 485190.83999999997, 0.0],
            [121083.901, 485190.697, 0.0],
            [121086.12700000001, 485180.77999999997, 0.0],
            [121096.30500000001, 485183.064, 0.0],
            [121100.3, 485165.266, 0.0],
            [121105.697, 485166.477, 0.0],
        ],
        [
            [121483.808, 484844.936, 0.0],
            [121483.808, 484844.936, 0.0],
            [121483.808, 484844.936, 0.0],
            [121483.808, 484844.936, 0.0],
        ],
    ]
]

boundary_multisurface_not_nested = [
    [
        [
            [121077.757, 485119.04699999996, 0.0],
            [121066.90800000001, 485116.72599999997, 0.0],
            [121066.88900000001, 485116.665, 0.0],
            [121068.043, 485111.091, 0.0],
            [121078.916, 485113.47599999997, 0.0],
        ]
    ]
]

boundary_solid = [
    [
        [[[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0], [0.0, 1.0, 1.0]]],
        [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 1.0], [0.0, 0.0, 1.0]]],
        [[[1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 1.0, 1.0], [1.0, 0.0, 1.0]]],
        [[[1.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 1.0, 1.0], [1.0, 1.0, 1.0]]],
        [[[0.0, 1.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 1.0]]],
        [[[0.0, 1.0, 0.0], [1.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]]],
    ]
]

geometry_1 = dict()
geometry_1["boundaries"] = boundary_multisurface
geometry_1["lod"] = "1.2"
geometry_1["type"] = "MultiSurface"

geometry_2 = dict()
geometry_2["boundaries"] = boundary_multisurface_not_nested
geometry_2["lod"] = "0.0"
geometry_2["type"] = "MultiSurface"

geometry_3 = dict()
geometry_3["boundaries"] = []
geometry_3["lod"] = "2.1"
geometry_3["type"] = "MultiSurface"

geometry_4 = dict()
geometry_4["boundaries"] = []
geometry_4["lod"] = "foo"
geometry_4["type"] = "MultiSurface"

geometry_5 = dict()
geometry_5["boundaries"] = boundary_multisurface
geometry_5["lod"] = "0"
geometry_5["type"] = "MultiSurface"

geometry_6 = dict()
geometry_6["boundaries"] = boundary_solid
geometry_6["lod"] = "1.2"
geometry_6["type"] = "MultiSurface"


def test_get_flattened_polygons_from_boundaries_multisurface():
    res = get_flattened_polygons_from_boundaries(
        boundary_multisurface_not_nested)
    assert isinstance(res[0], Polygon)
    assert res[0].exterior.coords[0][0] == approx(121077.757)
    assert res[0].exterior.coords[0][1] == approx(485119.04699999996)
    assert len(res) == 1


def test_get_flattened_polygons_from_boundaries_solid():
    res = get_flattened_polygons_from_boundaries(boundary_solid)
    assert isinstance(res[0], Polygon)


def test_get_geometry_with_minimum_lod_no_geom():
    res = get_geometry_with_minimum_lod([])
    assert res is None


def test_get_geometry_with_minimum_lod_single_geom():
    res = get_geometry_with_minimum_lod([geometry_1])
    assert res["lod"] == "1.2"


def test_get_geometry_with_minimum_lod_multiple_geom():
    res = get_geometry_with_minimum_lod([geometry_1, geometry_2, geometry_3])
    assert res["lod"] == "0.0"


def test_get_geometry_with_minimum_lod_wrong_value():
    with pytest.raises(InvalidLodException):
        _ = get_geometry_with_minimum_lod([geometry_1, geometry_2, geometry_4])


def test_get_ground_geometry():
    ground_geometry = get_ground_geometry([geometry_2], "test")
    assert isinstance(ground_geometry, MultiPolygon)


def test_get_ground_geometry_surfaces():
    ground_geometry = get_ground_geometry([geometry_5], "test")
    assert isinstance(ground_geometry, MultiPolygon)
    ground_geometry = get_ground_geometry([geometry_5], "test")
    assert isinstance(ground_geometry, MultiPolygon)


def test_get_ground_surfaces():
    surfaces = get_flattened_polygons_from_boundaries(boundary_solid)
    ground_surfaces = get_ground_surfaces(surfaces)
    assert ground_surfaces[0] == Polygon(((0, 1),
                                          (1, 1),
                                          (1, 0),
                                          (0, 0),
                                          (0, 1)))
