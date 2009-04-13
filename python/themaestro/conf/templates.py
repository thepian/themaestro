"""Project configuration templates

The **create** command constructs some configuration files dynamicaly. The templates for these files are found here.
Living in the conf source directory this module is not available to concrete projects.
Templates used by other commands are found in thepian.conf.structure which is backed by thepian.conf.global_structure.
"""

# projectname = name of the project
BUILD_XML = """
<project name="%(projectname)s" basedir="." default="build">
    <dirname property="%(projectname)s.src.home" file="${ant.file}"/>

    <!-- Allow the user to customise the build with their own uniquely named properties file -->
    <property file="${%(projectname)s.src.home}/main/conf/${user.name}.properties"/>

    <property name="build.lib" value="${user.home}/tools/lib"/>
    <property name="django.home" value="/repositories/django"/>
    <property name="config.home" value="$%(projectname)s.src.home}/../../../thepian.config"/>
    
    <echo>Getting jars from ${build.lib}</echo>
    <property name="main.src" value="${%(projectname)s.src.home}/main"/>
    <property name="bin.src" value="${main.src}/bin"/>
    <property name="conf.src" value="${main.src}/conf"/>
    <property name="css.src" value="${main.src}/css"/>
    <property name="js.src" value="${main.src}/js"/>
    <property name="as.src" value="${main.src}/as"/>
    <property name="images.src" value="${main.src}/images"/>
    <property name="java.src" value="${main.src}/java"/>
    <property name="resources.src" value="${main.src}/java-resources"/>
    <property name="python.src" value="${main.src}/python"/>
    <property name="root.src" value="${main.src}/root"/>
    <property name="templates.src" value="${main.src}/templates"/>

    <property name="lib.src" value="${%(projectname)s.src.home}/lib"/>
    <property name="lib.python.src" value="${lib.src}/python"/>

    <property name="extras.src" value="${%(projectname)s.src.home}/extras"/>
    <property name="extras.bin.src" value="${extras.src}/bin"/>
    <property name="extras.conf.src" value="${extras.src}/conf"/>
    <property name="extras.cppunit.src" value="${extras.src}/cppunit"/>
    <property name="extras.junit.src" value="${extras.src}/junit"/>
    <property name="extras.jsunit.src" value="${extras.src}/jsunit"/>
    <property name="extras.spec.src" value="${extras.src}/spec"/>
    <property name="extras.profile.src" value="${extras.src}/profile"/>
    <property name="extras.root.src" value="${extras.src}/root"/>
    <property name="extras.templates.src" value="${extras.src}/templates"/>

    <property name="target" value="${%(projectname)s.src.home}/../target"/>
    <property name="classes" value="${target}/classes"/>
    <property name="test-classes" value="${target}/test-classes"/>
    <property name="website" value="${target}/website"/>
    <property name="mediasite" value="${target}/mediasite"/>
    <property name="js" value="${website}/js"/>
    <property name="css" value="${website}/css"/>
    <property name="swf" value="${website}/swf"/>
    <property name="python" value="${target}/python"/>
	<!-- objects renderings fonts -->
    
    <property name="main.jar" value="%(projectname)s.jar"/>
    <property name="release" value="${%(projectname)s.src.home}/../release"/>
    <property name="bin.release" value="${release}/bin"/>
    <property name="conf.release" value="${release}/conf"/>
    <property name="website.release" value="${release}/website"/>
    <property name="mediasite.release" value="${release}/mediasite"/>
    <property name="classes.release" value="${release}/website/WEB-INF/classes"/>
    <property name="python.release" value="${release}/python"/>
    <property name="dist.release" value="${release}/dist"/>
    <property name="templates.release" value="${release}/templates"/>
    <property name="extras.templates.release" value="${release}/extras/templates"/>
    <property name="extras.website.release" value="${release}/extras/website"/>
    <property name="extras.conf.release" value="${release}/extras/conf"/>

    <property name="stop.port" value="8079"/>
    <property name="stop.key" value="secret"/>
	
    <path id="classpath">
        <fileset dir="${build.lib}" includes="*.jar"/>
    </path>
    <path id="targetclasspath"><pathelement location="${classes}"/></path>

    <mkdir dir="${classes}"/>
    <mkdir dir="${website}"/>
    <mkdir dir="${js}"/>
    <mkdir dir="${css}"/>
    <mkdir dir="${test-classes}"/>
    <mkdir dir="${bin.release}"/>
    <mkdir dir="${website.release}"/>
    <mkdir dir="${mediasite.release}"/>
    <!-- mkdir dir="${classes.release}"/ -->
    <mkdir dir="${python.release}"/>
    <!-- mkdir dir="${dist.release}"/ -->
    <mkdir dir="${templates.release}"/>

    <target name="clean-build" depends="clean, build"/>

    <target name="clean" description="Cleans the result of a previous build">
        <delete dir="${classes}"/>
        <delete dir="${test-classes}"/>
        <delete dir="${website}"/>
    </target>

    <target name="build" description="Builds the js-client project"
            depends="compile, jar"/>

    <target name="release-django" description="Synchronise the django library with version in release directory">
        <!-- Change this to be an update to the python.src? -->
        <sync todir="${python.release}/django"><fileset dir="${django.home}/django"/></sync>
    </target>
    
    <target name="release-thepian" description="Synchronise the thepian library with version in release directory">
        <sync todir="${python.release}/thepian"><fileset dir="${config.home}/python/thepian"/></sync>
    </target>
    
    <target name="release" description="Synchronise the release directories with source/target">
        <exec dir="${%(projectname)s.src.home}" executable="thepian"><arg value="buildclient"/></exec>
        <sync todir="${bin.release}"><fileset dir="${bin.src}"/></sync>
        <sync todir="${conf.release}"><fileset dir="${conf.src}"/></sync>
        <sync todir="${python.release}">
    		<fileset dir="${python.src}"/>
    		<fileset dir="${lib.python.src}"/>
    		<fileset dir="${python}" excludes="*.pth"/>
    	</sync>
        <sync todir="${website.release}">
                <fileset dir="${root.src}"/>
                <fileset dir="${website}"/>
        </sync>
        <sync todir="${mediasite.release}">
                <fileset dir="${root.src}"/>
                <fileset dir="${mediasite}"/>
        </sync>
        <sync todir="${templates.release}"><fileset dir="${templates.src}"/></sync>
        <!-- sync todir="${extras.templates.release}"><fileset dir="${extras.templates.src}"/></sync -->
    
        <exec executable="git" dir="../release"><arg value="add"/><arg value="."/></exec>
        <exec command="git" dir="../release"><arg value="commit"/><arg value="-m release"/></exec>
    </target>	

    <target name="compile" depends="compile.java, compile.js, compile.css">
    </target>
            
    <target name="compile.java" description="Compiles Java sources" 
            unless="skip.compile">
        <mkdir dir="${classes}" />
        <javac srcdir="${java.src}" destdir="${classes}" debug="true" classpathref="classpath" />
    	<copy todir="${classes}">
    		<fileset dir="${resources.src}"><include name="**/*.*"/></fileset>
    	</copy>
    </target>
	
    <target name="compile.js">
		<jspackage src="${js.src}" dest="${js}" force="true"/>
    	<!--
    	<jspackage src="${src.js}" dest="${wardir.js}" minify="${minify}" progressive="${progressive}" debug="${debug}" descpath="${descpath}" labelfunctions="${labelfunctions}"/>
    	-->
    </target>

    <target name="compile.css">
    	<csspackage src="${css.src}" dest="${css}" force="true" />
    	<!--
        <fileconcat src="${src.css}" dest="${wardir.css}" extension="css" markup="${debug}"/>
        -->
    </target>

    <target name="jar" depends="compile">
            <jar destfile="${dist.release}/${main.jar}">
                    <fileset dir="${classes}">
                        <include name="**/*.class"/>
                    </fileset>
                    <fileset dir="${resources.src}">
                    </fileset>
            </jar>
    </target>

    <macrodef name="extras-start">
        <attribute name="arg1" default=""/>
        <attribute name="arg2" default=""/>
        <attribute name="jvmarg1" default=""/>
        <attribute name="jvmarg2" default=""/>
        <sequential>
            <exec executable="java">
                    <arg value="-cp target/jsspec-extras.jar;lib/jetty-6.1.7.jar;lib/jetty-util-6.1.7.jar;lib/servlet-api-2.5-6.1.7.jar"/>
                    <arg value="-Dfile.encoding=UTF-8" />
                    <arg value="-DSTOP.PORT=8079"/>
                    <arg value="-DSTOP.KEY=secret"/>
                    <arg value="jsspec.extras.Main"/>
                    <arg value="@{arg1}"/>
            </exec>
        </sequential>
    </macrodef>

    <target name="extras-start" depends="extras.stop">
            <extras-start arg1="src/main/jetty-extras.xml" jvmarg1="-DDEBUG"/>
    </target>
    
    <target name="extras-check-status">
        <condition property="extras.started">
            <socket server="localhost" port="9080"/>
        </condition>
    </target>
    
    <taskdef resource="tasks.properties" classpathref="classpath"/>
    
    <target name="extras.stop" depends="extras-check-status" if="extras.started">
            <stopextras port="${stop.port}" key="${stop.key}"/>
        <sleep seconds="2"/>
    </target>
</project>
"""

