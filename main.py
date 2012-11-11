import os, sys
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

from hashlib import sha1
import hmac, binascii, urllib,logging, time, string, random
from xml.etree import ElementTree as ET

def OAuthEscape( s ):
   return urllib.quote( s.encode('utf-8'), '' )

def RandomString( size=6, chars=string.ascii_uppercase + string.digits ):
   return ''.join( random.choice(chars) for x in range(size) )

def GenerateSig( url, key, nonce, time_stamp, expand_parms, term ):
   sig = 'GET&' + OAuthEscape( url ) + '&'

   parameters = ''.join([
      'expand=' + OAuthEscape(expand_parms),
      '&max_results=1',
      '&oauth_consumer_key=' + key,
      '&oauth_nonce=' + nonce,
      '&oauth_signature_method=HMAC-SHA1',
      '&oauth_timestamp=' + time_stamp,
      '&oauth_version=1.0',
      '&term=' + term ])

   sig = sig + OAuthEscape(parameters)

   # Get secret from data file
   FILE = open('templates/data.txt', 'r')
   net_secret = FILE.readline().strip()

   secret =  net_secret + '&'
   hashed = hmac.new(secret, sig, sha1)

   safe_sig = binascii.b2a_base64(hashed.digest())[:-1]

   return safe_sig

class Entry:
   title = ''
   movie_art = ''
   release_year = ''
   runtime = ''
   avg_rating = '' 
   episodes = '' 
   formats = '' 
   synopsis = ''
   genre = ''

def GetAutocompleteSearchTitles( search_string ):
      auto_url = "http://api-public.netflix.com/catalog/titles/autocomplete"
      key = "adqe4ngafwj8ybwvnfgbnuta"

      auto_parameters = [
         ('term', search_string),
         ('oauth_consumer_key', key)]

      full_auto_url = auto_url + '?' + urllib.urlencode(auto_parameters)

      # Read autocomplete url and convert to XML
      auto_data = urlfetch.fetch(full_auto_url, deadline=10).content
      auto_xml = ET.fromstring(auto_data)

      # Logging DEBUG
      logging.info(auto_data)

      # auto_names holds the titles returned by autocomplete search
      auto_names = []

      # Grab all titles from autocomplete search
      for i in auto_xml.findall('.//title'):
         n = i.attrib.get('short')
         auto_names.append(n)

      return auto_names

def GetCatalogTitles( auto_names ):
   url = 'http://api-public.netflix.com/catalog/titles'
   key = "adqe4ngafwj8ybwvnfgbnuta"

   expand_parms = 'synopsis,cast,formats,@episodes,@seasons'
   nonce = RandomString()
   time_stamp = str( int(time.time()) )

   # Entries is a list of entry objects
   Entries = []

   MAX_RESULTS = 10 if len(auto_names) > 10 else len(auto_names)

   # Perform catalog search on autocomplete titles
   for i in range( MAX_RESULTS ):
      entry = Entry()

      term = auto_names[i]

      sign = GenerateSig( url, key, nonce, time_stamp, expand_parms, OAuthEscape(term) )

      parameters = [
         ('expand', expand_parms),
         ('max_results', '1'),
         ('oauth_consumer_key', key),
         ('oauth_nonce', nonce),
         ('oauth_signature', sign),
         ('oauth_signature_method', 'HMAC-SHA1'),
         ('oauth_timestamp', time_stamp),
         ('oauth_version', '1.0'),
         ('term', term)]

      full_url = url + '?' + urllib.urlencode(parameters)

      # Read catalog url and convert to XML
      fetch = urlfetch.fetch(full_url, deadline=30)

      if fetch.status_code == 200:
         data = fetch.content
      else:
         self.response.out.write("Request took too long. Please try again!")
         return

      xml = ET.fromstring(data)

      # Logging DEBUG
      logging.info(data)

      # Pull out title attributes of entry
      entry.title = xml.find('.//title').attrib.get('regular')

      entry.movie_art = '<img src=\"' + xml.find('.//box_art').attrib.get('large') + '\">'

      entry.release_year = xml.find('.//release_year').text

      entry.runtime =  xml.find('.//runtime')
      if entry.runtime is None:
         entry.runtime = '--'
      else:
         entry.runtime = int(entry.runtime.text) / 60
      entry.runtime = str(entry.runtime) + ' mins'

      entry.avg_rating = xml.find('.//average_rating').text
      
      valid_episodes = xml.find('.//catalog_titles/number_of_results')
      if valid_episodes is not None:
         entry.episodes = valid_episodes.text + ' episodes'

      for i in xml.findall('.//availability/category'):
         entry.formats = entry.formats + i.attrib.get('label') + ', '
      entry.formats = entry.formats[0:-2].title()

      count = 0
      entry.genre = '<b>Genre:</b> '
      for i in xml.findall('.//category'):
         if (i.attrib.get('scheme') == 'http://api-public.netflix.com/categories/genres'):
            entry.genre += i.attrib.get('label')
            count += 1
            if count == 2:
               break
            entry.genre += ', '

      entry.synopsis = xml.find('.//synopsis').text

      Entries.append(entry)

   return Entries

class MainHandler(webapp.RequestHandler):
   def get(self):

      # Get search string
      search_string = self.request.get('search_input')

      auto_names = GetAutocompleteSearchTitles( search_string )

      Entries = GetCatalogTitles( auto_names )

      # Set up template values
      template_values = {
         'Entries': Entries,
         'search_string': search_string
      }

      path = os.path.join( os.path.dirname(__file__), 'index.html' )
      self.response.out.write( template.render( path, template_values ) )

class AboutPage(webapp.RequestHandler):
   def get(self):

      template_values = { }

      path = os.path.join( os.path.dirname(__file__), 'templates/about.html' )
      self.response.out.write( template.render( path, template_values ) )

def main():
   application = webapp.WSGIApplication([
                     ('/', MainHandler),
                     ('/about', AboutPage),
                 ], debug=True)

   util.run_wsgi_app(application)

if __name__ == '__main__':
   main()
