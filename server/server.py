# -*- coding: utf-8 -*-
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
SAMPLE_SPREADSHEET_ID = '14fEYPSPJaMYvoESioHXSc0DR2jjiAFOns1FErhdGKPY'
SAMPLE_RANGE_NAME = 'Tall!D2'

DOOR_KNOCKING_SPREADSHEET_ID = '15NkVPeWOJvkDwY8tPCPhX16bDk9m2_TjU-ioGHa3LnY'
DOOR_KNOCKING_RANGE = 'Kontakt/samtaler!J2:L9'
FULL_RANGE = 'Kontakt/samtaler!A1:H20'

def setupGmailService():
    store = file.Storage('token-gmail.json')
    creds = store.get()
    
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials-gmail.json', SCOPES)
        creds = tools.run_flow(flow, store)

    return build('gmail', 'v1', http=creds.authorize(Http()))

def setupSheetsService():
    store = file.Storage('token-sheets.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials-sheets.json', SHEET_SCOPES)
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
        result = service.users().messages().get(userId="me",id=messageid).execute()
        messagesStore[messageid] = (result.get('snippet',[]), result.get('internalDate', 0))

    return messagesStore[messageid]


def isOlderThanTreshold(timestamp, hour_treshold):
    dateTime = datetime.fromtimestamp(int(timestamp)/1000)
    time_since_registration = datetime.today() - dateTime

    return time_since_registration.total_seconds()//3600 > hour_treshold


def getMembershipDataFromEmail(messageid, service):
    mailBody, registeredTime = getMailbodyAndTimeFromGmail(service, messageid)

    if not "meldt seg inn i" in mailBody:
        return False

    chapter = mailBody.split("meldt seg inn i ")[1].split(". L")[0]

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

def getNumberOfLists():
    service = setupSheetsService()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    value = result.get('values', [[-1]])

    return value[0][0]

def getDoorKnockingStats():
    service = setupSheetsService()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=DOOR_KNOCKING_SPREADSHEET_ID,
                                range=DOOR_KNOCKING_RANGE).execute()
    return result.get('values')

def getFullDoorKnockingStats():
    service = setupSheetsService()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=DOOR_KNOCKING_SPREADSHEET_ID,
                                range=FULL_RANGE).execute()
    return result.get('values')
    

app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def default():
    return "It works"

@app.route('/doors', methods=['GET'])
def get_door_stats():
    return jsonify(getDoorKnockingStats())

@app.route('/doors/extended', methods=['GET'])
def get_full_door_stats():
    return jsonify(getFullDoorKnockingStats())


CORS(app)


if __name__ == '__main__':
    print("Here")
    setupSheetsService()
    CORS(app)
    app.config["DEBUG"] = True

    print("Starting app")
    app.run(host='0.0.0.0', port='5000')