TOOLS_PTH = """
../../../../tools/cssutils
../../../../thepian.config/python
"""

DJANGO_APPS_PTH = """
/repositories/django-apps/django-tagging
/repositories/django-apps/django-feedutil
/repositories/django-apps/django-mailer
/repositories/django-apps/django-threadedcomments
/repositories/django-apps/django-openid
/repositories/django-apps/django-rendertext
"""

WORK_SINGLE_CONFIG = """
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
	ignorecase = true
    #excludesfile = /Users/henrikvendelbo/.gitignore
    #pager = "/opt/local/bin/less -RciqMSj5"
    #editor = mate -w
	
[remote "origin"]
	url = /repositories/%(projectname)s/src
	fetch = +refs/heads/*:refs/remotes/origin/*

[remote "sources"]
	url = ssh://hvendelbo@192.168.9.94/repositories/%(projectname)s
	fetch = +refs/heads/*:refs/remotes/sources/*

[remote "imac"]
	url = ssh://hvendelbo@192.168.9.94/Users/hvendelbo/Sites/%(projectname)s
	fetch = +refs/heads/*:refs/remotes/imac/*

[remote "macbook"]
	url = ssh://henrikvendelbo@192.168.9.93/Users/henrikvendelbo/Sites/%(projectname)s
	fetch = +refs/heads/*:refs/remotes/macbook/*

[branch "master"]
	remote = origin
	merge = refs/heads/master
"""

