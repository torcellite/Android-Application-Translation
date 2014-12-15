# -*- coding: utf-8 -*-

"""
A big shoutout to openlabs for this wonderful script.

This script is a modified version of the original.
It was done so that no external libraries needed to be used to be deployed onto GAE.

The original script can be found here -
     https://github.com/openlabs/Microsoft-Translator-Python-API

Changes: 
*Removed warnings and exception classes to get rid of the module `six`
*Removed requests and replaced it with urllib, urllib2
*Added detect_language
*Added get_languages

Editor: torcellite
DoC: 12/15/2014
"""


"""
    __init__

    A translator using the micrsoft translation engine documented here:

    http://msdn.microsoft.com/en-us/library/ff512419.aspx

    :copyright: © 2011 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""

import json
import urllib
import urllib2

from xml.dom import minidom
from urllib2 import HTTPError

class Translator(object):
    """Implements AJAX API for the Microsoft Translator service

    :param app_id: A string containing the Bing AppID. (Deprecated)
    """

    def __init__(self, client_id, client_secret,
            scope="http://api.microsofttranslator.com",
            grant_type="client_credentials", app_id=None, debug=False):
        """


        :param client_id: The client ID that you specified when you registered
                          your application with Azure DataMarket.
        :param client_secret: The client secret value that you obtained when
                              you registered your application with Azure
                              DataMarket.
        :param scope: Defaults to http://api.microsofttranslator.com
        ;param grant_type: Defaults to "client_credentials"
        :param app_id: Deprecated

        .. versionchanged: 0.4
            Bing AppID mechanism is deprecated and is no longer supported.
            See: http://msdn.microsoft.com/en-us/library/hh454950
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.grant_type = grant_type
        self.access_token = None
        self.debug = debug

    def get_access_token(self):
        """Bing AppID mechanism is deprecated and is no longer supported.
        As mentioned above, you must obtain an access token to use the
        Microsoft Translator API. The access token is more secure, OAuth
        standard compliant, and more flexible. Users who are using Bing AppID
        are strongly recommended to get an access token as soon as possible.

        .. note::
            The value of access token can be used for subsequent calls to the
            Microsoft Translator API. The access token expires after 10
            minutes. It is always better to check elapsed time between time at
            which token issued and current time. If elapsed time exceeds 10
            minute time period renew access token by following obtaining
            access token procedure.

        :return: The access token to be used with subsequent requests
        """
        args = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope,
            'grant_type': self.grant_type
        }
        
        data = urllib.urlencode(args)
        request = urllib2.Request('https://datamarket.accesscontrol.windows.net/v2/OAuth2-13', data)

        try:
            response = urllib2.urlopen(request)
        except HTTPError:
            return 400

        response = json.load(response)
        return response['access_token']

    def call(self, url, params):
        """Calls the given url with the params urlencoded.
        Encode data within the URL itself, since urllib2 makes a POST request if Request is used.
        """
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        url_values = urllib.urlencode(params)
        full_url =  url + '?' + url_values
        request = urllib2.Request(full_url, headers={'Authorization': 'Bearer %s' % self.access_token})
        response = urllib2.urlopen(request)
        response = response.read().decode('UTF-8-sig')
        
        rv = json.loads(response)
        return rv

    def get_languages(self):
        """Fetches the languages supported by Microsoft Translator
        Returns list of languages
        """
        if not self.access_token:
            self.access_token = self.get_access_token()

        request = urllib2.Request(
            'http://api.microsofttranslator.com/V2/Http.svc/GetLanguagesForTranslate',
            headers={'Authorization': 'Bearer %s' % self.access_token})
        response = urllib2.urlopen(request)

        languages = []
        xml = minidom.parseString(response.read().decode('UTF-8-sig'))
        array = xml.firstChild
        for childNode in array.childNodes:
            languages.append(childNode.firstChild.nodeValue)
        [language.encode('UTF-8') for language in languages]
        return languages

    def detect_language(self, text):
        """Detects language of given string
        Returns two letter language - Example : fr
        """
        if not self.access_token:
            self.access_token = self.get_access_token()

        params = {'text' : text}
        url = 'http://api.microsofttranslator.com/V2/Ajax.svc/Detect'
        url_values = urllib.urlencode(params)
        full_url =  url + '?' + url_values

        request = urllib2.Request(
            full_url,
            headers={'Authorization': 'Bearer %s' % self.access_token})
        response = urllib2.urlopen(request)

        response = response.read().decode('UTF-8-sig')
        language = response.split('\n')
        language = [l for l in language if l is not None]
        return language[0].encode('UTF-8')[1:-1]


    def translate(self, text, to_lang, from_lang=None,
            content_type='text/plain', category='general'):
        """Translates a text string from one language to another.

        :param text: A string representing the text to translate.
        :param to_lang: A string representing the language code to
            translate the text into.
        :param from_lang: A string representing the language code of the
            translation text. If left None the response will include the
            result of language auto-detection. (Default: None)
        :param content_type: The format of the text being translated.
            The supported formats are "text/plain" and "text/html". Any HTML
            needs to be well-formed.
        :param category: The category of the text to translate. The only
            supported category is "general".
        """
        [t.encode('UTF-8') for t in text]
        params = {
            'text': text,
            'to': to_lang,
            'contentType': content_type,
            'category': category,
        }
        if from_lang is not None:
            params['from'] = from_lang
        return self.call(
            "http://api.microsofttranslator.com/V2/Ajax.svc/Translate",
            params)

    def translate_array(self, texts, to_lang, from_lang=None, **options):
        """Translates an array of text strings from one language to another.

        :param texts: A list containing texts for translation.
        :param to_lang: A string representing the language code to
            translate the text into.
        :param from_lang: A string representing the language code of the
            translation text. If left None the response will include the
            result of language auto-detection. (Default: None)
        :param options: A TranslateOptions element containing the values below.
            They are all optional and default to the most common settings.

                Category: A string containing the category (domain) of the
                    translation. Defaults to "general".
                ContentType: The format of the text being translated. The
                    supported formats are "text/plain" and "text/html". Any
                    HTML needs to be well-formed.
                Uri: A string containing the content location of this
                    translation.
                User: A string used to track the originator of the submission.
                State: User state to help correlate request and response. The
                    same contents will be returned in the response.
        """
        options = {
            'Category': "general",
            'Contenttype': "text/plain",
            'Uri': '',
            'User': 'default',
            'State': ''
        }.update(options)
        params = {
            'texts': json.dumps(texts),
            'to': to_lang,
            'options': json.dumps(options),
        }
        if from_lang is not None:
            params['from'] = from_lang

        return self.call(
                "http://api.microsofttranslator.com/V2/Ajax.svc/TranslateArray",
                params)