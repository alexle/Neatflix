import os, sys, oauth2
import webapp2, jinja2
from google.appengine.api import urlfetch

from hashlib import sha1
import hmac, binascii, urllib,logging, time, string, random
from xml.etree import ElementTree as ET

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

# Get secret and consumer key from data file
FILE = open('templates/data.txt', 'r')
NET_SECRET = FILE.readline().strip()
CONSUMER_KEY = FILE.readline().strip()

AUTO_URL = "http://api-public.netflix.com/catalog/titles/autocomplete"
TITLE_URL = 'http://api-public.netflix.com/catalog/titles'

def OAuthEscape( s ):
   return urllib.quote( s, '' )

def RandomString( size=6, chars=string.ascii_uppercase + string.digits ):
   return ''.join( random.choice(chars) for x in range(size) )

def GenerateSig( parameters ):
   sig = 'GET&' + OAuthEscape( TITLE_URL ) + '&'

   param_encode = urllib.urlencode(parameters).replace('+', '%20')

   sig = sig + OAuthEscape(param_encode)

   secret =  NET_SECRET + '&'
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

   auto_parameters = [
      ('term', search_string),
      ('oauth_consumer_key', CONSUMER_KEY)]

   full_auto_url = AUTO_URL + '?' + urllib.urlencode(auto_parameters)

   # Read autocomplete url and convert to XML
   auto_data = urlfetch.fetch(full_auto_url, deadline=10).content
   auto_xml = ET.fromstring(auto_data)

   # auto_names holds the titles returned by autocomplete search
   auto_names = []

   # Grab all titles from autocomplete search
   for i in auto_xml.findall('.//title'):
      n = i.attrib.get('short')
      auto_names.append(n)

   return auto_names

def GetCatalogTitles( auto_names ):
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

      parameters = [
         ('expand', expand_parms),
         ('max_results', '1'),
         ('oauth_consumer_key', CONSUMER_KEY),
         ('oauth_nonce', nonce),
         ('oauth_signature_method', 'HMAC-SHA1'),
         ('oauth_timestamp', time_stamp),
         ('oauth_version', '1.0'),
         ('term', term)]

      sign = GenerateSig( parameters )

      parameters.append(('oauth_signature', sign))

      full_url = TITLE_URL + '?' + urllib.urlencode(parameters)

      # Read catalog url and convert to XML
      fetch = urlfetch.fetch(full_url, deadline=30)

      if fetch.status_code == 200:
         data = fetch.content
      else:
         self.response.out.write("Request took too long. Please try again!")
         return

      xml = ET.fromstring(data)

      # logging.info(data)

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

class MainHandler(webapp2.RequestHandler):
   def get(self):

      # Get search string
      search_string = self.request.get('search_input')

      # Gather autocomplete titles from Netflix API
      auto_names = GetAutocompleteSearchTitles( search_string )

      # Gather individual info for each autocomplete title
      Entries = GetCatalogTitles( auto_names )

      # Set up template values
      template_values = {
         'Entries': Entries,
         'search_string': search_string
      }

      template = jinja_environment.get_template('index.html')
      self.response.out.write( template.render( template_values ) )

class AboutPage(webapp2.RequestHandler):
   def get(self):

      template_values = { }

      template = jinja_environment.get_template('templates/about.html')
      self.response.out.write( template.render( template_values ) )

app = webapp2.WSGIApplication([
                  ('/', MainHandler),
                  ('/about', AboutPage),
               ], debug=True)
