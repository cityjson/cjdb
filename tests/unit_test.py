import pytest
from pytest import approx
from shapely.geometry import MultiPolygon, Polygon

from cjdb.modules.exceptions import InvalidLodException
from cjdb.modules.geometric import (get_flattened_polygons_from_boundaries,
                                    get_geometry_with_minimum_lod,
                                    get_ground_geometry,
                                    get_ground_geometry_mine,
                                    get_surfaces_from_boundaries)

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

def test_get_surfaces_from_boundaries_multisurface():
    res = get_surfaces_from_boundaries(boundary_multisurface)
    print(res)
    assert isinstance(res[0][0], Polygon)
    assert isinstance(res[0][1], Polygon)


def test_get_surfaces_from_boundaries_solid():
    res = get_surfaces_from_boundaries(boundary_solid)
    print(res)
    assert isinstance(res[0][0][0], Polygon)


def test_get_flattened_polygons_from_boundaries_multisurface():
    res = get_flattened_polygons_from_boundaries(boundary_multisurface_not_nested)
    print(res)
    assert isinstance(res[0], Polygon)
    assert res[0].exterior.coords[0][0] == approx(121077.757)
    assert res[0].exterior.coords[0][1] == approx(485119.04699999996)
    assert len(res) == 1


def test_get_flattened_polygons_from_boundaries_solid():
    res = get_flattened_polygons_from_boundaries(boundary_solid)
    print(res)
    assert isinstance(res[0], Polygon)


# def test_get_geometries_from_boundaries_single_point():
#     res = get_geometries_from_boundaries(boundary_multipoint_single_point)
#     assert isinstance(res[0], Point)


# def test_get_geometries_from_boundaries_multiple_points():
#     res = get_geometries_from_boundaries(boundary_multipoint_many_points)
#     assert isinstance(res[0], Point)
#     assert isinstance(res[1], Point)


# def test_get_geometries_from_boundaries_multiline_string():
#     res = get_geometries_from_boundaries(boundary_multiline_string)
#     print(res)
#     assert isinstance(res[0][0], Point)
#     assert res[0][0].x == approx(121483.808)
#     assert res[0][0].y == approx(484844.936)
#     assert res[0][0].z == approx(0.0)
#     assert isinstance(res[0][1], Point)
#     assert res[0][1].x == approx(121099.937)
#     assert res[0][1].y == approx(485192.14)
#     assert res[0][1].z == approx(0.0)
#     assert isinstance(res[1][0], Point)
#     assert res[1][0].x == approx(121099.444)
#     assert res[1][0].y == approx(485194.594)
#     assert res[1][0].z == approx(0.0)
#     assert isinstance(res[1][1], Point)
#     assert res[1][1].x == approx(121093.329)
#     assert res[1][1].y == approx(485196.323)
#     assert res[1][1].z == approx(0.0)


# def test_get_geometries_from_boundaries_solid():
#     res = get_geometries_from_boundaries(boundary_solid)
#     print(res)
#     print(type(res[0][0][0]))
#     assert isinstance(res[0][0][0], Polygon)
#     assert isinstance(res[0][1][0], Polygon)
#     assert isinstance(res[0][2][0], Polygon)
#     assert isinstance(res[0][3][0], Polygon)


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
    print(ground_geometry)
    assert isinstance(ground_geometry, MultiPolygon)


def test_get_ground_geometry_mine():
    ground_geometry1 = get_ground_geometry([geometry_2], "test")
    ground_geometry2 = get_ground_geometry_mine([geometry_2], "test")
    assert ground_geometry1 == MultiPolygon([ground_geometry2])


def test_get_ground_geometry_mine():
    ground_geometry1 = get_ground_geometry([geometry_5], "test")
    ground_geometry2 = get_ground_geometry_mine([geometry_5], "test")
    assert ground_geometry1 == MultiPolygon([ground_geometry2])
