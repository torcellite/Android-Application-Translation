import os
import re
import cgi
import json
import time
import jinja2
import urllib
import urllib2
import logging
import webapp2
import HTMLParser
import lib.goslate as goslate

from operator import itemgetter
from collections import OrderedDict

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainPage(webapp2.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)

    def get(self):
        gs = goslate.Goslate()
        languages = gs.get_languages()
        languages = OrderedDict(sorted(languages.items(), key=itemgetter(1)))
        template_values = {
            'languages': languages
        }
        template = JINJA_ENVIRONMENT.get_template('static/index.html')
        self.response.write(template.render(template_values))

class Translator(webapp2.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)
        self.to_lang = None
        self.from_lang = None
        self.translated = None

    def post(self):
        stringsxml = cgi.escape(self.request.get('stringsxml'))
        self.to_lang = cgi.escape(self.request.get('languages'))
        self.translated = self.translate(stringsxml)
        template_values = {
            'stringsxml': HTMLParser.HTMLParser().unescape(stringsxml),
            'newstringsxml': HTMLParser.HTMLParser().unescape(self.translated),
            'originallanguage': 'strings-' + self.from_lang + '.xml',
            'translatedlanguage': 'strings-' + self.to_lang + '.xml'
        }
        template = JINJA_ENVIRONMENT.get_template('static/translate.html')
        self.response.write(template.render(template_values))

    def translate(self, stringsxml):
        strings = stringsxml.split('\n')
        pattern = '(&lt;.+&gt;)(.*|\\s*)(&lt;/.+&gt;)'
        #Exclude strings with the comment <!--exclude--> between the <string> or <item> tags
        exclude_pattern = '&lt;!--\s*exclude\s*--&gt;' 
        gs = goslate.Goslate()
        translate_this = []
        for i in range(len(strings)):
            match = re.search(pattern, strings[i])
            if match:
                translate_this.append(match.group(2))
            else:
                translate_this.append('')
        translated = []
        for i in gs.translate(translate_this, self.to_lang):
            translated.append(i)
        self.from_lang = gs.detect(translated[0])            
        for i in range(len(strings)):
            match = re.search(exclude_pattern, strings[i])
            if match:
              continue
            else:
              match = re.search(pattern, strings[i])
              if match:
                beginning = match.group(1)
                end = match.group(3)
                replacement = beginning + translated[i] + end
                strings[i] = re.sub(pattern, replacement, strings[i])
        newstringsxml = ''.join(strings)
        return newstringsxml

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/translate', Translator),
],debug=False)
