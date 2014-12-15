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

from lib.microsofttranslator import Translator as MicrosoftTranslator

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

client_id = 'client_id'
client_secret = 'client_secret'


"""Get Client ID and Client Secret
"""

class CredentialsPage(webapp2.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)

    def get(self):
        template = JINJA_ENVIRONMENT.get_template('static/index.html')
        template_values = {}
        self.response.write(template.render(template_values))


"""Handle the main page requests - /
__init__:
    Initialize a goslate object to retrieve the language list.
post:
    Populate the select list with the retrieved languages.
"""

class MainPage(webapp2.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)

    def post(self):
        global client_id
        client_id = cgi.escape(self.request.get('client_id'))
        global client_secret
        client_secret = cgi.escape(self.request.get('client_secret'))
        microsofttranslator = MicrosoftTranslator(client_id, client_secret)
        if microsofttranslator.get_access_token() == 400:
            self.response.write('Invalid Client ID or Client Secret, go <a href="http://android-app-translation.appspot.com">back</a> and try again.')
            return
        languages = microsofttranslator.get_languages()
        languages.sort()
        template_values = {
            'languages': languages
        }
        template = JINJA_ENVIRONMENT.get_template('static/main.html')
        self.response.write(template.render(template_values))

"""Handle the translate page requests - /translate
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
        strings_xml = cgi.escape(self.request.get('strings_xml'))
        self.to_lang = cgi.escape(self.request.get('languages'))
        if 'store_listing' in self.request.POST:
            self.storelisting = True
        translator = Translate(strings_xml, self.storelisting, self.to_lang)
        two_tuple = translator.translate()
        if two_tuple[0] == 'error':
            self.response.write('Session has expired, go back to the <a href="http://android-app-translation.appspot.com">main page</a> and enter your credentials again.')
            return
        self.translated = two_tuple[0]
        self.from_lang = two_tuple[1]
        template_values = {
            'strings_xml': HTMLParser.HTMLParser().unescape(strings_xml),
            'new_strings_xml': HTMLParser.HTMLParser().unescape(self.translated).decode('utf-8'),
            'original_language': 'values-' + self.from_lang + '/strings.xml',
            'translated_language': 'values-' + self.to_lang + '/strings.xml'
        }
        template = JINJA_ENVIRONMENT.get_template('static/translate.html')
        self.response.write(template.render(template_values))


class Translate(object):

    """
    @params
    strings_xml: The strings.xml file's contents
    store_listing: Check if the translation is for Store Listing or strings.xml
                   If it is for Store Listing, do not escape single quotes.
    to_lang: The language to be converted to.

    pattern_1: <string name="example"> This is an example </string>
    pattern_2: <string name="example"> This is an example
    pattern_3: This is an example </string>
    pattern_4: This is an example
    pattern_5: <!--exclude-->
    """
    def __init__(self, strings_xml, store_listing = False, to_lang = None):
        self.microsofttranslator = MicrosoftTranslator(client_id, client_secret)
        self.strings_xml = strings_xml
        self.to_lang = to_lang
        self.from_lang = None
        self.store_listing = store_listing

        self.strings = []
        self.pattern_1 = '(&lt;[a-zA-Z\s\=\"\-\_\:\.]+&gt;)(.*|\\s*)(&lt;\/[a-zA-Z\s\=\"\-\_\:\.]+&gt;)'
        self.pattern_2 = '(&lt;[a-zA-Z\s\=\"\-\_\:\.]+&gt;)(.*|\\s*)'
        self.pattern_3 = '(.*|\\s*)(&lt;\/[a-zA-Z\s\=\"\-\_\:\.]+&gt;)'
        self.pattern_4 = '(.*|\\s*)'
        self.exclude_pattern = '&lt;!--\s*exclude\s*--&gt;'

    """    The substitutions are done in order to preserve the '\n' or newline character which appears in strings.xml
    """
    def parse_strings_xml(self):
        strings = self.strings_xml
        strings = re.sub('<', '&lt;', strings)
        strings = re.sub('>', '&gt;', strings)
        strings = re.sub(r'\n', '\r\n', strings) #replace newline with CR, LF
        strings = re.sub(r'\r\n', '(..)', strings) #replace CR, LF so that we know where to create newlines later
        strings = re.sub(r'\\n', '(...)', strings) #replace actual character "\n" to be used in the application
        self.strings = strings.split('(..)') #split it according to the new CR, LF

    """    Create a list of strings to be translated
    """
    def get_strings_to_translate(self):
        translate_this = []
        for i in range(len(self.strings)):
            translate_this.append(self.detect_pattern_type(self.strings[i]))
        return translate_this

    """    Detect the pattern of string and split it into the beginning, translate_this and end.
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

    """    Detect the from_lang
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
        self.from_lang = self.microsofttranslator.detect_language(translate_this[0])
        output = self.microsofttranslator.translate_array(translate_this, self.to_lang)
        translated = []
        try:
            for entry in output:
                translated.append(entry['TranslatedText'])
        except TypeError:
            return ['error', 'Session Expired']
        new_strings = []
        for i in range(len(self.strings)):
            match = re.search(self.exclude_pattern, self.strings[i])
            if match:
                new_strings.append(self.strings[i])
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
                new_strings.append(newstring)
        new_strings_xml = '\n'.join(new_strings).encode('utf-8')
        new_strings_xml = re.sub('&lt;', '<', new_strings_xml)
        new_strings_xml = re.sub('&gt;', '>', new_strings_xml)
        new_strings_xml = re.sub(r'\(\.\.\.\)', r'\\n', new_strings_xml)
        if not self.store_listing:
                new_strings_xml = re.sub(r"'", r"\'", new_strings_xml)
        return [new_strings_xml, self.from_lang]

application = webapp2.WSGIApplication([
    ('/', CredentialsPage),
    ('/main', MainPage),
    ('/translate', Translator),
],debug=False)
