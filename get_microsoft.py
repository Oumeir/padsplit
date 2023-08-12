import requests
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from requests.exceptions import MissingSchema, RequestException, Timeout
import concurrent.futures
import time

# Connect to the MongoDB
client = MongoClient("mongodb+srv://badr:ZzXx@badr.p8vevwi.mongodb.net/test")
db = client["newAutomation"]

m_collection = db["microsoft"]
login_collection = db["loginUrls"]


def search_for_microsoft(loginUrl, website, body_content):
    if (len(body_content) < 1):
        print('No body')
        m_collection.insert_one(
            {'website': website, 'oauth': 'unknown'}
        )
        return

    else:

        pattern = re.compile(r"(continue with microsoft|login with microsoft|log in with microsoft|sign in with microsoft|microsoft.svg|log in using your microsoft|microsoft account|sign up with microsoft|microsoft login|microsoft sign in|365 login|microsoft connect|access with microsoft|authorize with microsoft|ms login|microsoft credentials|ms account access|microsoft sso|ms sso|oauth microsoft|microsoft oauth2|microsoft ad login|login with ms account|azure ad login|use microsoft account|connect microsoft|microsoft sign on|verify with microsoft|enter with microsoft|join with microsoft|microsoft passport|microsoft federation|microsoft linked login|windows login|use microsoft credentials|authenticate with microsoft|microsoft auth|office login|ms auth|outlook login|signin with ms|proceed with microsoft|authenticate through microsoft|login via microsoft|use your microsoft account|login using ms|microsoft oauth login|one drive)", re.IGNORECASE)
        match_body = pattern.search(body_content)

        drop_pattern = re.compile(r"(dropbox)", re.IGNORECASE)

        if match_body:
            print(' => microsoft')
            m_collection.insert_one(
                {'website': website, 'oauth': 'microsoft', 'loginUrl': loginUrl}
            )

        else:
            print('noMicrosoft')
            m_collection.insert_one(
                {'website': website, 'oauth': 'noMicrosoft'}
            )


def handle_website(document):
    website = document['website']
    login = document['login']

    try:

        if login.startswith('//'):
            login = 'https:'+login
        elif login.startswith('/'):
            login = website+login
        if login[:4] != 'http':
            login = 'https://'+login

        response = requests.get(login, timeout=10)

        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')

        for script in soup("script"):
            script.decompose()

        # Search for the specified words in the page tags
        if soup.body:
            search_for_microsoft(login, website, soup.body.text)

    except RequestException:
        print('unknown')
        m_collection.insert_one(
            {'website': website, 'oauth': 'URL FAILD'}
        )
    except Exception as e:
        print('unknown')
        m_collection.insert_one(
            {'website': website, 'oauth': 'unknown'}
        )


def check_websites():

    login_documents = login_collection.find()

    login_documents_list = list(login_documents)

    print('check on:', len(login_documents_list))

    # Using ThreadPoolExecutor to run handle_website() for each website simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(handle_website, login_documents_list)


check_websites()
