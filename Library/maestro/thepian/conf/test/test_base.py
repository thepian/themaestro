import sys

def test_base_Settings_class():
    from thepian.conf import global_settings
    from thepian.conf.base import Settings
    settings = Settings()
    assert settings.__file__ == None
    for name in dir(global_settings):
        if name == name.upper():
            assert getattr(settings,name) == getattr(global_settings,name)

    from samples import sample_settings
    settings.blend(sample_settings)
    assert settings.ROOT_URLCONF == sample_settings.ROOT_URLCONF
    assert settings.__file__ == sample_settings.__file__
    assert settings.INTERNAL_IPS == (sample_settings.INTERNAL_IPS,)
    
def test_use_settings():
    from thepian.conf import settings, use_settings
    from samples import sample_settings
    use_settings(sample_settings)
    
    assert settings.ROOT_URLCONF == sample_settings.ROOT_URLCONF
    assert settings.__file__ == sample_settings.__file__
    assert settings.INTERNAL_IPS == (sample_settings.INTERNAL_IPS,)
    
    
def test_base_Structure_class():
    from thepian.conf import global_structure
    from thepian.conf.base import Structure
    structure = Structure()
    assert structure.__file__ == None
    
    # All entries in global_structure are found in a new structure
    for name in dir(global_structure):
        if name == name.upper():
            assert getattr(structure,name) == getattr(global_structure,name)
            
    # All entries in global_structure are found after blending in a blank structure module
    from samples import sample_structure
    structure.blend(sample_structure)
    for name in dir(sample_structure):
        if name == name.upper():
            assert getattr(structure,name) == getattr(sample_structure,name)
    assert structure.__file__ == sample_structure.__file__

    # New properties are found after blending in a structure module
    from samples import sample_structure2
    structure.blend(sample_structure2)
    assert structure.BOGUS == sample_structure2.BOGUS
    assert structure.SILLY_TUPLE == sample_structure2.SILLY_TUPLE
    assert structure.__file__ == sample_structure2.__file__

def test_use_structure():
    from thepian.conf import structure, global_structure
