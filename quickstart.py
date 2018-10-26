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

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))

    # Call the Gmail API
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])

    if not messages:
        return 'No messages found'
    else:
        print('New messages:')
        last_checked = open("last-checked-id", "r").read();
        new_messages = []
        lokallagene = []
        for message in messages:            
            #if message["id"] == last_checked:
            #    break
            new_messages.append(message["id"])

        if new_messages:
            open("last-checked-id","w").write(new_messages[0])

        for messageid in new_messages:
            result = service.users().messages().get(userId="me",id=messageid).execute()
            print(messageid)
            snippet = result.get('snippet',[])
            if not "meldt seg inn i" in snippet:
                continue
            lokallag = snippet.split("meldt seg inn i ")[1].split(". L")[0]
            internalDate = result.get('internalDate', 0)
            message_date = datetime.fromtimestamp(float(internalDate)/1000)
            time_since = datetime.today() - message_date
            if time_since.days > 0:
                break


            if snippet:
                lokallagene.append({"chapter":lokallag, "timestamp":str(int(internalDate)/1000)})

        return lokallagene



if __name__ == '__main__':
    #main()
    app = flask.Flask(__name__)
    CORS(app)
    app.config["DEBUG"] = True


    @app.route('/', methods=['GET'])
    def home():
        return jsonify(main())

    app.run()