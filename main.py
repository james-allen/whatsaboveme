import os

import numpy as np
import requests
from astropy.time import Time
from astropy import coordinates
import astropy.units as u
# from astroquery.ned import Ned
from astroquery.simbad import Simbad
from TwitterAPI import TwitterAPI

GOOGLE_URL_AUTOCOMPLETE = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
GOOGLE_URL_DETAILS = 'https://maps.googleapis.com/maps/api/place/details/json'

GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']

START_TIME = Time('2000-01-01 12:00:00.0', scale='utc')

SimbadQuerier = Simbad()
SimbadQuerier.add_votable_fields('otype')

def get_location(name):
    req_id = requests.get(
        GOOGLE_URL_AUTOCOMPLETE,
        params={'input':name, 'key':GOOGLE_MAPS_API_KEY})
    place_id = req_id.json()['predictions'][0]['place_id']
    req_loc = requests.get(
        GOOGLE_URL_DETAILS,
        params={'placeid': place_id, 'key':GOOGLE_MAPS_API_KEY})
    return req_loc.json()['result']['geometry']['location']

def get_ra_dec(location):
    gst = (18.697374558 + 24.06570982441908 * (Time.now() - START_TIME).value)
    ra = (gst * 15.0 + location['lng']) % 360                                                      
    dec = location['lat']                           
    return {'ra': ra, 'dec': dec}

# def get_object(coords_dict):
#     coords = coordinates.SkyCoord(
#         ra=coords_dict['ra'], dec=coords_dict['dec'], unit=(u.deg, u.deg))
#     ned_result = Ned.query_region(coords, radius=0.1*u.deg)
#     closest_object = ned_result[np.argmin(ned_result['Distance (arcmin)'])]
#     object_name = closest_object['Object Name']
#     return object_name

def get_object(coords_dict):
    coords = coordinates.SkyCoord(
        ra=coords_dict['ra'], dec=coords_dict['dec'], unit=(u.deg, u.deg))
    simbad_result = SimbadQuerier.query_region(coords, radius=0.1*u.deg)
    coords_result = coordinates.SkyCoord(
        ra=simbad_result['RA'], dec=simbad_result['DEC'], unit=(u.hour, u.deg))
    closest_object = simbad_result[np.argmin(coords_result)]
    object_name = closest_object['MAIN_ID']
    object_type = closest_object['OTYPE']
    return {'name': object_name, 'type': object_type}

# The following is an attempt to get an image directly out of Aladin. Needs work.
# http://cdsportal.u-strasbg.fr/AladinPoolServlet/AladinPoolServlet?script=setconf%20cm%3Dnoreverse%3Breticle%20off%3Bscale%20off%3Bget%20aladin%28POSSII/F/DSS2%29%2013%2029%2042.4%20%2B47%2011%2041%3Bget%20aladin%28POSSII/J/DSS2%29%2013%2029%2042.4%20%2B47%2011%2041%3Bsync%3Bzoom%202x%3Brgb%201%202%3Bsync%3Bgrid%20off%3Bsave%20-png%20768x768%3Bquit

