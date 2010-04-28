from django.http import HttpResponseNotFound
from django.template import Template,Context
from django.conf import settings
from django.utils.encoding import smart_unicode, smart_str

from django.views.debug import get_safe_settings

def technical_404_response(request, exception):
    "Create a technical 404 error response. The exception should be the Http404."
    try:
        tried = exception.args[0]['tried']
    except (IndexError, TypeError):
        tried = []
    else:
        if not tried:
            # tried exists but is an empty list. The URLconf must've been empty.
            return empty_urlconf(request)

    t = Template(TECHNICAL_404_TEMPLATE, name='Technical 404 template')
    c = Context({
        'root_urlconf': settings.ROOT_URLCONF,
        'request_path': request.path_info[1:], # Trim leading slash
        'urlpatterns': tried,
        'reason': smart_str(exception, errors='replace'),
        'request': request,
        'request_protocol': request.is_secure() and "https" or "http",
        'settings': get_safe_settings(),
    })
    return HttpResponseNotFound(t.render(c), mimetype='text/html')

TECHNICAL_404_TEMPLATE = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Page not found at {{ request.path_info|escape }}</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    table { border:none; border-collapse: collapse; width:100%; }
    td, th { vertical-align:top; padding:2px 3px; }
    th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    table.vars { margin:5px 0 2px 40px; }
    table.vars td, table.req td { font-family:monospace; padding-left:2em; }
    table td.code { width:100%; }
    table td.code div { overflow:hidden; }
    #info { background:#f6f6f6; }
    #info ol { margin: 0.5em 4em; }
    #info ol li { font-family: monospace; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
  </style>
</head>
<body>
  <div id="summary">
    <h1>Page not found <span>(404)</span></h1>
    <table class="meta">
      <tr>
        <th>Request Method:</th>
        <td>{{ request.META.REQUEST_METHOD }}</td>
      </tr>
      <tr>
        <th>Request URL:</th>
      <td>{{ request_protocol }}://{{ request.META.HTTP_HOST }}{{ request.path_info|escape }}</td>
      </tr>
    </table>

  </div>
  <div id="info">
    {% if urlpatterns %}
      <p>
      Using the URLconf defined in <code>{{ settings.ROOT_URLCONF }}</code>,
      Django tried these URL patterns, in this order:
      </p>
      <ol>
        {% for pattern in urlpatterns %}
          <li>{{ pattern }}</li>
        {% endfor %}
      </ol>
      <p>The current URL, <code>{{ request_path|escape }}</code>, didn't match any of these.</p>
    {% else %}
      <p>{{ reason }}</p>
    {% endif %}
  </div>

  <h3 id="meta-info">META</h3>
  <table class="req">
    <thead>
      <tr>
        <th>Variable</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      {% for var in request.META.items|dictsort:"0" %}
        <tr>
          <td>{{ var.0 }}</td>
          <td class="code"><div>{{ var.1|pprint }}</div></td>
        </tr>
      {% endfor %}
    </tbody>
  </table>

  <div id="explanation">
    <p>
      You're seeing this error because you have <code>DEBUG = True</code> in
      your Django settings file. Change that to <code>False</code>, and Django
      will display a standard 404 page.
    </p>
  </div>
</body>
</html>
"""