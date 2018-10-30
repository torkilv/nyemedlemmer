from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import flask
from flask import request, jsonify
from flask_cors import CORS

from datetime import datetime

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
messagesStore= {}

def setupGmailService():
    store = file.Storage('token.json')
    creds = store.get()
    
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)

    return build('gmail', 'v1', http=creds.authorize(Http()))


def getEmailListFromGmail(service):
    results = service.users().messages().list(userId='me').execute()
    return results.get('messages', [])


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

    server.run()