from __future__ import with_statement
import sys, os, fs
from optparse import make_option, OptionParser

class Command(object):
    
    help = 'Create a local HTML file for account/project'
    args = 'account/project'
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
        
        import tornado.template

        account = "essentialjs"
        project = "pagespec"        

        if "api" in structure.SITES:
            api = structure.SITES["api"]
            loader = tornado.template.Loader(join(structure.PROJECT_DIR,"templates"))
            with open(join(structure.PROJECT_DIR,"start-here.html"),"w") as f:
                f.write(loader.load("pagespec/local-suite-page.html").generate(api_base="http://localhost:%s/%s/%s/%s" % (api["port"],account,project,"all")))
                print "start-here.html generated."
        else:
            print "No API site defined, local suite page skipped."