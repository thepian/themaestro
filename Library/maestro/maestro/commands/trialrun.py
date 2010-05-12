from optparse import make_option, OptionParser

class Command(object):
    
    help = 'Run a trial with tornado'
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
        
        structure.ensure_target_dirs()
        #TODO part add_themaestro functionality

        import logging
        LOG_FILENAME = join(structure.PROJECT_DIR,'testing.log')
        logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
                
        from mediaserver import Application
        import tornado.httpserver
        import tornado.ioloop
        import tornado.autoreload

        # print "js dir =", structure.JS_DIR
        # tornado.options.parse_command_line()
        ioloop = tornado.ioloop.IOLoop.instance()
        http_server = tornado.httpserver.HTTPServer(Application(ioloop=ioloop))
        http_server.listen(8888)
        
        tornado.autoreload.start(io_loop=ioloop)
        ioloop.start()
        #return 'Tornado trial run\n'
