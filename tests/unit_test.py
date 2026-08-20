from typing import Any
from unittest import mock
from urllib.error import URLError

import pytest
import requests
from pytest import approx
from shapely.geometry import MultiPolygon, Polygon

from cjdb.modules.checks import check_reprojection
from cjdb.modules.exceptions import InvalidLodException, PathNotFoundException
from cjdb.modules.extensions import ExtensionHandler
from cjdb.modules.geometric import (
    get_flattened_polygons_from_boundaries,
    get_geometry_with_minimum_lod,
    get_ground_geometry,
    get_ground_surfaces,
)
from cjdb.modules.importer import Importer
from cjdb.modules.utils import get_city_object_types

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

geometry_1: dict[str, Any] = {}
geometry_1["boundaries"] = boundary_multisurface
geometry_1["lod"] = "1.2"
geometry_1["type"] = "MultiSurface"

geometry_2: dict[str, Any] = {}
geometry_2["boundaries"] = boundary_multisurface_not_nested
geometry_2["lod"] = "0.0"
geometry_2["type"] = "MultiSurface"

geometry_3: dict[str, Any] = {}
geometry_3["boundaries"] = []
geometry_3["lod"] = "2.1"
geometry_3["type"] = "MultiSurface"

geometry_4: dict[str, Any] = {}
geometry_4["boundaries"] = []
geometry_4["lod"] = "foo"
geometry_4["type"] = "MultiSurface"

geometry_5: dict[str, Any] = {}
geometry_5["boundaries"] = boundary_multisurface
geometry_5["lod"] = "0"
geometry_5["type"] = "MultiSurface"

geometry_6: dict[str, Any] = {}
geometry_6["boundaries"] = boundary_solid
geometry_6["lod"] = "1.2"
geometry_6["type"] = "MultiSurface"


def test_get_flattened_polygons_from_boundaries_multisurface():
    res = get_flattened_polygons_from_boundaries(boundary_multisurface_not_nested)
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
    assert ground_surfaces[0] == Polygon(((0, 1), (1, 1), (1, 0), (0, 0), (0, 1)))


def test_get_city_object_types():
    types = get_city_object_types()
    assert "Building" in types
    assert "BuildingPart" in types
    assert "Bridge" in types
    assert "BridgePart" in types
    assert types == sorted(types)


def _mock_transformer_group(best_available=True, download_side_effect=None):
    group = mock.Mock()
    group.best_available = best_available
    group.download_grids = mock.Mock(side_effect=download_side_effect)
    return group


def _patch_transformer_group(group):
    crs = mock.MagicMock()
    crs.from_epsg.return_value.axis_info = [mock.Mock(), mock.Mock(), mock.Mock()]
    return (
        mock.patch("cjdb.modules.checks.TransformerGroup", return_value=group),
        mock.patch("cjdb.modules.checks.CRS", crs),
        mock.patch("cjdb.modules.checks.datadir"),
    )


def test_check_reprojection_download_grids_urlerror():
    group = _mock_transformer_group(
        best_available=False, download_side_effect=URLError("no network")
    )
    patches = _patch_transformer_group(group)
    with patches[0], patches[1], patches[2]:
        check_reprojection(4326, 28992)
    assert group.download_grids.called


def test_check_reprojection_download_grids_oserror():
    group = _mock_transformer_group(
        best_available=False, download_side_effect=OSError("permission denied")
    )
    patches = _patch_transformer_group(group)
    with patches[0], patches[1], patches[2]:
        check_reprojection(4326, 28992)
    assert group.download_grids.called


def test_check_reprojection_download_grids_success():
    group = _mock_transformer_group(best_available=False)
    patches = _patch_transformer_group(group)
    with patches[0], patches[1], patches[2]:
        check_reprojection(4326, 28992)
    assert group.download_grids.called


def test_check_reprojection_best_available_skips_download():
    group = _mock_transformer_group(best_available=True)
    patches = _patch_transformer_group(group)
    with patches[0], patches[1], patches[2]:
        check_reprojection(4326, 28992)
    assert not group.download_grids.called


def test_check_reprojection_unexpected_error_propagates():
    group = _mock_transformer_group(
        best_available=False, download_side_effect=ValueError("boom")
    )
    patches = _patch_transformer_group(group)
    with patches[0], patches[1], patches[2], pytest.raises(ValueError):
        check_reprojection(4326, 28992)


def test_extension_handler_request_exception_is_handled():
    with mock.patch(
        "cjdb.modules.extensions.requests.get",
        side_effect=requests.exceptions.ConnectionError("connection failed"),
    ):
        handler = ExtensionHandler({"ext": {"url": "http://example.com/ext.json"}})
    assert handler.full_definitions == {}
    assert handler.extra_root_properties == []


def test_parse_cityjson_path_not_found():
    importer = Importer(
        engine=None,
        filepath="/nonexistent/path/does/not/exist.jsonl",
        db_schema="test",
        input_srid=None,
        indexed_attributes=[],
        partial_indexed_attributes=[],
        ignore_repeated_file=False,
        overwrite=False,
        transform=False,
        clustering=False,
    )
    with pytest.raises(PathNotFoundException):
        importer.parse_cityjson()
