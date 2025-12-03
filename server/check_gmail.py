#!/usr/bin/env python3
"""
Script to check Gmail for new member notifications and save to JSON file.
This script is designed to run in GitHub Actions.
"""
from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json
import os
from datetime import datetime

# If modifying these scopes, delete the file token-gmail.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
messagesStore = {}

def setupGmailService():
    """Set up and return Gmail service."""
    store = file.Storage('token-gmail.json')
    creds = store.get()
    
    if not creds or creds.invalid:
        if not os.path.exists('credentials.json'):
            print("ERROR: credentials.json not found.")
            print("For GitHub Actions: Set GMAIL_CREDENTIALS secret in repository settings.")
            print("For local: Place credentials.json in the server/ directory.")
            exit(1)
        
        # In GitHub Actions, we can't do interactive OAuth flow
        # The token must be pre-generated and stored as a secret
        if os.getenv('GITHUB_ACTIONS'):
            print("ERROR: token-gmail.json not found or invalid.")
            print("Please run this script locally first to generate the token,")
            print("then add the token-gmail.json contents as GMAIL_TOKEN secret.")
            print("If the token expired, regenerate it locally and update the secret.")
            exit(1)
        
        # Local development: interactive OAuth flow
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    
    # Check if token needs refresh
    if creds.access_token_expired:
        print("Token expired, attempting to refresh...")
        try:
            creds.refresh(Http())
            store.put(creds)
            print("Token refreshed successfully.")
        except Exception as e:
            print(f"ERROR: Failed to refresh token: {e}")
            if os.getenv('GITHUB_ACTIONS'):
                print("Please regenerate the token locally and update GMAIL_TOKEN secret.")
                exit(1)
            else:
                # Local: re-authenticate
                flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
                creds = tools.run_flow(flow, store)

    return build('gmail', 'v1', http=creds.authorize(Http()))

def getEmailListFromGmail(service):
    """Get list of all email messages."""
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])

    nextPageToken = results.get('nextPageToken', False)

    while nextPageToken:
        results = service.users().messages().list(userId='me', pageToken=nextPageToken).execute()
        nextPageToken = results.get('nextPageToken', False)
        messages.extend(results.get('messages', []))

    return messages

def getMailbodyAndTimeFromGmail(service, messageid):
    """Get email subject and timestamp, with caching."""
    if messageid not in messagesStore:
        result = service.users().messages().get(userId="me", id=messageid, format='full').execute()
        headers = result.get('payload', {}).get('headers', [])
        subject = ''
        for header in headers:
            if header['name'].lower() == 'subject':
                subject = header['value']
                break
        messagesStore[messageid] = (subject, result.get('internalDate', 0))

    return messagesStore[messageid]

def isOlderThanTreshold(timestamp, hour_treshold):
    """Check if timestamp is older than threshold."""
    dateTime = datetime.fromtimestamp(int(timestamp) / 1000)
    time_since_registration = datetime.today() - dateTime

    return time_since_registration.total_seconds() // 3600 > hour_treshold

def getMembershipDataFromEmail(messageid, service):
    """Extract membership data from email."""
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

def getNewMembers(hour_treshold=24):
    """Get new members from Gmail within the hour threshold."""
    service = setupGmailService()
    new_memberships = []

    for email in getEmailListFromGmail(service):
        membershipData = getMembershipDataFromEmail(email["id"], service)

        if not membershipData:
            continue

        if isOlderThanTreshold(membershipData["timestamp"], hour_treshold):
            break

        new_memberships.append(membershipData)

    return new_memberships

if __name__ == '__main__':
    # Get new members from last 24 hours
    new_members = getNewMembers(24)
    
    # Sort by timestamp (newest first)
    new_members.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Save to JSON file in the dashboard public directory
    # Handle both relative paths (local) and absolute paths (GitHub Actions)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    output_path = os.path.join(repo_root, 'dashboard', 'public', 'newmembers.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_members, f, indent=2, ensure_ascii=False)
    
    print(f"Found {len(new_members)} new members. Data saved to {output_path}")

