import os
import re
import json
import urllib
from io import BytesIO
import datetime
import string

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
import pytz

from otype import OTYPES_DICT, info

GOOGLE_URL_AUTOCOMPLETE = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
GOOGLE_URL_DETAILS = 'https://maps.googleapis.com/maps/api/place/details/json'

TWITTER_URL_MEDIA_UPLOAD = 'https://upload.twitter.com/1.1/media/upload.json'

TEXT_PROCESSING_URL = 'http://text-processing.com/api/tag/'

ALADIN_URL_IMAGE_BASE = 'http://alasky.u-strasbg.fr/cgi/portal/aladin/get-preview-img.py?pos={},{}&rgb=1'

CHARACTERS_MEDIA = 23
CHARACTERS_URL = 22
CHARACTERS_MAXIMUM = 140

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

TZ_DICT = {"International Date Line West": "Pacific/Midway", "Midway Island": "Pacific/Midway", "American Samoa": "Pacific/Pago_Pago", "Hawaii": "Pacific/Honolulu", "Alaska": "America/Juneau", "Pacific Time (US & Canada)": "America/Los_Angeles", "Tijuana": "America/Tijuana", "Mountain Time (US & Canada)": "America/Denver", "Arizona": "America/Phoenix", "Chihuahua": "America/Chihuahua", "Mazatlan": "America/Mazatlan", "Central Time (US & Canada)": "America/Chicago", "Saskatchewan": "America/Regina", "Guadalajara": "America/Mexico_City", "Mexico City": "America/Mexico_City", "Monterrey": "America/Monterrey", "Central America": "America/Guatemala", "Eastern Time (US & Canada)": "America/New_York", "Indiana (East)": "America/Indiana/Indianapolis", "Bogota": "America/Bogota", "Lima": "America/Lima", "Quito": "America/Lima", "Atlantic Time (Canada)": "America/Halifax", "Caracas": "America/Caracas", "La Paz": "America/La_Paz", "Santiago": "America/Santiago", "Newfoundland": "America/St_Johns", "Brasilia": "America/Sao_Paulo", "Buenos Aires": "America/Argentina/Buenos_Aires", "Montevideo": "America/Montevideo", "Georgetown": "America/Guyana", "Greenland": "America/Godthab", "Mid-Atlantic": "Atlantic/South_Georgia", "Azores": "Atlantic/Azores", "Cape Verde Is.": "Atlantic/Cape_Verde", "Dublin": "Europe/Dublin", "Edinburgh": "Europe/London", "Lisbon": "Europe/Lisbon", "London": "Europe/London", "Casablanca": "Africa/Casablanca", "Monrovia": "Africa/Monrovia", "UTC": "Etc/UTC", "Belgrade": "Europe/Belgrade", "Bratislava": "Europe/Bratislava", "Budapest": "Europe/Budapest", "Ljubljana": "Europe/Ljubljana", "Prague": "Europe/Prague", "Sarajevo": "Europe/Sarajevo", "Skopje": "Europe/Skopje", "Warsaw": "Europe/Warsaw", "Zagreb": "Europe/Zagreb", "Brussels": "Europe/Brussels", "Copenhagen": "Europe/Copenhagen", "Madrid": "Europe/Madrid", "Paris": "Europe/Paris", "Amsterdam": "Europe/Amsterdam", "Berlin": "Europe/Berlin", "Bern": "Europe/Berlin", "Rome": "Europe/Rome", "Stockholm": "Europe/Stockholm", "Vienna": "Europe/Vienna", "West Central Africa": "Africa/Algiers", "Bucharest": "Europe/Bucharest", "Cairo": "Africa/Cairo", "Helsinki": "Europe/Helsinki", "Kyiv": "Europe/Kiev", "Riga": "Europe/Riga", "Sofia": "Europe/Sofia", "Tallinn": "Europe/Tallinn", "Vilnius": "Europe/Vilnius", "Athens": "Europe/Athens", "Istanbul": "Europe/Istanbul", "Minsk": "Europe/Minsk", "Jerusalem": "Asia/Jerusalem", "Harare": "Africa/Harare", "Pretoria": "Africa/Johannesburg", "Moscow": "Europe/Moscow", "St. Petersburg": "Europe/Moscow", "Volgograd": "Europe/Moscow", "Kuwait": "Asia/Kuwait", "Riyadh": "Asia/Riyadh", "Nairobi": "Africa/Nairobi", "Baghdad": "Asia/Baghdad", "Tehran": "Asia/Tehran", "Abu Dhabi": "Asia/Muscat", "Muscat": "Asia/Muscat", "Baku": "Asia/Baku", "Tbilisi": "Asia/Tbilisi", "Yerevan": "Asia/Yerevan", "Kabul": "Asia/Kabul", "Ekaterinburg": "Asia/Yekaterinburg", "Islamabad": "Asia/Karachi", "Karachi": "Asia/Karachi", "Tashkent": "Asia/Tashkent", "Chennai": "Asia/Kolkata", "Kolkata": "Asia/Kolkata", "Mumbai": "Asia/Kolkata", "New Delhi": "Asia/Kolkata", "Kathmandu": "Asia/Kathmandu", "Astana": "Asia/Dhaka", "Dhaka": "Asia/Dhaka", "Sri Jayawardenepura": "Asia/Colombo", "Almaty": "Asia/Almaty", "Novosibirsk": "Asia/Novosibirsk", "Rangoon": "Asia/Rangoon", "Bangkok": "Asia/Bangkok", "Hanoi": "Asia/Bangkok", "Jakarta": "Asia/Jakarta", "Krasnoyarsk": "Asia/Krasnoyarsk", "Beijing": "Asia/Shanghai", "Chongqing": "Asia/Chongqing", "Hong Kong": "Asia/Hong_Kong", "Urumqi": "Asia/Urumqi", "Kuala Lumpur": "Asia/Kuala_Lumpur", "Singapore": "Asia/Singapore", "Taipei": "Asia/Taipei", "Perth": "Australia/Perth", "Irkutsk": "Asia/Irkutsk", "Ulaanbaatar": "Asia/Ulaanbaatar", "Seoul": "Asia/Seoul", "Osaka": "Asia/Tokyo", "Sapporo": "Asia/Tokyo", "Tokyo": "Asia/Tokyo", "Yakutsk": "Asia/Yakutsk", "Darwin": "Australia/Darwin", "Adelaide": "Australia/Adelaide", "Canberra": "Australia/Melbourne", "Melbourne": "Australia/Melbourne", "Sydney": "Australia/Sydney", "Brisbane": "Australia/Brisbane", "Hobart": "Australia/Hobart", "Vladivostok": "Asia/Vladivostok", "Guam": "Pacific/Guam", "Port Moresby": "Pacific/Port_Moresby", "Magadan": "Asia/Magadan", "Solomon Is.": "Pacific/Guadalcanal", "New Caledonia": "Pacific/Noumea", "Fiji": "Pacific/Fiji", "Kamchatka": "Asia/Kamchatka", "Marshall Is.": "Pacific/Majuro", "Auckland": "Pacific/Auckland", "Wellington": "Pacific/Auckland", "Nuku'alofa": "Pacific/Tongatapu", "Tokelau Is.": "Pacific/Fakaofo", "Chatham Is.": "Pacific/Chatham", "Samoa": "Pacific/Apia"}

