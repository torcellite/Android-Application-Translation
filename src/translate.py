"""
Author: torcellite
Date of Creation: 12/16/2014
"""
import re
import json
import xml.dom.minidom

from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from lib.microsofttranslator import Translator as MicrosoftTranslator


class Translate(object):

    """
    @params
    xml_string: The strings.xml file's contents
    store_listing: Check if the translation is for Store Listing or strings.xml
                   If it is for Store Listing, do not escape single quotes.
    to_lang: The language to be converted to.

    XML Elements with the "exclude" attribute will be ignored for translation

    Only <string> and <item> elements will be translated by default
    """
    def __init__(self, client_id, client_secret,
                 xml_string, to_lang='en', extra_tags=None,
                 store_listing=False, debug=False):
        self.microsofttranslator = MicrosoftTranslator(client_id,
                                                       client_secret,
                                                       debug=debug)
        self.xml_string = xml_string
        self.to_lang = to_lang
        self.from_lang = None
        self.extra_tags = extra_tags
        self.store_listing = store_listing

        self.exclude_attr = 'exclude'
        self.literal_newline_replacement = ';###;'

    """The substitutions are done in order to preserve the '\n'
       or newline character which appears in strings.xml
       restore=False: before translation
       restore=True: after translation
    """
    def preserve_literal_newline(self, restore=False):
        strings = self.xml_string
        if not restore:
            strings = re.sub(r'\\n', self.literal_newline_replacement, strings)
        else:
            strings = re.sub(self.literal_newline_replacement, r'\\n', strings)
        self.xml_string = strings

    """Translate the string, item and other elements respectively.
    """
    def translate(self):
        try:
            self.xml = parseString(self.xml_string)
        except xml.parsers.expat.ExpatError as err:
            return ['ExpatError', err.errno + ' ' + err.strerror]
        self.preserve_literal_newline()
        to_translate_list = []
        tags = ['string', 'item']
        is_tag_translated = []
        if self.extra_tags is not None:
            # Remove in case the user enters string and item anyway.
            if 'string' in self.extra_tags:
                self.extra_tags.remove('string')
            if 'item' in self.extra_tags:
                self.extra_tags.remove('item')
            tags = tags + self.extra_tags
        for tag in tags:
            for tag_element in self.xml.getElementsByTagName(tag):
                exclude = False
                for attr_tuple in tag_element.attributes.items():
                    if self.exclude_attr in attr_tuple:
                        exclude = True
                        is_tag_translated.append(False)
                if not exclude:
                    to_translate_list.append(tag_element.firstChild.data)
                    is_tag_translated.append(True)
        translated = self.translate_array(to_translate_list)
        if translated == 'session expired':
            return ['session expired', '']
        index_tag = 0
        index_translated = 0
        for tag in tags:
            for tag_element in self.xml.getElementsByTagName(tag):
                if is_tag_translated[index_tag]:
                    tag_element.firstChild.data = translated[index_translated]
                    index_translated = index_translated + 1
                index_tag = index_tag + 1
        self.xml = self.xml.toxml().encode('utf-8')
        self.from_lang = self.microsofttranslator.detect_language(
            to_translate_list[0])
        self.preserve_literal_newline(True)
        if not self.store_listing:
                new_strings_xml = re.sub(r"'", r"\'", self.xml)
        return [self.xml, self.from_lang]

    """Split the array into smaller chunks to avoid InvalidURL Error
    """
    def translate_array(self, to_translate_list):
        chunk_size = 10
        translate_chunks = list(self.chunks(to_translate_list,
                                            chunk_size))
        self.from_lang = self.microsofttranslator.detect_language(
            translate_chunks[0][0])
        translated = []
        for chunk in translate_chunks:
            output = self.microsofttranslator.translate_array(chunk,
                                                              self.to_lang)
            try:
                for entry in output:
                    translated.append(entry['TranslatedText'])
            except TypeError:
                return "session expired"
        return translated

    """ Yield successive n-sized chunks from list l.
    """
    def chunks(self, l, n):
        for i in xrange(0, len(l), n):
            yield l[i:i+n]
