from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import flask
from flask import request, jsonify
from flask_cors import CORS
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import datetime

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
messagesStore= {}

# If modifying these scopes, delete the file token.pickle.
SHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1KsEPEC4xwlTlTKugxX-IgfZ9jGE9Z6TdOVx_mYIDheM'
SAMPLE_RANGE_NAME = 'Rapport husbesk'

def setupGmailService():
    store = file.Storage('token-gmail.json')
    creds = store.get()
    
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)

    return build('gmail', 'v1', http=creds.authorize(Http()))

def setupSheetsService():
    store = file.Storage('token-sheets.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SHEET_SCOPES)
        creds = tools.run_flow(flow, store)
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    return build('sheets', 'v4', credentials=creds)


def getEmailListFromGmail(service):
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])

    nextPageToken = results.get('nextPageToken', False)

    while nextPageToken:
        results = service.users().messages().list(userId='me', pageToken=nextPageToken).execute()
        nextPageToken = results.get('nextPageToken', False)
        messages.extend(results.get('messages',[]))
   
    return messages


def getMailbodyAndTimeFromGmail(service, messageid):
    if messageid not in messagesStore:
        result = service.users().messages().get(userId="me",id=messageid, format='full').execute()
        headers = result.get('payload', {}).get('headers', [])
        subject = ''
        for header in headers:
            if header['name'].lower() == 'subject':
                subject = header['value']
                break
        messagesStore[messageid] = (subject, result.get('internalDate', 0))

    return messagesStore[messageid]


def isOlderThanTreshold(timestamp, hour_treshold):
    dateTime = datetime.fromtimestamp(int(timestamp)/1000)
    time_since_registration = datetime.today() - dateTime

    return time_since_registration.total_seconds()//3600 > hour_treshold


def getMembershipDataFromEmail(messageid, service):
    subject, registeredTime = getMailbodyAndTimeFromGmail(service, messageid)

    # New format: "Nytt medlem i [lokallag]" - chapter name is the 4th word
    if not "Nytt medlem i" in subject:
        return False

    # Extract lokallag as the 4th word (index 3)
    words = subject.split()
    if len(words) < 4:
        return False
    
    chapter = words[3]

    return {
        "chapter": chapter, 
        "timestamp": int(registeredTime)
    }


def getNewMembers(hour_treshold):
    service = setupGmailService()
    new_memberships =  []

    for email in getEmailListFromGmail(service):
        membershipData = getMembershipDataFromEmail(email["id"], service)

        if not membershipData:
            continue

        if isOlderThanTreshold(membershipData["timestamp"], hour_treshold):
            break

        new_memberships.append(membershipData)

    return new_memberships

def getActions():
    service = setupSheetsService()
    sheets = service.spreadsheets()
    result = sheets.get(spreadsheetId=SAMPLE_SPREADSHEET_ID).execute()
    
    # Return the number of sheets in the spreadsheet
    # This matches the route name 'get_number_of_lists'
    sheet_count = len(result.get('sheets', []))
    return {'count': sheet_count, 'sheets': [sheet.get('properties', {}).get('title', '') for sheet in result.get('sheets', [])]}

if __name__ == '__main__':
    server = flask.Flask(__name__)
    CORS(server)
    server.config["DEBUG"] = True


    @server.route('/newmembers', methods=['GET'])
    def home():
        return jsonify(getNewMembers(0))

    @server.route('/newmembers/<hour_treshold>', methods=['GET'])
    def specific_day(hour_treshold):
        return jsonify(getNewMembers(int(hour_treshold)))

    @server.route('/actions', methods=['GET'])
    def get_number_of_lists():
        return jsonify(getActions())

    server.run()