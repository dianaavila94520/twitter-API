import os
import json
from flask import Flask, request, redirect, url_for
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# App configuration
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

# OAuth 1.0a credentials (for Twitter API)
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

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

def get_oauth_session(token=None):
    return OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=token.get("oauth_token") if token else ACCESS_TOKEN,
        resource_owner_secret=token.get("oauth_token_secret") if token else ACCESS_TOKEN_SECRET
    )

@app.route('/')
def index():
    """Redirect to Twitter for authentication."""
    oauth = get_oauth_session()
    request_token_url = "https://api.twitter.com/oauth/request_token"
    
    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        
        authorization_url = oauth.authorization_url("https://api.twitter.com/oauth/authorize")
        return redirect(authorization_url)
    except Exception as e:
        return f"Error during authentication: {e}", 500

@app.route('/callback')
def callback():
    """Handle the callback from Twitter and exchange authorization code for tokens."""
    oauth = get_oauth_session()
    access_token_url = "https://api.twitter.com/oauth/access_token"
    verifier = request.args.get('oauth_verifier')
    
    try:
        oauth_tokens = oauth.fetch_access_token(access_token_url, verifier=verifier)
        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]
        
        # Save credentials for the user (could use a default username or handle differently)
        save_credentials("default_user", {
            "oauth_token": access_token,
            "oauth_token_secret": access_token_secret
        })
        
        return "Authentication successful! You can now use the app."
    except Exception as e:
        return f"Error during token exchange: {e}", 500

@app.route('/protected')
def protected():
    """Access protected Twitter API endpoints."""
    credentials = load_credentials("default_user")
    if not credentials:
        return redirect(url_for('index'))

    oauth = get_oauth_session(token=credentials)
    api_url = "https://api.twitter.com/1.1/account/verify_credentials.json"
    
    try:
        response = oauth.get(api_url)
        return f"Protected content: {response.json()}"
    except Exception as e:
        return f"Error accessing protected content: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
