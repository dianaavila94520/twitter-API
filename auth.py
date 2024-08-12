import os
import json
from flask import Flask, redirect, request, session, url_for
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# App configuration
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

# OAuth 2.0 credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/callback")

# Define the OAuth 2.0 endpoints
AUTHORIZATION_BASE_URL = "https://api.twitter.com/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/oauth2/token"
REFRESH_URL = TOKEN_URL  # Twitter API may not use a separate refresh URL

CREDENTIALS_FILE = "twitter_credentials.json"

def save_credentials(username, credentials):
    """Save credentials for a specific user to a JSON file."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            all_credentials = json.load(file)
    else:
        all_credentials = {}
    
    all_credentials[username] = credentials
    
    with open(CREDENTIALS_FILE, 'w') as file:
        json.dump(all_credentials, file, indent=4)

def load_credentials(username):
    """Load credentials for a specific user from the JSON file."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            all_credentials = json.load(file)
            return all_credentials.get(username)
    return None

def refresh_access_token(oauth_session, refresh_token):
    """Refresh access token using the refresh token."""
    try:
        token = oauth_session.refresh_token(REFRESH_URL, refresh_token=refresh_token, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        return token
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None

def get_oauth_session(state=None, token=None):
    return OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        state=state,
        token=token
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle user login and redirect to Twitter for authentication."""
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            return "Username is required.", 400
        
        # Create an OAuth session
        oauth = get_oauth_session()
        authorization_url, state = oauth.authorization_url(AUTHORIZATION_BASE_URL)
        session['oauth_state'] = state
        session['username'] = username
        
        # Redirect user to Twitter for authentication
        return redirect(authorization_url)
    
    # Render login form
    return '''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Twitter Login</title>
        </head>
        <body>
            <h2>Login to Twitter</h2>
            <form method="POST" action="/">
                <label for="username">Username:</label><br>
                <input type="text" id="username" name="username" required><br><br>
                <input type="submit" value="Login">
            </form>
        </body>
        </html>
    '''

@app.route('/callback')
def callback():
    """Handle the callback from Twitter and exchange authorization code for tokens."""
    oauth = get_oauth_session(state=session['oauth_state'])
    token = oauth.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)

    # Save token for the user
    username = session.get('username')
    if username:
        save_credentials(username, token)
    
    return "Authentication successful! You can now use the app without reauthorization."

@app.route('/protected')
def protected():
    """A protected route that requires authentication."""
    username = request.args.get('username')
    if not username:
        return "Username parameter is required.", 400

    credentials = load_credentials(username)
    if not credentials:
        return redirect(url_for('index'))

    # Check if the access token is expired and refresh it if needed
    oauth = get_oauth_session(token=credentials)
    if oauth.token.is_expired():
        refresh_token = credentials.get('refresh_token')
        if refresh_token:
            new_token = refresh_access_token(oauth, refresh_token)
            if new_token:
                save_credentials(username, new_token)
                oauth = get_oauth_session(token=new_token)
            else:
                return "Failed to refresh token.", 401

    # Example API request (commented out)
    # response = oauth.get('https://api.twitter.com/1.1/account/verify_credentials.json')
    # return f"Protected content: {response.json()}"

    return "This is a protected area. You are authenticated!"

if __name__ == '__main__':
    app.run(host='http://10.204.205.129', port=int(os.getenv("PORT", 5000)))
