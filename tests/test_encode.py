import pytest
from vector_tile_base import vector_tile_pb2
from vector_tile_base import VectorTile, SplineFeature, PointFeature, PolygonFeature, LineStringFeature, Layer, FeatureAttributes, Float, FloatList

def test_no_layers():
    vt = VectorTile()
    assert len(vt.serialize()) == 0

def test_create_layer():
    vt = VectorTile()
    layer = vt.add_layer('point')
    assert layer.name == 'point'
    assert layer.version == 2
    assert isinstance(layer, Layer)
    layer = vt.add_layer('point_3', 3)
    assert layer.name == 'point_3'
    assert layer.version == 3
    assert isinstance(layer, Layer)
    layer = vt.add_layer('point_4', 4)
    assert layer.name == 'point_4'
    assert layer.version == 4
    assert isinstance(layer, Layer)

def test_layer_extent():
    vt = VectorTile()
    layer = vt.add_layer('test')
    assert layer.extent == 4096
    layer.extent = 8000
    assert layer.extent == 8000

def test_layer_zoom_x_y():
    vt = VectorTile()
    layer = vt.add_layer('test0', version=2)
    assert layer.x == None
    assert layer.y == None
    assert layer.zoom == None
    with pytest.raises(Exception):
        layer.set_tile_location(zoom=3, x=4, y=2)
    layer = vt.add_layer('test1', version=3)
    assert layer.x == None
    assert layer.y == None
    assert layer.zoom == None
    layer.set_tile_location(zoom=3, x=4, y=2)
    assert layer.x == 4
    assert layer.y == 2
    assert layer.zoom == 3
    layer = vt.add_layer('test2', version=3, x=0, y=0, zoom=0)
    assert layer.x == 0
    assert layer.y == 0
    assert layer.zoom == 0
    layer.set_tile_location(zoom=3, x=4, y=2)
    assert layer.x == 4
    assert layer.y == 2
    assert layer.zoom == 3
    with pytest.raises(Exception):
        layer.x = 5
    with pytest.raises(Exception):
        layer.y = 5
    with pytest.raises(Exception):
        layer.zoom = 4
    with pytest.raises(Exception):
        layer = vt.add_layer('test2', version=2, x=0, y=0, zoom=0)
    with pytest.raises(Exception):
        vt.add_layer('test3', version=3, x=-1, y=0, zoom=0)
    with pytest.raises(Exception):
        vt.add_layer('test4', version=3, x=1, y=0, zoom=0)
    with pytest.raises(Exception):
        vt.add_layer('test5', version=3, x=2, y=0, zoom=1)
    with pytest.raises(Exception):
        vt.add_layer('test3', version=3, x=0, y=-1, zoom=0)
    with pytest.raises(Exception):
        vt.add_layer('test4', version=3, x=0, y=1, zoom=0)
    with pytest.raises(Exception):
        vt.add_layer('test5', version=3, x=0, y=2, zoom=1)
    with pytest.raises(Exception):
        vt.add_layer('test3', version=3, x=0, y=0, zoom=-1)
    with pytest.raises(Exception):
        vt.add_layer('test3', version=3, x=0, y=0, zoom=51)

def test_layer_name():
    vt = VectorTile()
    layer = vt.add_layer('test')
    assert layer.name == 'test'
    layer.name = 'foo'
    assert layer.name == 'foo'

def test_layer_features():
    vt = VectorTile()
    layer = vt.add_layer('test')
    assert len(layer.features) == 0
    assert isinstance(layer.features, list)
    with pytest.raises(AttributeError):
        layer.features = [1,2]
    assert len(layer.features) == 0

