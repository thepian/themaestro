from __future__ import absolute_import
from os.path import expanduser,join,exists
from fs import makedirs, copy_file, listdir, filters
from thepian.conf import structure
import os
from subprocess import Popen, PIPE

def ensure_presets():
    home = expanduser("~/.ffmpeg")
    makedirs(home)
    presets = listdir(structure.CONF_DIR,filters=(filters.no_hidden,filters.no_system,filters.fnmatch("*.ffpreset")))
    for preset in presets:
        copy_file(src=join(structure.CONF_DIR,preset),dst=join(home,preset))
        
def convert_h264(src,dst,width,height):
    # ffmpeg -y -i $1 -pass 2 -b 512k -bt 512k -s 320x240 -vcodec libx264 -an -f mp4 /dev/null
    # ffmpeg -y -i $1 -pass 2 -b 512k -bt 512k -s 320x240 -vcodec libx264 -acodec libfaac -ab 96k -ac 2 -f mp4 $2
    
    ff_cmd = ' '.join((
        'ffmpeg -y -i "%s"' % src,
        '-pass 1 -vcodec libx264 -an -vpre pass1 -b 512k -bt 512k -threads 0',
        '-s %dx%d' % (width,height),
        '-f mp4 /dev/null',
        '&&',
        'ffmpeg -y -i "%s"' % src,
        '-pass 2 -vcodec libx264 -acodec libfaac -vpre pass2 -b 512k -bt 512k -threads 0',
        '-s %dx%d' % (width,height),
        '-f mp4 "%s"' % dst
    ))
    ffmpegp = Popen(ff_cmd,shell=True)
    sts = os.waitpid(ffmpegp.pid,0)
    
     