WORK_SRC_CONFIG = """
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
	ignorecase = true
	
[remote "origin"]
	url = /repositories/%(projectname)s/src
	fetch = +refs/heads/*:refs/remotes/origin/*

[remote "sources"]
	url = ssh://hvendelbo@192.168.9.94/repositories/%(projectname)s/src
	fetch = +refs/heads/*:refs/remotes/sources/*

[remote "imac"]
	url = ssh://hvendelbo@192.168.9.94/Users/hvendelbo/Sites/%(projectname)s/src
	fetch = +refs/heads/*:refs/remotes/imac/*

[remote "macbook"]
	url = ssh://henrikvendelbo@192.168.9.93/Users/henrikvendelbo/Sites/%(projectname)s/src
	fetch = +refs/heads/*:refs/remotes/macbook/*

[branch "master"]
	remote = origin
	merge = refs/heads/master
"""

WORK_RELEASE_CONFIG = """
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
	ignorecase = true
	
[remote "origin"]
	url = /repositories/%(projectname)s/release
	fetch = +refs/heads/*:refs/remotes/origin/*

[remote "sources"]
	url = ssh://hvendelbo@192.168.9.94/repositories/%(projectname)s/release
	fetch = +refs/heads/*:refs/remotes/sources/*

[remote "imac"]
	url = ssh://hvendelbo@192.168.9.94/Users/hvendelbo/Sites/%(projectname)s/release
	fetch = +refs/heads/*:refs/remotes/imac/*

[remote "macbook"]
	url = ssh://henrikvendelbo@192.168.9.93/Users/henrikvendelbo/Sites/%(projectname)s/release
	fetch = +refs/heads/*:refs/remotes/macbook/*
	
[remote "s1"]
	url = ssh://thepian@s1.thepia.net/Sites/%(projectname)s
	fetch = +refs/heads/*:refs/remotes/s1/*
[remote "s2"]
	url = ssh://thepian@s2.thepia.net/Sites/%(projectname)s
	fetch = +refs/heads/*:refs/remotes/s2/*
[remote "s3"]
	url = ssh://thepian@s3.thepia.net/Sites/%(projectname)s
	fetch = +refs/heads/*:refs/remotes/s3/*


[branch "master"]
	remote = origin
	merge = refs/heads/master
"""

