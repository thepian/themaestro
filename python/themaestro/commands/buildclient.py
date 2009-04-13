"""thepian rebuild

Gather assets saved in 'assets' directories found in the python source tree; Populating 'images'
and 'embed' subdirectories of 'mediasite'

Generate css and js assets in 'mediasite'

"""
from __future__ import with_statement
import os
import os.path
from fs import listdir, makedirs, walk, copy_tree, symlink
from optparse import make_option
from django.conf import settings
from django import template

from thepian.cmdline import BaseCommand, CommandError
from thepian.conf import structure, dependency
from thepian.utils import *
from thepian.assets import *
from devonly.sources import CssSourceNode,JsSourceNode, combine_asset_sources 
from devonly.assets import sources
from devonly.config.maintenance import create_maintenance

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--parse-templates', action='store_true',
            help='Rebuild assets found by parsing project templates instead of using the tracking database.'),
    )
    help = 'Manage assets (gather).'
    args = '[monitor]'
    requires_model_validation = True

    def handle(self, *args, **options):
        self._generate_assets()
        self._gather_assets()
        self.link_dependencies()
        create_maintenance()
        if len(args) and args[0] == "monitor":
            self._monitor_assets(**options)

    def _gather_assets(self):
        media_target_dir = os.path.join(structure.TARGET_DIR,"mediasite")
        makedirs(media_target_dir)
        for source in sources:
            images_dir = os.path.join(os.path.dirname(source.__file__),'images')
            if os.path.exists(images_dir):
                copy_tree(images_dir,os.path.join(media_target_dir,"images"))
            embed_dir = os.path.join(os.path.dirname(source.__file__),'embed')
            if os.path.exists(embed_dir):
                copy_tree(embed_dir,os.path.join(media_target_dir,"embed"))
            print os.path.dirname(source.__file__)
        print 'Copying application assets ->', media_target_dir
        
    def _generate_assets(self,**options):
        filenames = []
        media_target_dir = os.path.join(structure.TARGET_DIR,"mediasite")
        makedirs(os.path.join(media_target_dir,"css"))
        makedirs(os.path.join(media_target_dir,"js"))
        for d in listdir(structure.CSS_DIR):
            if os.path.splitext(d)[1] == ".css" and os.path.isdir(os.path.join(structure.CSS_DIR,d)):
                filenames.append(d)
                target = os.path.join(structure.MEDIASITE_DIRS[-1],"css",d)
                src = os.path.join(structure.CSS_DIR,d)
            	sources = listdir(src,full_path=True,recursed=True)
                lines = combine_asset_sources(sources,structure.CSS_DIR,source_node=CssSourceNode)	
                with open(os.path.join(media_target_dir, "css", d), 'w') as handle:
                    handle.write(''.join(lines))
                    handle.flush()
        for d in listdir(structure.JS_DIR):
            if os.path.splitext(d)[1] == ".js" and os.path.isdir(os.path.join(structure.JS_DIR,d)):
                filenames.append(d)
                target = os.path.join(structure.MEDIASITE_DIRS[-1],"js",d)
                src = os.path.join(structure.JS_DIR,d)
            	sources = listdir(src,full_path=True,recursed=True)
                lines = combine_asset_sources(sources,structure.JS_DIR,source_node=JsSourceNode)	
                with open(os.path.join(media_target_dir, "js", d), 'w') as handle:
                    handle.write(''.join(lines))
                    handle.flush() 
        print "Generating", ' '.join(filenames), '->', media_target_dir
        
    def link_dependencies(self):
        makedirs(os.path.join(structure.TARGET_DIR,"python"))
        for mod in dependency.MODULE_PATHS:
            python_target = os.path.join(structure.TARGET_DIR,"python",mod)
            symlink(dependency.MODULE_PATHS[mod],python_target)
        print "Linking dependencies", ",".join(dependency.MODULE_PATHS.keys()), "->", os.path.join(structure.TARGET_DIR,"python")
            
    def app_assets_changed(self):
        return False
        
    def templates_changed(self):
        return False
            
    MONITOR = True
    MONITOR_FREQUENCY = 3000
    
    def _monitor_assets(self,**options):
        import time,sys
        while self.MONITOR:
            try:
                if self.app_assets_changed():
                    self._gather_assets()
                if self.templates_changed():
                    self._generate_assets()
                time.sleep(self.MONITOR_FREQUENCY)
            except KeyboardInterrupt:
                print "Done."
                sys.exit(0)
                
