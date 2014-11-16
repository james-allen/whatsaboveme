import os
import re
import json
import urllib
from io import BytesIO

import numpy as np
import requests
from astropy.time import Time
from astropy import coordinates
import astropy.units as u
from astroquery.simbad import Simbad
from TwitterAPI import TwitterAPI
from PIL import Image
from wordpress_xmlrpc import Client as WordPressClient
from wordpress_xmlrpc import WordPressPost
from wordpress_xmlrpc import methods as wordpress_methods
from wordpress_xmlrpc.compat import xmlrpc_client

from otype import OTYPES_DICT

GOOGLE_URL_AUTOCOMPLETE = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
GOOGLE_URL_DETAILS = 'https://maps.googleapis.com/maps/api/place/details/json'

TWITTER_URL_MEDIA_UPLOAD = 'https://upload.twitter.com/1.1/media/upload.json'

ALADIN_URL_IMAGE_BASE = 'http://alasky.u-strasbg.fr/cgi/portal/aladin/get-preview-img.py?pos={},{}&rgb=1'

try:
    GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']
except KeyError:
    print 'Google maps API key not found.'
    GOOGLE_MAPS_API_KEY = None

try:
    TWITTER_CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
    TWITTER_CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
    TWITTER_ACCESS_TOKEN_KEY = os.environ['TWITTER_ACCESS_TOKEN_KEY']
    TWITTER_ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
except KeyError:
    print 'Twitter API key not found.'
    TWITTER_CONSUMER_KEY = None
    TWITTER_CONSUMER_SECRET = None
    TWITTER_ACCESS_TOKEN_KEY = None
    TWITTER_ACCESS_TOKEN_SECRET = None

WORDPRESS_ENDPOINT = 'http://whatsaboveme.wordpress.com/xmlrpc.php'
try:
    WORDPRESS_PASSWORD = os.environ['WORDPRESS_PASSWORD']
except KeyError:
    print 'WordPress password not found.'
    WORDPRESS_PASSWORD = None

START_TIME = Time('2000-01-01 12:00:00.0', scale='utc')

SimbadQuerier = Simbad()
SimbadQuerier.add_votable_fields('otype')

# The following is an attempt to get an image directly out of Aladin. Needs work.
# http://cdsportal.u-strasbg.fr/AladinPoolServlet/AladinPoolServlet?script=setconf%20cm%3Dnoreverse%3Breticle%20off%3Bscale%20off%3Bget%20aladin%28POSSII/F/DSS2%29%2013%2029%2042.4%20%2B47%2011%2041%3Bget%20aladin%28POSSII/J/DSS2%29%2013%2029%2042.4%20%2B47%2011%2041%3Bsync%3Bzoom%202x%3Brgb%201%202%3Bsync%3Bgrid%20off%3Bsave%20-png%20768x768%3Bquit

