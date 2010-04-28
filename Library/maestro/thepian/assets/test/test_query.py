from thepian.assets import Asset

def test_query():
    try:
        raise Asset.NotFound, "Asset not found"
    except Asset.NotFound, e:
        assert type(e) == Asset.NotFound