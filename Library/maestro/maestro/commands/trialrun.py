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
        import tornado.httpserver
        import tornado.ioloop
        import tornado.web

        class MainHandler(tornado.web.RequestHandler):
            def get(self):
                self.write("Hello, world")

        application = tornado.web.Application([
            (r"/", MainHandler),
        ])

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()
        return 'Tornado trial run\n'
