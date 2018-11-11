from __future__ import print_function
from botocore.vendored import requests

import argparse
import json
import pprint
import boto3
import sys
import urllib
import decimal
import types

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode


# Yelp Fusion no longer uses OAuth as of December 7, 2017.
# You no longer need to provide Client ID to fetch Data
# It now uses private keys to authenticate requests (API Key)
# You can find it on
# https://www.yelp.com/developers/v3/manage_app
API_KEY= 'XWkjMu1uv1b_SjIyVpcjUv0wUUAlmaxO6US5D9Cn8G43FSaPY3jdIombADZcDNvnFbebE2597isBzTNkx4bL9IOMWp-ohJujD6s43D5ca8h73W5gtNbXc6Nd-dPkW3Yx' 


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


# Defaults for our simple example.
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'San Francisco, CA'
SEARCH_LIMIT = 1


def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


def search(api_key, term, location):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def get_business(api_key, business_id):
    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, api_key)


def query_api(term, location, userNumber):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    response = search(API_KEY, term, location)

    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return

    business_id = businesses[0]['id']

    print(u'{0} businesses found, querying business info ' \
        'for the top result "{1}" ...'.format(
            len(businesses), business_id))
    response = get_business(API_KEY, business_id)

    print(u'Result for business "{0}" found:'.format(business_id))
    pprint.pprint(response, indent=2)
    # Dynamo operation
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://dynamodb.us-west-2.amazonaws.com")
    
    yelpCuisineName = response['name']
    yelpCuisineLocation = response['location']['address1']
    
    table = dynamodb.Table('CuisineTable')
    response = table.put_item(
        Item={
            'Name' : yelpCuisineName,
            'Location' : yelpCuisineLocation,
            'Phone' : userNumber
        }
    )
    # SMS send message to user's phone number & 
    SMSclient = boto3.client("sns")

    
    #phoneNumber = '+19175158166'
    phoneNumber = '+1'+userNumber
    SMSclient.publish(
        PhoneNumber= phoneNumber,
        Message="Your cuisine order is finished! "+'The cuisine is '+yelpCuisineName+' in '+yelpCuisineLocation+'. Enjoy!'
    )
    

def findCuisineFromYelp(intent_request):
    ############################################ boto3 receive SQS and find cuisine
    sqs = boto3.client('sqs')

    queue_url = 'https://sqs.us-west-2.amazonaws.com/225139474139/TestQueue'

    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )

    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']

    sqs.delete_message(QueueUrl=queue_url,ReceiptHandle=receipt_handle)
    
    print('Received and deleted message: %s' % json.loads(message['Body'])['Cuisine_type'])
    ############################################ boto3 receive SQS and find cuisine
    cuisine_type = json.loads(message['Body'])['Cuisine_type']
    location_type = json.loads(message['Body'])['Location_type']
    user_phoneNumber = json.loads(message['Body'])['User_phone_number']
    try:
        query_api(cuisine_type, location_type, user_phoneNumber)
    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )

def lambda_handler(event, context):
    
    return findCuisineFromYelp(event)