class Bot(object):
    """The WhatsAboveMe twitterbot."""

    def __init__(self, n_pix_image=400, arrow_filename='/app/arrow.png',
                 arrow_offset=(179, 130)):
        self.twitter_api = TwitterAPI(
            TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
            TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)
        self.stream = None
        self.wp_client = WordPressClient(
            WORDPRESS_ENDPOINT, 'whatsaboveme', WORDPRESS_PASSWORD)
        self.n_pix_image = n_pix_image
        self.arrow = Image.open(arrow_filename)
        self.arrow_offset = arrow_offset

    def activate(self):
        """Switch the bot on."""
        self.stream = self.twitter_api.request(
            'statuses/filter', {'track': '@whatsaboveme'})
        for tweet in self.stream:
            self.process_tweet(tweet)

    def process_tweet(self, tweet):
        """Process and reply to a tweet."""
        text = tweet['text'].lower().replace('@whatsaboveme', '')
        try:
            location = self.get_location(text)
        except LocationNotFoundError:
            return
        ra_dec = self.get_ra_dec(location)
        obj = self.get_object(ra_dec)
        image = self.get_sky_image(obj['coords'])
        processed_image = self.process_image(image)
        processed_image.filename = obj['name']+'.jpeg'
        link = self.make_post_with_info(obj, text, processed_image)
        message = '{}, {}, is above you right now. More info: {}'.format(
            obj['name'], OTYPES_DICT[obj['type']].tweet_name, link)
        reply_text = '@{} {}'.format(tweet['user']['screen_name'], message)
        print 'Sending reply: {}'.format(reply_text)
        self.tweet_image(reply_text, processed_image, in_reply_to=tweet)

    def tweet_image(self, status, image, in_reply_to=None):
        """Tweet with an image. `image` is a PIL Image."""
        image_bytes = image.tobytes('jpeg', image.mode)
        response = requests.post(
            TWITTER_URL_MEDIA_UPLOAD,
            files={'media': image_bytes},
            auth=self.twitter_api.auth)
        response_json = json.loads(response.text)
        media_id = response_json['media_id_string']
        payload = {'status': status,
                   'media_ids': media_id}
        if in_reply_to is not None:
            payload['in_reply_to_status_id'] = in_reply_to['id']
        self.twitter_api.request(
            'statuses/update',
            payload)

    def get_location(self, name):
        print 'Searching for location: {}'.format(name)
        req_id = requests.get(
            GOOGLE_URL_AUTOCOMPLETE,
            params={'input':name, 'key':GOOGLE_MAPS_API_KEY})
        result = req_id.json()
        if result['status'] == 'ZERO_RESULTS':
            raise LocationNotFoundError(name)
        place_id = result['predictions'][0]['place_id']
        print 'Place ID found: {}'.format(place_id)
        req_loc = requests.get(
            GOOGLE_URL_DETAILS,
            params={'placeid': place_id, 'key':GOOGLE_MAPS_API_KEY})
        location = req_loc.json()['result']['geometry']['location']
        print 'Location found: {}, {}'.format(location['lng'], location['lat'])
        return location

    def get_ra_dec(self, location):
        gst = (18.697374558 + 24.06570982441908 * (Time.now() - START_TIME).value)
        ra = (gst * 15.0 + location['lng']) % 360                                                      
        dec = location['lat']
        print 'Coordinates found: {}, {}'.format(ra, dec)
        return {'ra': ra, 'dec': dec}

    def get_object(self, coords_dict):
        coords = coordinates.SkyCoord(
            ra=coords_dict['ra'], dec=coords_dict['dec'], unit=(u.deg, u.deg))
        simbad_result = SimbadQuerier.query_region(coords, radius=0.25*u.deg)
        print 'Simbad results received: {} objects'.format(len(simbad_result))
        keep = np.array([bool(re.match(r'.+ .+ .+\..+', line['RA'])) and
                         bool(re.match(r'.+ .+ .+\..+', line['DEC']))
                         for line in simbad_result])
        trimmed_result = simbad_result[keep]
        coords_result = coordinates.SkyCoord(
            ra=trimmed_result['RA'], dec=trimmed_result['DEC'],
            unit=(u.hour, u.deg))
        idx = np.argmin(coords_result)
        closest_object = trimmed_result[idx]
        object_name = closest_object['MAIN_ID']
        object_type = closest_object['OTYPE']
        print 'Object found: {}, {}'.format(object_name, object_type)
        return {'name': object_name, 'type': object_type,
                'coords': coords_result[idx]}

    def get_sky_image(self, coords):
        """Return a jpeg PIL Image downloaded from Aladin."""
        print 'Downloading image'
        response = urllib.urlopen(aladin_url_image(coords))
        image = Image.open(BytesIO(response.read()))
        print 'Image received'
        return image

    def process_image(self, image):
        """Crop the image and add an arrow pointing to the central object."""
        size = image.size
        image_crop = image.convert(mode='RGB').crop((
            size[0]/2-self.n_pix_image/2,
            size[1]/2-self.n_pix_image/2,
            size[0]/2+self.n_pix_image/2,
            size[1]/2+self.n_pix_image/2))
        image_crop.paste(self.arrow, box=self.arrow_offset, mask=self.arrow)
        print 'Image processed'
        return image_crop

    def make_wp_post(self, title, content, tags=None, categories=None,
                     images=None, publish=True):
        """Make a WordPress blog post and return its ID."""
        if tags is None:
            tags = []
        if categories is None:
            categories = []
        post = WordPressPost()
        post.title = title
        post.terms_names = {'post_tag': tags, 'category': categories}
        if images is not None:
            image_responses = [self.upload_wp_image(image) for image in images]
            image_ids = ','.join(
                [response['id'] for response in image_responses])
            content = content.format(image_ids)
        post.content = content
        if publish:
            post.post_status = 'publish'
        else:
            post.post_status = 'draft'
        return self.wp_client.call(wordpress_methods.posts.NewPost(post))

    def upload_wp_image(self, image):
        """Upload a PIL Image to WordPress and return the response."""
        image_bytes = image.tobytes('jpeg', image.mode)
        image_bits = xmlrpc_client.Binary(image_bytes)
        data = {'name': image.filename,
                'type': 'image/jpg',
                'bits': image_bits}
        return self.wp_client.call(wordpress_methods.media.UploadFile(data))

    def get_wp_link(self, post_id):
        """Get the URL of a WordPress post with the given ID."""
        post = self.wp_client.call(wordpress_methods.posts.GetPost(post_id))
        return post.link

    def make_post_with_info(self, obj, location, image):
        """Make a WordPress post about the object and return its URL."""
        title = obj['name']
        content = '''<p>{}, {}, is above {} right now.</p>
[gallery type="rectangular" ids="{}" size="full"]'''
        content = content.format(
            obj['name'], OTYPES_DICT[obj['type']].tweet_name, location, '{}')
        post_id = self.make_wp_post(
            title, content, categories=['botpost'], tags=[obj['type']],
            images=[image])
        return self.get_wp_link(post_id)


def aladin_url_image(coords):
    """Return the URL to get an Aladin preview image."""
    return ALADIN_URL_IMAGE_BASE.format(coords.ra.degree, coords.dec.degree)


class BotError(Exception):
    pass

class LocationNotFoundError(BotError):
    pass


if __name__ == '__main__':
    bot = Bot()
    bot.activate()


