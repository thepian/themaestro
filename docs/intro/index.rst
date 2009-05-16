Make sure the basic ports are installed

git-core +doc+svn
mercurial

python2.6
py26-ipython
py26-numeric
py26-scientific
py26-docutils
py26-sphinx
#py26-pip
py26-virtualenv
py26-virtualenvwrapper
py26-pil

nginx +dav+flv+google_perftools+gzip_static+ssl+status
memcached
libmemcached

postgresql83
postgresql83-server
postgis


mkdir ~/envs
virtualenv2.6 ~/envs/maestroenv
source ~/envs/maestroenv/bin/activate
./pip.py install -r maestroenv.txt
./pip.py freeze > maestroenv.txt

nosetests --where=python/thepian
