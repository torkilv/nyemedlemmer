# Gmail API Credentials Setup with 2FA

This guide explains how to create Gmail API credentials for an account with SMS two-factor authentication (2FA) enabled.

## Important Note

**OAuth 2.0 works perfectly with 2FA!** When you authorize the application, Google will prompt you for your 2FA code during the OAuth flow. This is actually more secure than using App Passwords.

## Step-by-Step Instructions

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "MDG Member Dashboard")
5. Click "Create"
6. Wait for the project to be created, then select it from the dropdown

### 2. Enable Gmail API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click on "Gmail API" in the results
4. Click **Enable**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (unless you have a Google Workspace account)
3. Click **Create**
4. Fill in the required information:
   - **App name**: e.g., "MDG Member Dashboard"
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **Save and Continue**
6. On the **Scopes** page:
   - Click **Add or Remove Scopes**
   - Search for and select: `https://www.googleapis.com/auth/gmail.readonly`
   - Click **Update**, then **Save and Continue**
7. On the **Test users** page (if in testing mode):
   - Click **Add Users**
   - Add your Gmail address
   - Click **Add**
   - Click **Save and Continue**
8. Review and click **Back to Dashboard**

### 4. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure the OAuth consent screen (you should have done this in step 3)
4. Choose **Application type**: **Desktop app**
5. Give it a name (e.g., "Gmail API Client")
6. Click **Create**
7. A dialog will appear with your **Client ID** and **Client Secret**
   - **Important**: Copy these or download the JSON file
   - Click **Download JSON** to save the credentials file
   - Rename this file to `credentials.json`

### 5. Download the Credentials File

The downloaded file will look something like this:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

**Save this file as `credentials.json` in the `server/` directory.**

### 6. Generate the Token (This is where 2FA comes in)

1. Place `credentials.json` in the `server/` directory
2. Install required Python packages:
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib oauth2client
   ```
3. Run the script:
   ```bash
   cd server
   python check_gmail.py
   ```

4. **During the OAuth flow:**
   - A browser window will open
   - You'll be asked to sign in to your Google account
   - **Enter your password**
   - **Google will then prompt for your 2FA code** (SMS, authenticator app, etc.)
   - Enter your 2FA code
   - You'll see a warning about "Google hasn't verified this app" - click **Advanced** → **Go to [Your App Name] (unsafe)**
   - Click **Allow** to grant permissions
   - The browser will show "The authentication flow has completed"

5. The script will generate `token-gmail.json` in the `server/` directory

### 7. Add Secrets to GitHub

1. **GMAIL_CREDENTIALS secret:**
   - Open `server/credentials.json`
   - Copy the entire contents
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GMAIL_CREDENTIALS`
   - Value: Paste the entire JSON contents
   - Click "Add secret"

2. **GMAIL_TOKEN secret:**
   - Open `server/token-gmail.json`
   - Copy the entire contents
   - Create a new secret named `GMAIL_TOKEN`
   - Paste the JSON contents
   - Click "Add secret"

## Troubleshooting 2FA Issues

### "This app isn't verified" Warning

This is normal for apps in testing mode. To proceed:
1. Click **Advanced**
2. Click **Go to [Your App Name] (unsafe)**
3. Click **Allow**

### OAuth Flow Doesn't Open Browser

If running on a remote server or in an environment without a browser:
1. The script will print an authorization URL
2. Copy the URL
3. Open it in your local browser
4. Complete the 2FA flow
5. Copy the authorization code from the browser
6. Paste it back into the terminal

### Token Expires

OAuth tokens can expire. The `oauth2client` library should automatically refresh them using the refresh token. If you get authentication errors:
1. Delete `token-gmail.json`
2. Run `python check_gmail.py` again
3. Complete the OAuth flow again (including 2FA)
4. Update the `GMAIL_TOKEN` secret with the new token

### "Access blocked: This app's request is invalid"

This usually means:
- The OAuth consent screen isn't properly configured
- Your email isn't added as a test user (if in testing mode)
- The scopes don't match

**Solution:** Go back to OAuth consent screen settings and ensure:
- Your email is in the test users list
- The `gmail.readonly` scope is added

## Security Notes

- **Never commit `credentials.json` or `token-gmail.json` to git**
- These files should be in `.gitignore`
- Use GitHub Secrets to store them securely
- The refresh token in `token-gmail.json` allows the app to access your Gmail without re-authenticating
- You can revoke access at any time: [Google Account Security](https://myaccount.google.com/permissions)

## Alternative: Service Account (Not Recommended for Gmail)

Service accounts don't work well with Gmail API for personal accounts. OAuth 2.0 with 2FA is the recommended approach.

