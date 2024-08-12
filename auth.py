import json
import os
from requests_oauthlib import OAuth1Session
from requests.exceptions import RequestException

# File to save credentials
CREDENTIALS_FILE = "twitter_credentials.json"

def authenticate():
    """
    Authenticates with Twitter API and saves the credentials to a file.
    
    Returns:
        tuple: Contains consumer_key, consumer_secret, access_token, and access_token_secret.
    """
    consumer_key = os.environ.get("CONSUMER_KEY")
    consumer_secret = os.environ.get("CONSUMER_SECRET")

    if not consumer_key or not consumer_secret:
        raise ValueError("Consumer key or consumer secret is missing. Ensure both are set in environment variables.")

    # Check if credentials file exists and read credentials from it
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as file:
                creds = json.load(file)
                return (
                    creds["consumer_key"],
                    creds["consumer_secret"],
                    creds["access_token"],
                    creds["access_token_secret"]
                )
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Error reading credentials file: {e}")

    # If credentials file doesn't exist, proceed with authentication
    try:
        # Get request token
        request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
        oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
        fetch_response = oauth.fetch_request_token(request_token_url)

        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")

        # Get authorization
        base_authorization_url = "https://api.twitter.com/oauth/authorize"
        authorization_url = oauth.authorization_url(base_authorization_url)
        
        print("Please go here and authorize:", authorization_url)
        verifier = input("Paste the PIN here: ")

        # Get the access token
        access_token_url = "https://api.twitter.com/oauth/access_token"
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier
        )
        oauth_tokens = oauth.fetch_access_token(access_token_url)

        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]

        # Save the credentials to a file
        with open(CREDENTIALS_FILE, 'w') as file:
            json.dump({
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
                "access_token": access_token,
                "access_token_secret": access_token_secret
            }, file)

        return consumer_key, consumer_secret, access_token, access_token_secret

    except RequestException as e:
        raise RuntimeError(f"Error during authentication: {e}")

if __name__ == '__main__':
    try:
        authenticate()
    except Exception as e:
        print(f"Authentication failed: {e}")