c = 299792.458

# The following is an attempt to get an image directly out of Aladin. Needs work.
# http://cdsportal.u-strasbg.fr/AladinPoolServlet/AladinPoolServlet?script=setconf%20cm%3Dnoreverse%3Breticle%20off%3Bscale%20off%3Bget%20aladin%28POSSII/F/DSS2%29%2013%2029%2042.4%20%2B47%2011%2041%3Bget%20aladin%28POSSII/J/DSS2%29%2013%2029%2042.4%20%2B47%2011%2041%3Bsync%3Bzoom%202x%3Brgb%201%202%3Bsync%3Bgrid%20off%3Bsave%20-png%20768x768%3Bquit

class Bot(object):
    """The WhatsAboveMe twitterbot."""

    def __init__(self, n_pix_image=400, arrow_offset=(179, 130)):
        self.twitter_api = TwitterAPI(
            TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
            TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)
        self.stream = None
        self.wp_client = WordPressClient(
            WORDPRESS_ENDPOINT, 'whatsaboveme', WORDPRESS_PASSWORD)
        self.n_pix_image = n_pix_image
        try:
            self.arrow = Image.open('/app/arrow.png')
        except IOError:
            self.arrow = Image.open('arrow.png')
        self.arrow_offset = arrow_offset
        # The following list is in descending order of preference
        self.filternames = ['V', 'r', 'B', 'g', 'R', 'i', 'U', 'u', 'I', 'z']
        self.simbad = Simbad()
        self.simbad.add_votable_fields('otype', 'ze', 'velocity')
        self.simbad.add_votable_fields(
            *['flux({})'.format(f) for f in self.filternames])

    def activate(self):
        """Switch the bot on."""
        self.stream = self.twitter_api.request('user')
        for tweet in self.stream:
            self.process_tweet(tweet)

    def process_tweet(self, tweet):
        """Process and reply to a tweet."""
        tweet_info = self.parse_tweet(tweet)
        print 'Retrieved this information from the tweet:'
        print tweet_info
        if tweet_info['type'] in ['other', 'mention', 'not_tweet']:
            return
        if tweet['user']['screen_name'].lower() == 'whatsaboveme':
            # Don't reply to your own tweets!
            return
        elif tweet_info['type'] == 'follow':
            self.follow(
                tweet_info['username'],
                in_reply_to=tweet['id'],
                send_tweet=True)
        elif tweet_info['type'] == 'unfollow':
            self.unfollow(
                tweet_info['username'],
                in_reply_to=tweet['id'],
                send_tweet=True)
        elif tweet_info['type'] == 'location':
            self.tweet_location(
                tweet_info['location'],
                tweet_info['time'],
                tweet_info['username'],
                tweet_info['tz'],
                False,
                tweet['id'],
                location_in_tweet=tweet_info['location'],
                strict=True)
        elif tweet_info['type'] == 'request':
            self.tweet_location(
                tweet_info['location'],
                tweet_info['time'],
                tweet_info['username'],
                tweet_info['tz'],
                tweet_info['dot_at'],
                tweet['id'])

    def follow(self, username, in_reply_to=None, send_tweet=True):
        """Follow a user and send them an explanatory tweet."""
        payload = {'screen_name': username}
        self.twitter_api.request(
            'friendships/create',
            payload)
        if send_tweet:
            message = '@{} I am now following you, and will occasionally tweet you with updates. Tweet "@WhatsAboveMe unfollow" to stop at any time.'.format(username)
            self.tweet_text(message, in_reply_to=in_reply_to)

    def unfollow(self, username, in_reply_to=None, send_tweet=True):
        """Unfollow a user and send them an explanatory tweet."""
        payload = {'screen_name': username}
        self.twitter_api.request(
            'friendships/destroy',
            payload)
        if send_tweet:
            message = '@{} Sorry to say goodbye! I will no longer tweet you any updates. If you change your mind, tweet "@WhatsAboveMe follow".'.format(username)
            self.tweet_text(message, in_reply_to=in_reply_to)

    def tweet_location(self, location_name, tweet_time, username, tweet_tz,
                       dot_at, tweet_id, location_in_tweet='you',
                       strict=False):
        try:
            location = self.get_location(location_name, strict=strict)
        except LocationNotFoundError:
            return
        ra_dec = self.get_ra_dec(location, tweet_time)
        obj = self.get_object(ra_dec)
        image = self.get_sky_image(obj['coords'])
        processed_image = self.process_image(image)
        processed_image.filename = obj['name']+'.jpeg'
        link = self.make_post_with_info(
            obj, location['description'], tweet_time, tweet_tz,
            processed_image)
        reply_text = self.construct_reply(
            obj, link, username, dot_at, location_in_tweet)
        print 'Sending reply: {}'.format(reply_text)
        self.tweet_image(reply_text, processed_image, in_reply_to=tweet_id)

    def construct_reply(self, obj, link, screen_name, dot_at,
                        location_in_tweet):
        """Construct a reply to a tweet."""
        message = '.' if dot_at else ''
        message += '@{} {}'.format(screen_name, obj['name'])
        description = OTYPES_DICT[obj['type']].tweet_name
        characters_left = (
            CHARACTERS_MAXIMUM - 
            (len(message) + CHARACTERS_URL + CHARACTERS_MEDIA))
        if (len(description) + 3) <= characters_left:
            message += ', ' + description
        characters_left = (
            CHARACTERS_MAXIMUM - 
            (len(message) + CHARACTERS_URL + CHARACTERS_MEDIA))
        if (12 + len(location_in_tweet)) <= characters_left:
            message += ', is above ' + location_in_tweet
            extra_options = [
                ' right now. More info: ',
                ' right now. More: ',
                ' now. More info: ',
                ' now. More: ',
                ' now. ',
                '. ',
                ' ',
            ]
        else:
            extra_options = [
                '. More: ',
                '. ',
                ' ',
            ]
        characters_left = (
            CHARACTERS_MAXIMUM - 
            (len(message) + CHARACTERS_URL + CHARACTERS_MEDIA))
        for extra in extra_options:
            if len(extra) <= characters_left:
                message += extra
                break
        else:
            # Really should put a catch here for very extreme cases
            pass
        message += link
        return message

    def parse_tweet(self, tweet):
        """
        Extract location name and other info from a tweet message.

        Returns a dict that always includes 'type', plus other data as
        necessary. Possible types are:

        'request': a direct request for an update
        'mention': a tweet mentioning @whatsaboveme, but not a request
        'follow': a request that @whatsaboveme should follow the user
        'unfollow': a request that @whatsaboveme should unfollow the user
        'location': a tweet that includes a location to reply to
        'geolocation': a tweet that has geolocation data to reply to
        'other': none of the above, to be ignored
        'not_tweet': some other message from Twitter, not a tweet

        A 'location' type supercedes a 'geolocation' type, i.e. if a location
        is found in the text than any geolocation data will be ignored.
        """
        if tweet.keys() == ['friends'] or tweet.keys() == ['friends_str']:
            return {'type': 'not_tweet'}
        text = tweet['text']
        dot_at = text.startswith('.')
        if dot_at:
            text = text[1:]
        words = text.split()
        # All @'s removed
        words_trimmed = []
        # All @'s replaced with John, for text parsing purposes
        words_johnned = []
        found_me = False
        tweet_type = 'other'
        for word in words:
            if word.lower().startswith('@whatsaboveme'):
                found_me = True
                if words_trimmed:
                    # There have already been some non-@ words
                    tweet_type = 'mention'
            # Remove all @mentions from the text
            if word.startswith('@'):
                words_johnned.append('John')
            else:
                # This is a normal word. Have I been mentioned yet?
                if tweet_type == 'other' and found_me:
                    # The tweet was addressed to me. Mark it as a request.
                    # This might change to follow/unfollow later
                    tweet_type = 'request'
                # Copy what's left
                words_trimmed.append(word)
                words_johnned.append(word)
        text_trimmed = ' '.join(words_trimmed)
        text_johnned = ' '.join(words_johnned)
        # At this point tweet_type will be 'request' if the tweet started with
        # @whatsaboveme, 'mention' if @whatsaboveme was elsewhere in the text,
        # or 'other' if we weren't mentioned at all.
        # First check if 'request' is actually follow/unfollow
        if tweet_type == 'request':
            text_simple = text_trimmed.strip(string.punctuation).lower()
            if text_simple == 'follow':
                tweet_type = 'follow'
            elif text_simple == 'unfollow':
                tweet_type = 'unfollow'
        elif tweet_type == 'other':
            # We weren't mentioned in this tweet. Check it for locations that
            # might be named.
            response = requests.post(
                TEXT_PROCESSING_URL,
                data={'text': text_johnned, 'output': 'iob'})
            tagged = json.loads(response.content)['text']
            location = find_location_in_tags(tagged)
            if location:
                tweet_type = 'location'
        # Now construct an appropriate response, depending on the tweet type
        result = {'type': tweet_type,
                  'time': self.read_time(tweet['created_at']),
                  'tz': self.read_tz(tweet['user']['time_zone'])} 
        if tweet_type == 'request':
            result['location'] = text_trimmed
            result['dot_at'] = False
            result['username'] = tweet['user']['screen_name']
        elif tweet_type == 'follow' or tweet_type == 'unfollow':
            result['username'] = tweet['user']['screen_name']
        elif tweet_type == 'location':
            result['location'] = location
            result['username'] = tweet['user']['screen_name']
        return result

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
            payload['in_reply_to_status_id'] = in_reply_to
        self.twitter_api.request(
            'statuses/update',
            payload)

    def tweet_text(self, status, in_reply_to=None):
        """Tweet with text only, no image."""
        payload = {'status': status}
        if in_reply_to is not None:
            payload['in_reply_to_status_id'] = in_reply_to
        self.twitter_api.request(
            'statuses/update',
            payload)

    def get_location(self, name, strict=False):
        """Convert a location name into lon+lat."""
        print 'Searching for location: {}'.format(name)
        req_id = requests.get(
            GOOGLE_URL_AUTOCOMPLETE,
            params={'input':name, 'key':GOOGLE_MAPS_API_KEY})
        result = req_id.json()
        if result['status'] == 'ZERO_RESULTS':
            raise LocationNotFoundError(name)
        place_id = result['predictions'][0]['place_id']
        print 'Place ID found: {}'.format(place_id)
        description = result['predictions'][0]['description']
        terms = result['predictions'][0]['terms']
        if strict and not perfect_match(name, terms):
            raise LocationNotFoundError(name)
        req_loc = requests.get(
            GOOGLE_URL_DETAILS,
            params={'placeid': place_id, 'key':GOOGLE_MAPS_API_KEY})
        location = req_loc.json()['result']['geometry']['location']
        location['description'] = description
        print 'Location found: {}, {}'.format(location['lng'], location['lat'])
        return location

    def get_ra_dec(self, location, at_time):
        """Convert lon+lat+time into ra+dec."""
        delta = (Time(at_time, scale='utc') - START_TIME).value
        gst = 18.697374558 + 24.06570982441908 * delta
        ra = (gst * 15.0 + location['lng']) % 360                                                      
        dec = location['lat']
        print 'Coordinates found: {}, {}'.format(ra, dec)
        return {'ra': ra, 'dec': dec}

    def get_object(self, coords_dict):
        """Query Simbad for the object at a given ra+dec."""
        coords = coordinates.SkyCoord(
            ra=coords_dict['ra'], dec=coords_dict['dec'], unit=(u.deg, u.deg))
        simbad_result = self.simbad.query_region(coords, radius=0.25*u.deg)
        print 'Simbad results received: {} objects'.format(len(simbad_result))
        keep = np.array([bool(re.match(r'.+ .+ .+\..+', line['RA'])) and
                         bool(re.match(r'.+ .+ .+\..+', line['DEC']))
                         for line in simbad_result])
        trimmed_result = simbad_result[keep]
        coords_result = coordinates.SkyCoord(
            ra=trimmed_result['RA'], dec=trimmed_result['DEC'],
            unit=(u.hour, u.deg))
        idx = np.argmin(coords_result.separation(coords))
        closest_object = trimmed_result[idx]
        obj = {
            'name': closest_object['MAIN_ID'],
            'type': closest_object['OTYPE'],
            'coords': coords_result[idx],
        }
        if closest_object['ze_redshift']:
            obj['redshift'] = closest_object['ze_redshift']
        elif closest_object['RVZ_RADVEL']:
            obj['redshift'] = closest_object['RVZ_RADVEL'] / c
        # elif closest_object['RV_VALUE']:
        #     obj['redshift'] = closest_object['RV_VALUE'] / c
        else:
            obj['redshift'] = None
        for filt in self.filternames:
            key = 'FLUX_' + filt
            if closest_object[key]:
                obj['mag'] = closest_object[key]
                break
        else:
            obj['mag'] = None
        print 'Object found: {}, {}'.format(obj['name'], obj['type'])
        return obj

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
                     publish=True):
        """Make a WordPress blog post and return its ID."""
        if tags is None:
            tags = []
        if categories is None:
            categories = []
        post = WordPressPost()
        post.title = title
        post.content = content
        post.terms_names = {'post_tag': tags, 'category': categories}
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

    def make_post_with_info(self, obj, location, at_time, time_zone, image):
        """Make a WordPress post about the object and return its URL."""
        title = obj['name']
        image_response = self.upload_wp_image(image)
        image_html = '''[caption id="attachment_22" align="aligncenter" width="{n_pix_image}"]<a href="{image_url}"><img class="wp-image-22 size-full" src="{image_url}" alt="{name}" width="{n_pix_image}" height="{n_pix_image}" /></a> {name}[/caption]'''.format(
            n_pix_image=self.n_pix_image,
            image_url=image_response['url'],
            name=obj['name'])
        formatted_time = self.format_time(at_time, time_zone)
        description_html = '''<p>{name}, {otype}, was above {location} at {at_time}.</p>'''.format(
            name=obj['name'],
            otype=OTYPES_DICT[obj['type']].tweet_name,
            location=location,
            at_time=formatted_time)
        content = description_html + image_html + info(obj)
        post_id = self.make_wp_post(
            title, content, categories=['botpost'], tags=[obj['type']])
        return self.get_wp_link(post_id)

    def read_time(self, time_str):
        """Convert time string to UTC datetime object."""
        time_obj = datetime.datetime.strptime(
            time_str, '%a %b %d %H:%M:%S +0000 %Y')
        time_obj = datetime.datetime(
            time_obj.year, time_obj.month, time_obj.day, time_obj.hour,
            time_obj.minute, time_obj.second, tzinfo=pytz.utc)
        return time_obj

    def read_tz(self, time_zone):
        """Convert timezone string to pytz timezone object."""
        if time_zone:
            tz_str = TZ_DICT[time_zone]
        else:
            tz_str = 'UTC'
        return pytz.timezone(tz_str)

    def format_time(self, time, time_zone):
        """Format a time+date for human reading."""
        time_in_tz = time.astimezone(time_zone)
        time_str = time_in_tz.strftime('%H:%M:%S on %d %B %Y (%Z)')
        time_str = time_str.replace(' 0', ' ').replace(' ()', '')
        return time_str


def find_location_in_tags(tagged):
    """Return the longest location in the tagged text, or None."""
    location = []
    current_location = []
    for line in tagged.split('\n'):
        if line.endswith('GPE') or line.endswith('LOCATION'):
            # This is a location word, add it to the current one
            current_location.append(line.split()[0])
        elif line.startswith(',') and current_location:
            current_location[-1] += ','
        else:
            # Not a location word.
            if len(current_location) > len(location):
                # Just finished a new longest word, so save it
                location = current_location
                # Restart the counter
                current_location = []
    # Check again in case the text finished with the longest location
    if len(current_location) > len(location):
        location = current_location
    return ' '.join(location)

def perfect_match(requested, matched):
    """Make sure the requested location full matches the matched one."""
    requested_simple = requested.lower()
    for char in string.punctuation:
        requested_simple = requested_simple.replace(char, '')
    for i in xrange(len(matched)):
        # Add one term at a time, and compare the result against the request
        check = ' '.join([term['value'] for term in matched[:i+1]]).lower()
        for char in string.punctuation:
            check = check.replace(char, '')
        print check, requested_simple
        if check == requested_simple:
            return True
    return False

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


