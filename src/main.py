"""
Author: torcellite
Date of Creation: 12/14/2014
"""

import os
import re
import cgi
import json
import time
import jinja2
import urllib
import urllib2
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

"""
Handle the main page requests - /
__init__:
    Initialize a goslate object to retrieve the language list.
get:
    Populate the select list with the retrieved languages.
"""

class MainPage(webapp2.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)
        self.gs = goslate.Goslate()

    def get(self):
        languages = self.gs.get_languages()
        languages = OrderedDict(sorted(languages.items(), key = itemgetter(1)))
        template_values = {
            'languages': languages
        }
        template = JINJA_ENVIRONMENT.get_template('static/index.html')
        self.response.write(template.render(template_values))

"""
Handle the translate page requests - /translate
"""

class Translator(webapp2.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)
        self.request = request
        self.to_lang = None
        self.from_lang = None
        self.translated = None
        self.storelisting = False

    def post(self):
        stringsxml = cgi.escape(self.request.get('stringsxml'))
        self.to_lang = cgi.escape(self.request.get('languages'))
        if 'store-listing' in self.request.POST:
            self.storelisting = True
        translator = Translate(stringsxml, self.storelisting, self.to_lang)
        two_tuple = translator.translate()
        self.translated = two_tuple[0]
        self.from_lang = two_tuple[1]
        template_values = {
            'stringsxml': HTMLParser.HTMLParser().unescape(stringsxml),
            'newstringsxml': HTMLParser.HTMLParser().unescape(self.translated).decode('utf-8'),
            'originallanguage': 'values-' + self.from_lang + '/strings.xml',
            'translatedlanguage': 'values-' + self.to_lang + '/strings.xml'
        }
        template = JINJA_ENVIRONMENT.get_template('static/translate.html')
        self.response.write(template.render(template_values))


class Translate(object):

    """
    @params
    stringsxml: The strings.xml file's contents
    store_listing: Check if the translation is for Store Listing or strings.xml
                   If it is for Store Listing, do not escape single quotes.
    to_lang: The language to be converted to.

    pattern_1: <string name="example"> This is an example </string>
    pattern_2: <string name="example"> This is an example
    pattern_3: This is an example </string>
    pattern_4: This is an example
    pattern_5: <!--exclude-->
    """
    def __init__(self, stringsxml, store_listing = False, to_lang = None):
        self.gs = goslate.Goslate()
        self.stringsxml = stringsxml
        self.to_lang = to_lang
        self.from_lang = None
        self.store_listing = store_listing

        self.strings = []
        self.pattern_1 = '(&lt;[a-zA-Z\s\=\"\-\_\:\.]+&gt;)(.*|\\s*)(&lt;\/[a-zA-Z\s\=\"\-\_\:\.]+&gt;)'
        self.pattern_2 = '(&lt;[a-zA-Z\s\=\"\-\_\:\.]+&gt;)(.*|\\s*)'
        self.pattern_3 = '(.*|\\s*)(&lt;\/[a-zA-Z\s\=\"\-\_\:\.]+&gt;)'
        self.pattern_4 = '(.*|\\s*)'
        self.exclude_pattern = '&lt;!--\s*exclude\s*--&gt;'

    """
    The substitutions are done in order to preserve the '\n' or newline character which appears in strings.xml
    """
    def parse_strings_xml(self):
        strings = self.stringsxml
        strings = re.sub('<', '&lt;', strings)
        strings = re.sub('>', '&gt;', strings)
        strings = re.sub(r'\n', '\r\n', strings) #replace newline with CR, LF
        strings = re.sub(r'\r\n', '(..)', strings) #replace CR, LF so that we know where to create newlines later
        strings = re.sub(r'\\n', '(...)', strings) #replace actual character "\n" to be used in the application
        self.strings = strings.split('(..)') #split it according to the new CR, LF

    """
    Create a list of strings to be translated
    """
    def get_strings_to_translate(self):
        translate_this = []
        for i in range(len(self.strings)):
            translate_this.append(self.detect_pattern_type(self.strings[i]))
        return translate_this

    """
    Detect the pattern of string and split it into the beginning, translate_this and end.
    <string name="example"> --> beginning
    This is an example      --> translate_this
    </string>               --> end
    If none are found, just add an empty line to preserve strings.xml's structure
    """
    def detect_pattern_type(self, string, get_tags = False):
        match = re.search(self.pattern_1, string)
        if match:
            beginning = match.group(1)
            translate_this = match.group(2)
            end = match.group(3)
        else:
            match = re.search(self.pattern_2, string)
            if match:
                beginning = match.group(1)
                translate_this = match.group(2)
                end = ''
            else:
                match = re.search(self.pattern_3, string)
                if match:
                    beginning = ''
                    translate_this = match.group(1)
                    end = match.group(2)
                else:  
                    match = re.search(self.pattern_4, string)
                    if match:
                        beginning = ''
                        translate_this = match.group(1)
                        end = ''
                    else:
                        beginning = ''
                        translate_this = ''
                        end = ''
        if get_tags:
            return [beginning, end]
        else:
            return translate_this

    """
    Detect the from_lang
    Use goslate's translate array to exploit goslate's threading translation
    Detect pattern with tags enabled this time, to retrieve only the tags
    Replace translate_this with the translated text
    Detect the string pattern again to extract the tags
    Reconstruct the strings.xml file with the translated text
    Escape apostrophes if it is for strings.xml and not for store listing
    """
    def translate(self):
        self.parse_strings_xml()
        translate_this = self.get_strings_to_translate()
        self.from_lang = self.gs.detect(translate_this[0])
        translated = []
        newstrings = []
        for i in self.gs.translate(translate_this, self.to_lang):
            translated.append(i)
        for i in range(len(self.strings)):
            match = re.search(self.exclude_pattern, self.strings[i])
            if match:
                newstrings.append(self.strings[i])
            else:
                stringxmltuple = self.detect_pattern_type(self.strings[i], get_tags = True)
                beginning = stringxmltuple[0]
                replacement = translated[i]
                end = stringxmltuple[1]
                replacement = beginning + replacement + end
                newstring = re.sub(self.pattern_1, replacement, self.strings[i])
                newstring = re.sub(self.pattern_2, replacement, self.strings[i])
                newstring = re.sub(self.pattern_3, replacement, self.strings[i])
                newstring = re.sub(self.pattern_4, replacement, self.strings[i])
                newstrings.append(newstring)
        newstringsxml = '\n'.join(newstrings).encode('utf-8')
        newstringsxml = re.sub('&lt;', '<', newstringsxml)
        newstringsxml = re.sub('&gt;', '>', newstringsxml)
        newstringsxml = re.sub(r'\(\.\.\.\)', r'\\n', newstringsxml)
        if not self.store_listing:
                newstringsxml = re.sub(r"'", r"\'", newstringsxml)
        return [newstringsxml, self.from_lang]

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/translate', Translator),
],debug=False)