SINGLE_IGNORE = """
.Python
bin/activate
bin/activate_this.py
bin/buildout
bin/easy_install
bin/easy_install-2.5
bin/easy_install-2.6
bin/python
bin/python2.5
bin/python2.6
bin/csscapture
bin/csscombine
bin/cssparse
bin/ipcluster
bin/ipcontroller
bin/ipengine
bin/iptest
bin/ipython
bin/ipythonx
bin/nosetests
bin/pycolor
*.pyc
*.tmproj
.svn
.DS_Store
*.egg-info
develop-eggs/
eggs/
include/python2.6
lib/python2.6
parts/
target/
release/
"""

SRC_IGNORE = """
*.pyc
*.tmproj
.svn
.DS_Store
"""


RELEASE_IGNORE = """
*.pyc
.svn
.DS_Store
"""

NGINX_FUTURE = """

worker_processes 5;

events { worker_connections 1024; }

http {

location / {
         if ($request_method = POST) {
                 proxy_pass http://localhost:9004;
                 break;
         }
         default_type  "text/html; charset=utf-8";
         set $memcached_key "/your-site-name-$uri";
         memcached_pass localhost:11211;
         error_page 404 502 = /django;
 }

 location = /django  {
         proxy_pass http://localhost:9004;
         break;
 }


  include /usr/local/etc/nginx/mime.types;

  default_type application/octet-stream;

  sendfile on;

  upstream mongrel {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
  }

  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header Host $http_host;
  proxy_redirect false;
  
  server {
      listen 80 default rcvbuf=64k backlog=128;
      server_name _ *;
      location / {
          return 500;
      }
  }

  server {
    listen 80;
    server_name site1.com www.site1.com;
    root /usr/local/www/site1/public;
    location / { error_page 404 /404.html = @fallback; }
    location @fallback {
      proxy_pass http://mongrel;
      recursive_error_pages on;
      error_page 500 /500.html;
    }
  }

  server {
    listen 80;
    server_name site2.no www.site2.no;
    root /usr/local/www/site2/public;
    location / { error_page 404 /404.html = @fallback; }
    location @fallback {
      proxy_pass http://mongrel;
      recursive_error_pages on;
      error_page 500 /500.html;
    }
  }
}
"""

"""
domains        Names from structure.CLUSTERS[n].public prefixed by proper subdomain
base_domains   Names from structure.CLUSTERS[n].public
star_domains   Names from structure.CLUSTERS[n].public prefixed by a star
log_dir             Path to log directory for the domain
shard               subdomain name
website_one         root (for release, website)
website_two         target/website (for release, website)
mediasite_one       root (for release, mediasite)
mediasite_two       target/mediasite (for release, mediasite)
downloads_dir        
"""

# nginx config files
NGINX_WWW_SERVER_SECTION = """
server {
    listen 127.0.0.1:80;
    server_name %(domains)s %(base_domains)s;
    access_log  %(log_dir)s/www.access.log main;
    
    location /favicon.ico {
        root %(website_one)s;
        if (!-f $request_filename) { root %(website_two)s; }
    }
    
    location / {
        %(upstream)s
    }
    
    set $slow 1;
    if ($slow) {
        set $limit_rate 10k;
    }
}
"""

