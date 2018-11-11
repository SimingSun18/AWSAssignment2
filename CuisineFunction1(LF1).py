"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import datetime
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_orders(cuisine, location, people_number, phone_number, dining_time):
    cuisine_types = ['Chinese', 'Japanese', 'Italian']
    location_types = ['Manhattan', 'Brooklyn', 'Queens']
    
    #if cuisine is not None and cuisine not in cuisine_types:
        #return build_validation_result(False,'Cuisine','We do not have {}, would you like a different type?'.format(cuisine))
    #if location is not None and location not in location_types:
        #return build_validation_result(False,'Location','We do not have {}, would you like a different type?'.format(location))
    return build_validation_result(True, None, None)
""" --- Functions that control the bot's behavior --- """


def order_dining(intent_request):

    cuisine = get_slots(intent_request)["Cuisine"]
    location = get_slots(intent_request)["Location"]
    people_number = get_slots(intent_request)["NumberOfPeople"]
    phone_number = get_slots(intent_request)["PhoneNumber"]
    dining_time = get_slots(intent_request)["DiningTime"]
    
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':

        slots = get_slots(intent_request)
        
        #SQS test

        queue_url = 'https://sqs.us-west-2.amazonaws.com/225139474139/TestQueue'
        
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName='TestQueue')
        response = queue.send_message(MessageBody=json.dumps(
            {   
                'Cuisine_type' : get_slots(intent_request)["Cuisine"],
                'Location_type' : get_slots(intent_request)["Location"],
                'User_phone_number' : get_slots(intent_request)["PhoneNumber"]
            }))
        #
        
        validation_result = validate_orders(cuisine, location, people_number, phone_number, dining_time)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                            intent_request['currentIntent']['name'],
                            slots,
                            validation_result['violatedSlot'],
                            validation_result['message'])
        
        return delegate(None, get_slots(intent_request))
        
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thanks, your {} cuisine order for {} people has been placed in {} on {} and phone number is {}'
                  .format(cuisine, people_number, location, dining_time, phone_number)})


""" --- Intents --- """

def dispatch(intent_request):

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Hi there, can I help you?'})

    if intent_name == 'DiningSuggectionIntent':
        return order_dining(intent_request)
    if intent_name == 'ThankYouIntent':
        return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'You are welcome, enjoy your cuisine!'})
            
    #raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):

    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
