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
    print("  Loading token from token-gmail.json...", flush=True)
    import sys
    sys.stdout.flush()
    store = file.Storage('token-gmail.json')
    creds = store.get()
    print(f"  Token loaded: {creds is not None}, invalid: {creds.invalid if creds else 'N/A'}", flush=True)
    sys.stdout.flush()
    
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
    print("  Checking if token needs refresh...", flush=True)
    import sys
    sys.stdout.flush()
    if hasattr(creds, 'access_token_expired') and creds.access_token_expired:
        print("  Token expired, attempting to refresh...", flush=True)
        sys.stdout.flush()
        try:
            creds.refresh(Http())
            store.put(creds)
            print("  ✓ Token refreshed successfully.", flush=True)
            sys.stdout.flush()
        except Exception as e:
            print(f"  ERROR: Failed to refresh token: {e}", flush=True)
            sys.stdout.flush()
            if os.getenv('GITHUB_ACTIONS'):
                print("Please regenerate the token locally and update GMAIL_TOKEN secret.", flush=True)
                sys.stdout.flush()
                exit(1)
            else:
                # Local: re-authenticate
                flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
                creds = tools.run_flow(flow, store)
    else:
        print("  Token is valid, no refresh needed.", flush=True)
        sys.stdout.flush()

    print("  Building Gmail service...", flush=True)
    sys.stdout.flush()
    service = build('gmail', 'v1', http=creds.authorize(Http()))
    print("  ✓ Gmail service ready.", flush=True)
    sys.stdout.flush()
    return service

def getEmailListFromGmail(service, after_date=None):
    """Get list of email messages, optionally filtered by date.
    
    Args:
        service: Gmail API service object
        after_date: datetime object - only fetch emails after this date
    """
    import sys
    from datetime import datetime
    
    # Build query string for date filter
    query = None
    if after_date:
        # Gmail query format: after:YYYY/MM/DD
        date_str = after_date.strftime('%Y/%m/%d')
        query = f'after:{date_str}'
        print(f"    Filtering emails after {date_str}...", flush=True)
        sys.stdout.flush()
    else:
        print("    Making API call to list messages (no date filter)...", flush=True)
        sys.stdout.flush()
    
    try:
        # Make API call with query filter
        if query:
            results = service.users().messages().list(userId='me', q=query).execute()
        else:
            results = service.users().messages().list(userId='me').execute()
        
        messages = results.get('messages', [])
        print(f"    Found {len(messages)} messages in first page", flush=True)
        sys.stdout.flush()

        nextPageToken = results.get('nextPageToken', False)
        page_count = 1
        max_pages = 10  # Limit to prevent infinite loops

        while nextPageToken and page_count < max_pages:
            page_count += 1
            print(f"    Fetching page {page_count}...", flush=True)
            sys.stdout.flush()
            if query:
                results = service.users().messages().list(userId='me', q=query, pageToken=nextPageToken).execute()
            else:
                results = service.users().messages().list(userId='me', pageToken=nextPageToken).execute()
            nextPageToken = results.get('nextPageToken', False)
            messages.extend(results.get('messages', []))
            print(f"    Total messages so far: {len(messages)}", flush=True)
            sys.stdout.flush()

        if page_count >= max_pages:
            print(f"    ⚠ Reached max pages limit ({max_pages}), stopping", flush=True)
            sys.stdout.flush()

        print(f"    ✓ Retrieved {len(messages)} total messages", flush=True)
        sys.stdout.flush()
        return messages
    except Exception as e:
        print(f"    ERROR in getEmailListFromGmail: {type(e).__name__}: {e}", flush=True)
        sys.stdout.flush()
        import traceback
        traceback.print_exc()
        raise

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
    import sys
    from datetime import datetime, timedelta
    
    print("  Getting email list from Gmail...", flush=True)
    sys.stdout.flush()
    service = setupGmailService()
    
    # Only fetch emails from December 3rd, 2024 onwards
    # This significantly reduces the number of emails to process
    cutoff_date = datetime(2025, 12, 3)
    print(f"  Fetching emails after {cutoff_date.strftime('%Y-%m-%d')}...", flush=True)
    sys.stdout.flush()
    email_list = getEmailListFromGmail(service, after_date=cutoff_date)
    print(f"  Processing {len(email_list)} emails...", flush=True)
    sys.stdout.flush()
    new_memberships = []
    
    processed = 0
    for email in email_list:
        processed += 1
        if processed % 100 == 0:
            print(f"  Processed {processed} emails, found {len(new_memberships)} members so far...", flush=True)
            sys.stdout.flush()
        
        membershipData = getMembershipDataFromEmail(email["id"], service)

        if not membershipData:
            continue

        if isOlderThanTreshold(membershipData["timestamp"], hour_treshold):
            print(f"  Reached threshold, stopping at email {processed}...", flush=True)
            sys.stdout.flush()
            break

        new_memberships.append(membershipData)
    
    print(f"  ✓ Processed {processed} emails, found {len(new_memberships)} new members", flush=True)
    sys.stdout.flush()
    return new_memberships

if __name__ == '__main__':
    import sys
    print("Starting Gmail check...", flush=True)
    sys.stdout.flush()
    try:
        print("Setting up Gmail service...", flush=True)
        sys.stdout.flush()
        # Get new members from last 24 hours
        print("Calling getNewMembers(24)...", flush=True)
        sys.stdout.flush()
        new_members = getNewMembers(24)
        print(f"Retrieved {len(new_members)} new members", flush=True)
        sys.stdout.flush()
        
        # Sort by timestamp (newest first)
        new_members.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Save to JSON file in docs/ directory (served directly by GitHub Pages)
        # This way the file can be updated without rebuilding the React app
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(script_dir)
        output_path = os.path.join(repo_root, 'docs', 'newmembers.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"Saving data to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(new_members, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Found {len(new_members)} new members. Data saved to {output_path}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

