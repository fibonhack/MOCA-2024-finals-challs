from base64 import b64encode
import requests
import os

def get_ebay_access_token(client_id, client_secret):
    encoded_creds = (b64encode(bytes(client_id+":"+client_secret, 'utf-8'))).decode()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_creds}',
    }

    data = {
        'grant_type': 'client_credentials',
        'scope': f'https://api.ebay.com/oauth/api_scope', 
    }

    response = requests.post("https://api.ebay.com/identity/v1/oauth2/token", headers=headers, data=data)
    response_content = response.json()
    try:
        if response_content["access_token"]:
            return response_content["access_token"]
    except:
        raise Exception("Ebay API connection went wrong")

def api_research(base_url, access_token, search_param):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    params = {
        "q": f"{search_param}",
        "limit": 1
    }
    response = requests.get(base_url+"/buy/browse/v1/item_summary/search", headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()["itemSummaries"][0]
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return {}

def ebay_research(base_url, search_param):
    client_id = os.environ.get('EBAY_CLIENT_ID', '')
    client_secret = os.environ.get('EBAY_CLIENT_SECRET', '')
    token = get_ebay_access_token(client_id, client_secret)
    result = api_research(f"{base_url.scheme}://{base_url.netloc}", token, search_param)
    return result