NGINX_SHARD_SERVER_SECTION = """
server {
    listen 127.0.0.1:80;
    server_name %(domains)s;
    access_log  %(log_dir)s/%(shard)s.access.log main;
    set $limit_rate  50k;
    
    location /favicon.ico {
        root %(website_one)s;
        if (!-f $request_filename) { root %(website_two)s; }
    }
    location / {
        %(upstream_headers)s
        if ($request_method != GET) {
            %(upstream_pass)s
            break;
        }
        root %(downloads_dir)s;
        error_page 403 404 502 = /fallback$uri;
    }
    location /downloads/ {
        internal;
        alias %(downloads_dir)s;
    }
    location /fallback {
        %(upstream)s
    }
}
"""

NGINX_MEDIA_SERVER_SECTION = """
server {
    listen 127.0.0.1:80;
    server_name %(domains)s;
    access_log  off;
    # access_log  %(log_dir)s/media.access.log main;
    
    location / {
        #autoindex on;
        valid_referers  none  blocked %(star_domains)s %(base_domains)s;
        if ($invalid_referer) {
            return 403;
        }
        root %(mediasite_one)s;
        if (!-f $request_filename) {
            root %(mediasite_two)s;
        }
        error_page 404 502 = /fallback$uri;
    }
    location /fallback {
        internal;
        %(upstream)s
    }
}
"""

NGINX_SERVER_SECTIONS = {
    'www': NGINX_WWW_SERVER_SECTION,
    'media': NGINX_MEDIA_SERVER_SECTION,
    'shard': NGINX_SHARD_SERVER_SECTION
}

NGINX_WWW_HTTP_ROOT = """
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header Country $country;
        proxy_redirect false;
        proxy_pass http://127.0.0.1:%(port)s;
"""

NGINX_WWW_HTTP_HEADERS = """
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header Country $country;
        proxy_redirect false;
"""
NGINX_WWW_HTTP_PASS = """proxy_pass http://127.0.0.1:%(port)s;"""

NGINX_WWW_FCGI_ROOT = """
        #fastcgi_pass   unix:%(socket)s;
        fastcgi_pass    localhost:%(port)s;
        fastcgi_read_timeout    5m;
        
        fastcgi_param   COUNTRY $country;
        include /etc/nginx/fastcgi.conf;
"""
NGINX_WWW_FCGI_HEADERS = """
        fastcgi_read_timeout    5m;

        fastcgi_param   COUNTRY $country;
        include /etc/nginx/fastcgi.conf;
"""
NGINX_WWW_FCGI_PASS = """fastcgi_pass    localhost:%(port)s;"""

NGINX_WWW_UPSTREAM = {
    'http': NGINX_WWW_HTTP_ROOT,
    'fastcgi': NGINX_WWW_FCGI_ROOT
}
NGINX_WWW_HEADERS = {
    'http': NGINX_WWW_HTTP_HEADERS,
    'fastcgi': NGINX_WWW_FCGI_HEADERS,
}
NGINX_WWW_PASS = {
    'http': NGINX_WWW_HTTP_PASS,
    'fastcgi': NGINX_WWW_FCGI_PASS,
}

NGINX_WWW_XXX_ROOT = """
        root /somewhere
        
        # If the file exists as a static file serve it directly without
        # running all the other rewite tests on it
        if (-f $request_filename) { 
          break; 
        }

      # check for index.html for directory index
      # if its there on the filesystem then rewite 
      # the url to add /index.html to the end of it
      # and then break to send it to the next config rules.
      if (-f $request_filename/index.html) {
        rewrite (.*) $1/index.html break;
      }

      # this is the meat of the rails page caching config
      # it adds .html to the end of the url and then checks
      # the filesystem for that file. If it exists, then we
      # rewite the url to have explicit .html on the end 
      # and then send it on its way to the next config rule.
      # if there is no file on the fs then it sets all the 
      # necessary headers and proxies to our upstream mongrels
      if (-f $request_filename.html) {
        rewrite (.*) $1.html break;
      }

      if (!-f $request_filename) {
        fastcgi_pass unix:%(socket)s;
        break;
      }
"""

NGINX_LOGROTATE_ACCESS_LOG = """

/var/log/%(domain)s/%(sub)s.access.log {
    daily
    rotate 90
    #copytruncate
    postrotate
             [! -f /var/run/nginx.pid] || kill -USR1 `cat /var/run/nginx.pid`
             sleep 0.5
    endscript
    #mail testin3@gmail.com
    #mailfirst
    compress
    notifempty
    missingok
}
"""


