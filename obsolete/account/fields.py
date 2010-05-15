from django import forms
from django.forms.widgets import TextInput,flatatt
from django.forms.util import smart_unicode

from django.utils.html import escape

class TextWithSuggestionsInput(TextInput):
    def __init__(self, attrs=None, url='', options='{paramName: "text"}'):
        super(TextWithSuggestionsInput, self).__init__(attrs)
        self.url = url
        self.options = options
    
    def render(self, name, value=None, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        if value:
            value = smart_unicode(value)
            final_attrs['value'] = escape(value)
        if not self.attrs.has_key('id'):
                    final_attrs['id'] = 'id_%s' % name
        return (u'<input type="text" name="%(name)s" class="%(name)s_field" id="%(id)s"/>'
                ' <span class="%(name)s_suggestions"></span>') % {'attrs' : flatatt(final_attrs),
                                        'name'	: name,
                                        'id'	: final_attrs['id'],
                                        'url'	: self.url,
                                        'options' : self.options}


