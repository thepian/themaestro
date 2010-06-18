import sys, os, fs
from optparse import make_option, OptionParser

class Command(object):
    
    help = 'Start the services needed to run the site'
    args = '[?]'
    option_list = ()
    
    def get_version(self):
        return 0.1
        
    def create_parser(self, prog_name, subcommand):
        usage = '%%prog %s [options] %s' % (subcommand, self.args)
        usage = '%s\n\n%s' % (usage, self.help)
        return OptionParser(prog=prog_name,
                            usage=usage,
                            version=self.get_version(),
                            option_list=self.option_list)

    def __call__(self,*args,**options):
        from thepian.conf import structure
        from os.path import join
        
        from thepian.conf import ensure_target_tree
        ensure_target_tree(structure.PROJECT_DIR)
        #TODO part add_themaestro functionality

        sys.path.append(structure.PROJECT_DIR)
        
        import logging
        LOG_FILENAME = join(structure.PROJECT_DIR,'testing.log')
        logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
        
        from mediaserver import Application, HTTPServer
        import tornado.httpserver
        import tornado.ioloop
        import tornado.autoreload
        
        ioloop = tornado.ioloop.IOLoop.instance()
        for n in structure.SITES:
            site = structure.SITES[n]
            if site["package"] in ("tornado", "mediaserver"):
                http_server = tornado.httpserver.HTTPServer(Application(site,ioloop=ioloop))
                http_server.listen(site["port"])
        
        tornado.autoreload.start(io_loop=ioloop)
        ioloop.start()
        #return 'Tornado trial run\n'
