"""
Author: torcellite
Date of Creation: 12/14/2014
"""

import os
import jinja2
import logging
import webapp2

from translate import Translate

from lib.microsofttranslator import Translator as MicrosoftTranslator

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir))),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

client_id = 'client_id'
client_secret = 'client_secret'

debug = False


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
        client_id = self.request.get('client_id')
        global client_secret
        client_secret = self.request.get('client_secret')
        microsofttranslator = MicrosoftTranslator(client_id,
                                                  client_secret,
                                                  debug=debug)
        if microsofttranslator.get_access_token() == 400:
            self.response.write(
                """Invalid Client ID or Client Secret,
                   go <a href="/">back</a> and try again.""")
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
        self.extra_tags = None
        self.store_listing = False

    def post(self):
        strings_xml = self.request.get('strings_xml')
        self.to_lang = self.request.get('languages')
        self.extra_tags = self.request.get('extra_tags').split(',')
        if 'store_listing' in self.request.POST:
            self.store_listing = True
        translator = Translate(client_id=client_id,
                               client_secret=client_secret,
                               xml_string=strings_xml,
                               to_lang=self.to_lang,
                               extra_tags=self.extra_tags,
                               store_listing=self.store_listing,
                               debug=debug)
        two_tuple = translator.translate()
        self.translated = two_tuple[0]
        self.from_lang = two_tuple[1]
        if self.translated == 'session expired':
            self.response.write(
                """Your session has expired,
                   go <a href="/">back</a> and try again.""")
            return
        elif self.translated == 'Expat Error':
            self.response.write(
                'Looks like something is wrong with your XML file.\n' +
                self.from_lang)
        template_values = {
            'strings_xml': strings_xml,
            'new_strings_xml': self.translated.decode('utf-8'),
            'original_language': 'values-' + self.from_lang + '/strings.xml',
            'translated_language': 'values-' + self.to_lang + '/strings.xml'
        }
        template = JINJA_ENVIRONMENT.get_template('static/translate.html')
        self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
    ('/', CredentialsPage),
    ('/main', MainPage),
    ('/translate', Translator),
], debug=debug)
