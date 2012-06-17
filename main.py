import os, sys
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from hashlib import sha1
import hmac, binascii
import urllib, urllib2
import time, string, random
from xml.etree import ElementTree as ET

import logging

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

   secret = '<SECRET_KEY>' + '&'
   hashed = hmac.new(secret, sig, sha1)

   safe_sig = binascii.b2a_base64(hashed.digest())[:-1]

   return safe_sig

class MainHandler(webapp.RequestHandler):
   def get(self):

      template_values = { }

      path = os.path.join( os.path.dirname(__file__), 'index.html' )
      self.response.out.write( template.render( path, template_values ) )

   def post(self):

      url = 'http://api-public.netflix.com/catalog/titles'
      key = 'adqe4ngafwj8ybwvnfgbnuta'
      nonce = RandomString()
      time_stamp = str( int(time.time()) )
      expand_parms = 'synopsis,cast,formats,@episodes,@seasons'

      term = self.request.get('user')

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

      data = urllib2.urlopen(full_url).read()

      xml = ET.fromstring(data)

      # Parse xml
      movie_art = '<img src=\"' + xml.find('.//box_art').attrib.get('large') + '\">'

      title = xml.find('.//title').attrib.get('regular')

      release_year = xml.find('.//release_year').text

      runtime = xml.find('.//runtime')
      if runtime is None:
         runtime = '--'
      else:
         runtime = int(runtime.text) / 60
      runtime = str(runtime) + ' mins'

      avg_rating = xml.find('.//average_rating').text
      
      episodes = ''
      for i in xml.findall('.//link/catalog_titles/number_of_results'):
         if i is not None:
            episodes = i.text + ' episodes'

      formats = ''
      for i in xml.findall('.//availability/category'):
         formats = formats + i.attrib.get('label') + ', '
      formats = formats[0:-2].title()

      genre = ''
      for i in xml.findall('.//category'):
         if (i.attrib.get('scheme') == 'http://api.netflix.com/categories/genres'):
            genre = genre + i.attrib.get('label') + ', '
      genre = '<b>Genre:</b> ' + genre[0:-2]

      synopsis = xml.find('.//synopsis').text
      
      # Set up template values
      template_values = {
         'movie_art': movie_art,
         'title': title,
         'release_year': release_year,
         'runtime': runtime,
         'avg_rating': avg_rating,
         'episodes': episodes,
         'formats': formats,
         'synopsis': synopsis,
         'genre': genre,
         'user_name': sign,
      }
      
      path = os.path.join( os.path.dirname(__file__), 'index.html' )
      self.response.out.write( template.render( path, template_values ) )

      #//http://odata.netflix.com/Catalog/Titles?$filter=Name%20eq%20'Storage%20wars'

def main():
   application = webapp.WSGIApplication([
                     ('/', MainHandler),
                 ], debug=True)

   util.run_wsgi_app(application)

if __name__ == '__main__':
   main()
