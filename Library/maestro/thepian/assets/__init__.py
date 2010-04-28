from base import Asset

def resolve_url(asset_or_url,site,type="still",index=0):
    """determine the url for an asset or external url
    type = still|video
    site = current site object
    """
    if isinstance(asset_or_url,basestring):
        if asset_or_url.startswith("http"):
            return asset_or_url
        if asset_or_url.startswith("asset://"):
            asset_or_url = asset_or_url[7:]
        asset = Asset.objects.get(asset_or_url)
    else:
        asset = asset_or_url
    
    if type == "video":
        base = asset.main_bases[0] if len(asset.main_bases) > 0 else asset.image_bases[0]
    else:
        base = asset.image_bases[int(index)]
    return "http://"+ asset.subdomain+site.base_domain+base.path
    
def resolve_asset(asset_or_url):
    """determine the asset
       If an asset is given it is returned, otherwise an asset url is assumed
       """
    from static import Static
    if isinstance(asset_or_url,Static) or isinstance(asset_or_url,Asset): 
        return asset_or_url
    url = str(asset_or_url)
    if url.startswith("asset://"): url = url[7:]
    return Asset.objects.get(url)
    