def test_feature_id():
    vt = VectorTile()
    layer = vt.add_layer('test', version=2)
    feature = layer.add_point_feature()
    assert feature.id == None
    feature.id = 12
    assert feature.id == 12
    # Fails for a version 2 layer
    with pytest.raises(Exception):
        feature.id = "FeatureName"

    layer = vt.add_layer('test2', version=3)
    feature = layer.add_point_feature()
    assert feature.id == None
    feature.id = 12
    assert feature.id == 12
    feature.id = "FeatureName"
    assert feature.id == "FeatureName"

    data = vt.serialize()
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    assert feature.id == 12
    feature = vt.layers[1].features[0]
    assert feature.id == "FeatureName"

def test_feature_attributes_version_2():
    vt = VectorTile()
    layer = vt.add_layer('test', version=2)
    assert layer.version == 2
    feature = layer.add_point_feature()
    assert isinstance(feature, PointFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    prop = feature.attributes
    assert isinstance(prop, FeatureAttributes)
    assert feature.attributes == {}
    assert prop == {}
    prop['fun'] = 'stuff'
    assert 'fun' in prop
    assert prop['fun'] == 'stuff'
    assert feature.attributes['fun'] == 'stuff'
    assert feature.attributes == {'fun':'stuff'}
    # Can set by external dictionary
    prop_dict = { 'number': 1, 'bool': True, 'string': 'foo', 'float': 4.1 }
    feature.attributes = prop_dict
    assert feature.attributes == prop_dict
    # Key error on not existant property
    with pytest.raises(KeyError):
        foo = feature.attributes['doesnotexist']
    # Type errors on invalid key types
    with pytest.raises(TypeError):
        feature.attributes[1.234] = True
    with pytest.raises(TypeError):
        feature.attributes[1] = True
    with pytest.raises(TypeError):
        foo = feature.attributes[1.234]
    with pytest.raises(TypeError):
        foo = feature.attributes[1]
    # During setting invalid attributes with bad keys or value types will just be dropped
    prop_dict = {'foo': [1,2,3], 'fee': [{'a':'b'}, {'a':['c','d']}], 1.2341: 'stuff', 1: 'fish', 'go': False, 'double': 2.32432, 'float': Float(23432.3222) }
    prop_dict2 = {'go': False, 'double': 2.32432, 'float': Float(23432.3222) }
    feature.attributes = prop_dict
    assert feature.attributes != prop_dict
    assert feature.attributes == prop_dict2

    # Show that geometric attributes don't work with version 2
    with pytest.raises(Exception):
        feature.geometric_attributes = {'hmm': [1,2,3,4,5]}

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    assert feature.attributes['go'] == prop_dict2['go']
    assert feature.attributes['double'] == prop_dict2['double']
    # note change is expected due to float encoding!
    assert feature.attributes['float'] == 23432.322265625
    # Show that geometric attributes don't work with version 2
    assert feature.geometric_attributes == {}

def test_feature_attributes_version_3_legacy():
    vt = VectorTile()
    layer = vt.add_layer('test', version=3, legacy_attributes=True)
    assert layer.version == 3
    feature = layer.add_point_feature()
    assert isinstance(feature, PointFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    prop = feature.attributes
    assert isinstance(prop, FeatureAttributes)
    assert feature.attributes == {}
    assert prop == {}
    prop['fun'] = 'stuff'
    assert 'fun' in prop
    assert prop['fun'] == 'stuff'
    assert feature.attributes['fun'] == 'stuff'
    assert feature.attributes == {'fun':'stuff'}
    # Can set by external dictionary
    prop_dict = { 'number': 1, 'bool': True, 'string': 'foo', 'float': 4.1 }
    feature.attributes = prop_dict
    assert feature.attributes == prop_dict
    # Key error on not existant property
    with pytest.raises(KeyError):
        foo = feature.attributes['doesnotexist']
    # Type errors on invalid key types
    with pytest.raises(TypeError):
        feature.attributes[1.234] = True
    with pytest.raises(TypeError):
        feature.attributes[1] = True
    with pytest.raises(TypeError):
        foo = feature.attributes[1.234]
    with pytest.raises(TypeError):
        foo = feature.attributes[1]
    assert len(layer._values) == 5
    # During setting invalid attributes with bad keys or value types will just be dropped
    prop_dict = {
        'foo': [1,2,3],
        'fee': [{'a':'b'}, {'a':['c','d']}],
        1.2341: 'stuff',
        1: 'fish',
        'go': False,
        'double': 2.32432,
        'float': Float(23432.3222),
        'double2': 23432.3222,
        'double3': 23432.3222
    }
    prop_dict2 = {
        'go': False,
        'double': 2.32432,
        'float': Float(23432.3222),
        'double2': 23432.3222,
        'double3': 23432.3222
    }
    feature.attributes = prop_dict
    assert feature.attributes != prop_dict
    assert feature.attributes == prop_dict2
    assert len(layer._values) == 9

    # Show that geometric attributes don't work with version 3 legacy attributes
    with pytest.raises(Exception):
        feature.geometric_attributes = {'hmm': [1,2,3,4,5]}

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    assert feature.attributes['go'] == prop_dict2['go']
    assert feature.attributes['double'] == prop_dict2['double']
    # note change is expected due to float encoding!
    assert feature.attributes['float'] == 23432.322265625
    # Show that geometric attributes don't work with version 3 with legacy attributes
    assert feature.geometric_attributes == {}

def test_feature_attributes_version_3():
    vt = VectorTile()
    layer = vt.add_layer('test', version=3)
    assert layer.version == 3
    feature = layer.add_point_feature()
    assert isinstance(feature, PointFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    prop = feature.attributes
    assert isinstance(prop, FeatureAttributes)
    assert feature.attributes == {}
    assert prop == {}
    prop['fun'] = 'stuff'
    assert 'fun' in prop
    assert prop['fun'] == 'stuff'
    assert feature.attributes['fun'] == 'stuff'
    assert feature.attributes == {'fun':'stuff'}
    # Can set by external dictionary
    prop_dict = { 'number': 1, 'bool': True, 'string': 'foo', 'float': 4.1 }
    feature.attributes = prop_dict
    assert feature.attributes == prop_dict
    # Key error on not existant property
    with pytest.raises(KeyError):
        foo = feature.attributes['doesnotexist']
    # Type errors on invalid key types
    with pytest.raises(TypeError):
        feature.attributes[1.234] = True
    with pytest.raises(TypeError):
        feature.attributes[1] = True
    with pytest.raises(TypeError):
        foo = feature.attributes[1.234]
    with pytest.raises(TypeError):
        foo = feature.attributes[1]

    dvalues = [1.0, 2.0, None, 2.3, 4.3, None, None, 15.0, 22.5]
    scaling1 = layer.add_attribute_scaling(precision=10.0**-6, min_value=1.0, max_value=25.0)
    assert scaling1.index == 0
    assert scaling1.offset == 0
    assert scaling1.base == 1.0
    assert scaling1.multiplier == 9.5367431640625e-07

    # roughly 10**-8 precision
    scaling2 = layer.add_attribute_scaling(offset=10, base=8.0, multiplier=7.450580596923828e-09)
    assert scaling2.index == 1
    assert scaling2.offset == 10
    assert scaling2.base == 8.0
    assert scaling2.multiplier == 7.450580596923828e-09

    flist1 = FloatList(scaling1, dvalues)
    flist2 = FloatList(scaling2, dvalues)

    # During setting invalid attributes with bad keys or value types will just be dropped
    prop_dict = {
        'foo': [1,2,3],
        'fee': [{'a':'b'}, {'a':['c','d']}],
        1.2341: 'stuff',
        1: 'fish',
        'go': False,
        'double': 2.32432,
        'float': Float(23432.3222),
        'doubleList': flist1,
        'otherDoubleList': flist2
    }
    prop_dict2 = {
        'foo': [1,2,3],
        'fee': [{'a':'b'}, {'a':['c','d']}],
        'go': False,
        'double': 2.32432,
        'float': Float(23432.3222),
        'doubleList': flist1,
        'otherDoubleList': flist2
    }
    geometric_dict = {
        'now': [1,2,4,5,234],
        'stuff': [{'x':12}, None, None, None, {'y':13}],
        'dlist': flist2,
        'not': None,
        'this': 8,
        'or': True,
        'that': { 'lost':'values'}
    }
    geometric_dict2 = {
        'now': [1,2,4,5,234],
        'stuff': [{'x':12}, None, None, None, {'y':13}],
        'dlist': flist2
    }
    feature.attributes = prop_dict
    assert feature.attributes != prop_dict
    assert feature.attributes == prop_dict2

    feature.geometric_attributes = geometric_dict
    assert feature.geometric_attributes == geometric_dict2

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    assert feature.attributes['foo'] == prop_dict2['foo']
    assert feature.attributes['fee'] == prop_dict2['fee']
    assert feature.attributes['go'] == prop_dict2['go']
    assert feature.attributes['double'] == prop_dict2['double']
    # note change is expected due to float encoding!
    assert feature.attributes['float'] == 23432.322265625
    # specialized double encoding with scaling should result in approximate equality
    assert isinstance(feature.attributes['doubleList'], list)
    dlist = feature.attributes['doubleList']
    for i in range(len(dlist)):
        if dvalues[i] is None:
            assert dlist[i] is None
        else:
            assert abs(dvalues[i] - dlist[i]) < 10.0**-6
    assert isinstance(feature.attributes['otherDoubleList'], list)
    dlist = feature.attributes['otherDoubleList']
    for i in range(len(dlist)):
        if dvalues[i] is None:
            assert dlist[i] is None
        else:
            assert abs(dvalues[i] - dlist[i]) < 10.0**-8

    assert feature.geometric_attributes['now'] == geometric_dict2['now']
    assert feature.geometric_attributes['stuff'] == geometric_dict2['stuff']
    dlist = feature.geometric_attributes['dlist']
    for i in range(len(dlist)):
        if dvalues[i] is None:
            assert dlist[i] is None
        else:
            assert abs(dvalues[i] - dlist[i]) < 10.0**-8

def test_create_point_feature():
    vt = VectorTile()
    layer = vt.add_layer('test')
    feature = layer.add_point_feature()
    assert isinstance(feature, PointFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert not feature.has_elevation
    feature.add_points([10,11])
    geometry = feature.get_points()
    assert geometry[0] == [10,11]
    # add points simply adds to end
    feature.add_points([10,12])
    feature.add_points([10,13])
    geometry = feature.get_points()
    assert geometry[1] == [10,12]
    assert geometry[2] == [10,13]
    # clear current geometry
    feature.clear_geometry()
    assert feature.get_points() == []
    # This is proper way to add multiple points!
    feature.add_points([[10,11],[10,12],[10,13]])
    assert feature.get_points() == [[10,11],[10,12],[10,13]]

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    feature.add_points([10,14])
    assert feature.get_points() == [[10,11],[10,12],[10,13],[10,14]]

def test_create_point_feature_3d():
    vt = VectorTile()
    layer = vt.add_layer('test')
    ## Should fail first because layer is a version 2 layer
    with pytest.raises(Exception):
        feature = layer.add_point_feature(has_elevation=True)
    vt = VectorTile()
    layer = vt.add_layer('test', version=3)
    feature = layer.add_point_feature(has_elevation=True)
    assert isinstance(feature, PointFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert feature.has_elevation
    ## Should fail to add 2 point list
    with pytest.raises(IndexError):
        feature.add_points([10,11])
    feature.add_points([10,11,12])
    geometry = feature.get_points()
    assert geometry[0] == [10,11,12]
    # add points simply adds to end
    feature.add_points([10,12,13])
    feature.add_points([10,13,14])
    geometry = feature.get_points()
    assert geometry[1] == [10,12,13]
    assert geometry[2] == [10,13,14]
    # clear current geometry
    feature.clear_geometry()
    assert feature.get_points() == []
    # This is proper way to add multiple points!
    feature.add_points([[10,11,12],[10,12,13],[10,13,14]])
    assert feature.get_points() == [[10,11,12],[10,12,13],[10,13,14]]

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    feature.add_points([10,14,15])
    assert feature.get_points() == [[10,11,12],[10,12,13],[10,13,14],[10,14,15]]

def test_create_line_feature():
    vt = VectorTile()
    layer = vt.add_layer('test')
    feature = layer.add_line_string_feature()
    assert isinstance(feature, LineStringFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert not feature.has_elevation
    line_string = [[10,11],[10,12],[10,13],[10,14]]
    feature.add_line_string(line_string)
    # note that we pull back possible multi line string here
    assert feature.get_line_strings() == [line_string]

    bad_line_string = [[1,1]]
    with pytest.raises(Exception):
        feature.add_line_string(bad_line_string)
    assert feature.get_line_strings() == [line_string]
    bad_line_string2 = [[1,1], [0]]
    with pytest.raises(IndexError):
        feature.add_line_string(bad_line_string2)
    assert feature.get_line_strings() == [line_string]

    line_string2 = [[9,9],[30,5]]
    feature.add_line_string(line_string2)
    assert feature.get_line_strings() == [line_string, line_string2]

    # clear current geometry
    feature.clear_geometry()
    assert feature.get_line_strings() == []
    feature.add_line_string(line_string)
    assert feature.get_line_strings() == [line_string]

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    feature.add_line_string(line_string2)
    assert feature.get_line_strings() == [line_string, line_string2]

def test_create_line_feature_3d():
    vt = VectorTile()
    layer = vt.add_layer('test')
    # Should raise because is version 2 tile
    with pytest.raises(Exception):
        feature = layer.add_line_string_feature(has_elevation=True)
    vt = VectorTile()
    layer = vt.add_layer('test', version=3)
    feature = layer.add_line_string_feature(has_elevation=True)
    assert isinstance(feature, LineStringFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert feature.has_elevation
    line_string = [[10,11,12],[10,12,13],[10,13,14],[10,14,15]]
    feature.add_line_string(line_string)
    # note that we pull back possible multi line string here
    assert feature.get_line_strings() == [line_string]

    bad_line_string = [[1,1,1]]
    with pytest.raises(Exception):
        feature.add_line_string(bad_line_string)
    assert feature.get_line_strings() == [line_string]
    bad_line_string2 = [[1,1],[2,2]]
    with pytest.raises(IndexError):
        feature.add_line_string(bad_line_string2)
    assert feature.get_line_strings() == [line_string]

    line_string2 = [[9,9,9],[30,5,9]]
    feature.add_line_string(line_string2)
    assert feature.get_line_strings() == [line_string, line_string2]

    # clear current geometry
    feature.clear_geometry()
    assert feature.get_line_strings() == []
    feature.add_line_string(line_string)
    assert feature.get_line_strings() == [line_string]

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    feature.add_line_string(line_string2)
    assert feature.get_line_strings() == [line_string, line_string2]

def test_create_polygon_feature():
    vt = VectorTile()
    layer = vt.add_layer('test')
    feature = layer.add_polygon_feature()
    assert isinstance(feature, PolygonFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert not feature.has_elevation
    polygon = [[[0,0],[10,0],[10,10],[0,10],[0,0]],[[3,3],[3,5],[5,5],[3,3]]]
    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_rings() == polygon
    assert feature.get_polygons() == [polygon]

    bad_ring1 = [[0,0],[1,0]]
    with pytest.raises(Exception):
        feature.add_ring(bad_ring)
    assert feature.get_polygons() == [polygon]

    bad_ring2 = [[0,0],[1,0],[0,0]]
    with pytest.raises(Exception):
        feature.add_ring(bad_ring2)
    assert feature.get_polygons() == [polygon]

    bad_ring3 = [[0,0],[1,0],[1,1],[1],[0,0]]
    with pytest.raises(IndexError):
        feature.add_ring(bad_ring3)
    assert feature.get_polygons() == [polygon]

    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_polygons() == [polygon, polygon]

    # clear current geometry
    feature.clear_geometry()
    assert feature.get_rings() == []
    assert feature.get_polygons() == []

    # Add in opposite order
    feature.add_ring(polygon[1])
    feature.add_ring(polygon[0])
    assert feature.get_rings() == [polygon[1], polygon[0]]
    # First ring in wrong winding order so dropped from polygon output
    assert feature.get_polygons() == [[polygon[0]]]

    # clear current geometry
    feature.clear_geometry()
    assert feature.get_rings() == []
    assert feature.get_polygons() == []

    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_rings() == polygon
    assert feature.get_polygons() == [polygon]

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    assert feature.get_rings() == polygon
    assert feature.get_polygons() == [polygon]
    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_polygons() == [polygon, polygon]

def test_create_polygon_feature_3d():
    vt = VectorTile()
    layer = vt.add_layer('test')
    # Should not be allowed with version 2 layer
    with pytest.raises(Exception):
        feature = layer.add_polygon_feature(has_elevation=True)
    vt = VectorTile()
    layer = vt.add_layer('test', version=3)
    feature = layer.add_polygon_feature(has_elevation=True)
    assert isinstance(feature, PolygonFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert feature.has_elevation
    polygon = [[[0,0,1],[10,0,1],[10,10,1],[0,10,1],[0,0,1]],[[3,3,1],[3,5,1],[5,5,1],[3,3,1]]]
    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_rings() == polygon
    assert feature.get_polygons() == [polygon]

    bad_ring1 = [[0,0,1],[1,0,1]]
    with pytest.raises(Exception):
        feature.add_ring(bad_ring)
    assert feature.get_polygons() == [polygon]

    bad_ring2 = [[0,0,1],[1,0,1],[0,0,1]]
    with pytest.raises(Exception):
        feature.add_ring(bad_ring2)
    assert feature.get_polygons() == [polygon]

    bad_ring3 = [[0,0,1],[1,0,1],[1,1,1],[1,1],[0,0,1]]
    with pytest.raises(IndexError):
        feature.add_ring(bad_ring3)
    assert feature.get_polygons() == [polygon]

    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_polygons() == [polygon, polygon]

    # clear current geometry
    feature.clear_geometry()
    assert feature.get_rings() == []
    assert feature.get_polygons() == []

    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_rings() == polygon
    assert feature.get_polygons() == [polygon]

    # Now serialize the tile
    data = vt.serialize()
    # Reload as new tile to check that cursor moves to proper position for another add point
    vt = VectorTile(data)
    feature = vt.layers[0].features[0]
    assert feature.get_rings() == polygon
    assert feature.get_polygons() == [polygon]
    feature.add_ring(polygon[0])
    feature.add_ring(polygon[1])
    assert feature.get_polygons() == [polygon, polygon]

def test_create_spline_feature_fail_v2():
    vt = VectorTile()
    layer = vt.add_layer('test')
    with pytest.raises(Exception):
        feature = layer.add_spline_feature()

def test_create_spline_feature():
    vt = VectorTile()
    layer = vt.add_layer('test', version=3)
    feature = layer.add_spline_feature()
    assert isinstance(feature, SplineFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert not feature.has_elevation
    assert feature.degree == 2

    scaling = layer.add_attribute_scaling(precision=10.0**-8, min_value=0.0, max_value=25.0)
    bad_control_points1 = [[8,10]]
    knot_values = [0.0, 0.0, 0.0, 1.0, 2.0, 2.0, 2.0]
    knots = FloatList(scaling, knot_values)
    with pytest.raises(Exception):
        feature.add_spline(bad_control_points1, knots)
    bad_control_points2 = [[8,10],[9,11],[9],[12,10]]
    with pytest.raises(IndexError):
        feature.add_spline(bad_control_points2, knots)

    control_points = [[8,10],[9,11],[11,9],[12,10]]
    feature.add_spline(control_points, knots)

    assert feature.get_splines() == [[control_points, knot_values]]

def test_create_spline_feature_3d():
    vt = VectorTile()
    layer = vt.add_layer('test', version=3)
    feature = layer.add_spline_feature(has_elevation=True)
    assert isinstance(feature, SplineFeature)
    assert len(layer.features) == 1
    assert feature == layer.features[0]
    assert feature.has_elevation
    assert feature.degree == 2

    scaling = layer.add_attribute_scaling(precision=10.0**-8, min_value=0.0, max_value=25.0)
    bad_control_points1 = [[8,10,1]]
    knot_values = [0.0, 0.0, 0.0, 1.0, 2.0, 2.0, 2.0]
    knots = FloatList(scaling, knot_values)
    with pytest.raises(Exception):
        feature.add_spline(bad_control_points1, knots)
    bad_control_points2 = [[8,10,1],[9,11,1],[9,1],[12,10,1]]
    with pytest.raises(IndexError):
        feature.add_spline(bad_control_points2, knots)

    control_points = [[8,10,1],[9,11,1],[11,9,1],[12,10,1]]
    feature.add_spline(control_points, knots)

    assert feature.get_splines() == [[control_points, knot_values]]

def test_create_spline_feature_3d_with_elevation_scaling():
    vt = VectorTile()
    layer = vt.add_layer('test', version=3)

    scaling = layer.add_attribute_scaling(precision=10.0**-8, min_value=0.0, max_value=25.0)
    knot_values = [0.0, 0.0, 0.0, 1.0, 2.0, 2.0, 2.0]
    knots = FloatList(scaling, knot_values)
    control_points = [[8,10,-11000.0],[9,11,9000.0],[11,9,85.1],[12,10,1500.74]]
    
    layer.add_elevation_scaling(precision=10.0**-8, min_value=-11000.0, max_value=9000.0)
    with pytest.raises(Exception):
        feature = layer.add_spline_feature(has_elevation=True)
        feature.add_spline(control_points, knots)
    
    feature = layer.add_spline_feature(has_elevation=True)
    layer.add_elevation_scaling(precision=10.0**-5, min_value=-11000.0, max_value=9000.0)
    feature.add_spline(control_points, knots)

    out = feature.get_splines()
    assert len(out) == 1
    assert len(out[0]) == 2
    out_control_points = out[0][0]
    out_knot_values = out[0][1]
    assert out_knot_values == knot_values
    assert len(control_points) == len(out_control_points)
    for i in range(len(control_points)):
        assert len(control_points[i]) == len(out_control_points[i])
        assert out_control_points[i][0] == control_points[i][0]
        assert out_control_points[i][1] == control_points[i][1]
        assert out_control_points[i][2] == pytest.approx(control_points[i][2])


def test_float():
    x1 = Float(293.045998633665)
    x2 = Float(293.045998634)
    x3 = Float(293.045998633748)
    vm = vector_tile_pb2.Tile.Value()
    vm.float_value = 293.045998633665
    x1_encoded = vm.float_value
    vm.float_value = 293.045998634
    x2_encoded = vm.float_value
    vm.float_value = 293.045998633748
    x3_encoded = vm.float_value
    assert x1 == x2
    assert x1 == x3
    assert x1_encoded == x2_encoded
    assert x1_encoded == x3_encoded
    assert x1 == x1_encoded
    assert x2 == x2_encoded
    assert x3 == x3_encoded
