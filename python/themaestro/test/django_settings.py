import sys
def test_settings():
    from thepian.conf import settings, use_settings
    import __testing
    use_settings(__testing)
    
    assert settings.ROOT_URLCONF == '__testing_urls'
    
    print >>sys.stderr, dir(settings)
    print >>sys.stderr,'testing django settings'
    assert settings.__path__, "Settings module not imported yet"  
    
def test_two():
    pass