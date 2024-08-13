from flask import Flask, redirect, url_for, session, request
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Use a strong, secure key for session management

# OAuth 2.0 configuration
TWITTER_CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
TWITTER_CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
TWITTER_REDIRECT_URI = os.getenv('TWITTER_REDIRECT_URI')

oauth = OAuth2Session(
    client_id=TWITTER_CLIENT_ID,
    redirect_uri=TWITTER_REDIRECT_URI,
    scope=['tweet.read', 'users.read']
)
authorization_base_url = 'https://api.twitter.com/oauth2/authorize'
token_url = 'https://api.twitter.com/oauth2/token'

@app.route('/login')
def login():
    authorization_url, state = oauth.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    oauth.fetch_token(token_url, authorization_response=request.url,
                      client_secret=TWITTER_CLIENT_SECRET)
    user_info = oauth.get('https://api.twitter.com/2/users/me').json()
    
    user_id = user_info['data']['id']
    if 'users' not in session:
        session['users'] = {}
    session['users'][user_id] = {
        'access_token': oauth.token['access_token'],
        'refresh_token': oauth.token.get('refresh_token')
    }
    
    return f"Logged in as {user_info['data']['name']}"

@app.route('/profile')
def profile():
    user_id = request.args.get('user_id')
    if not user_id or user_id not in session.get('users', {}):
        return "User not found or not authenticated."
    
    user_data = session['users'][user_id]
    return f"User data: {json.dumps(user_data)}"

@app.route('/refresh_token/<user_id>')
def refresh_token(user_id):
    if user_id not in session.get('users', {}):
        return "User not found."

    user_data = session['users'][user_id]
    if 'refresh_token' not in user_data:
        return "No refresh token available."

    oauth.refresh_token(token_url, refresh_token=user_data['refresh_token'])
    session['users'][user_id]['access_token'] = oauth.token['access_token']
    session['users'][user_id]['refresh_token'] = oauth.token.get('refresh_token')

    return f"Token refreshed for user {user_id}"

if __name__ == '__main__':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host='0.0.0.0', port=8000, threaded=True)
