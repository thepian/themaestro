Project Tree
====================

Several project file structures are supported.

serverbrowser
-------------
The server-browser template is suited for a publishing content heavy Django site.
Source code dependencies are simplistic.
All external python packages should be installed in the virtualenv. Other applications/packages
must be maintained in the server directory.

 ::
project
|
+-- bin
+-- server
+-- browser
+-- mediasite
+-- website
+-- index.text
+-- <text dir>


