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
        from mediaserver import Application
        import tornado.httpserver
        import tornado.ioloop

        from thepian.conf import structure
        # print "js dir =", structure.JS_DIR
        # tornado.options.parse_command_line()
        http_server = tornado.httpserver.HTTPServer(Application())
        http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()
        return 'Tornado trial run\n'
