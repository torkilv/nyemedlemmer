# GitHub Pages Setup Guide

This project is configured to run on GitHub Pages with a GitHub Actions cronjob checking Gmail for new member notifications.

## Setup Instructions

### 1. Update GitHub Pages Homepage

Edit `dashboard/package.json` and replace `YOUR_USERNAME` in the `homepage` field with your GitHub username:

```json
"homepage": "https://YOUR_USERNAME.github.io/nyemedlemmer"
```

### 2. Configure GitHub Secrets

You need to set up two secrets in your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

   - **GMAIL_CREDENTIALS**: The contents of your `credentials.json` file from Google Cloud Console
     - **Detailed instructions**: See [GMAIL_SETUP.md](./GMAIL_SETUP.md) for step-by-step guide
     - Quick version: Go to [Google Cloud Console](https://console.cloud.google.com/)
     - Create a project, enable Gmail API, create OAuth 2.0 credentials (Desktop app type)
     - Download the credentials JSON file
     - Copy the entire contents and paste as the secret value
     - **Note**: Works perfectly with 2FA - you'll enter your 2FA code during the OAuth flow

   - **GMAIL_TOKEN**: The contents of your `token-gmail.json` file
     - **Important**: This must be generated locally first (GitHub Actions can't do interactive OAuth)
     - Steps to generate:
       1. Place your `credentials.json` in the `server/` directory
       2. Run: `cd server && python check_gmail.py`
       3. Complete the OAuth flow in your browser
       4. Copy the contents of the generated `token-gmail.json` file
       5. Add it as the `GMAIL_TOKEN` secret
     - After setup, the token will be automatically refreshed by the workflow

### 3. Enable GitHub Pages (REQUIRED - Do this first!)

**⚠️ IMPORTANT:** The deployment workflow will fail until GitHub Pages is enabled!

1. Go to your repository on GitHub: `https://github.com/YOUR_USERNAME/nyemedlemmer`
2. Navigate to **Settings** → **Pages**
3. Under **"Build and deployment"** → **"Source"**, select **"GitHub Actions"**
4. The deployment will happen automatically when you push to the `master` branch

**Note:** After enabling GitHub Pages, you may need to trigger the workflow manually the first time (go to Actions tab → Deploy to GitHub Pages → Run workflow)

### 4. Adjust Cron Schedule (Optional)

The Gmail checker runs every 3 minutes by default. To change this, edit `.github/workflows/check-gmail.yml`:

```yaml
schedule:
  - cron: '*/3 * * * *'  # Change this to your desired schedule
```

Common cron schedules:
- `*/3 * * * *` - Every 3 minutes
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Every hour
- `0 */6 * * *` - Every 6 hours

### 5. First Run

1. Push your code to GitHub
2. The Gmail checker workflow will run automatically (or trigger it manually from Actions tab)
3. On first run, it may need OAuth authorization - check the workflow logs
4. The deployment workflow will build and deploy your React app to GitHub Pages

## How It Works

1. **Gmail Checker Workflow** (`.github/workflows/check-gmail.yml`):
   - Runs on a cron schedule (every 3 minutes by default)
   - Checks Gmail for new member notifications
   - Saves the data to `dashboard/public/newmembers.json`
   - Commits and pushes the updated JSON file

2. **Deployment Workflow** (`.github/workflows/deploy-pages.yml`):
   - Runs when code is pushed to `master` branch
   - Builds the React app
   - Deploys it to GitHub Pages

3. **React App** (`dashboard/src/NewMemberList.js`):
   - Fetches data from `/newmembers.json` (served as a static file)
   - Updates every 3 minutes (matching the cron schedule)

## Local Development

To test locally:

1. Install dependencies:
   ```bash
   cd dashboard
   npm install
   ```

2. Run the Gmail checker script:
   ```bash
   cd ../server
   python check_gmail.py
   ```

3. Start the React app:
   ```bash
   cd ../dashboard
   npm start
   ```

## Troubleshooting

- **Workflow fails with "credentials.json not found"**: Make sure you've set the `GMAIL_CREDENTIALS` secret
- **OAuth errors**: The first run may require manual OAuth approval. Check workflow logs for authorization URL
- **No data showing**: Check that the Gmail checker workflow is running successfully and updating the JSON file
- **Pages not deploying**: Make sure GitHub Pages is enabled and set to use "GitHub Actions" as the source

