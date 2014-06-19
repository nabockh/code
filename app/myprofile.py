import oauth2 as oauth
import httplib2
import time, os, simplejson

 
# Fill the keys and secrets you retrieved after registering your app
consumer_key      =   '77pi0tgejrq7si'
consumer_secret  =   'ZneKr9tbVPSSrm5O'
 
# Use your API key and secret to instantiate consumer object
consumer = oauth.Consumer(consumer_key, consumer_secret)
 
# Use the consumer object to initialize the client object
client = oauth.Client(consumer)
 
# "{"first_name": "Oleg", "last_name": "Kushynsky", "access_token": "oauth_token_secret=dfef9ee5-8437-4bc6-9406-66305dc010bc&oauth_token=046c9e52-b886-424f-a153-661998643425", "id": "0hMQQoVi_l"}"
# Use your developer token and secret to instantiate access token object
access_token = oauth.Token(
            key=   '92fdf41f-c4d4-48dd-9c75-c2d2c068c823',
            secret='42ca5cb7-6837-4194-9a9c-922faeb2d8ba')

# access_token = "oauth_token_secret=bb323eb0-812b-44a2-ad58-e1e07eb19e0c&oauth_token=d399b742-6a65-4bee-9c5f-dc2e00c49a51" 
client = oauth.Client(consumer, access_token)
 
# Make call to LinkedIn to retrieve your own profile
# resp,content = client.request("http://api.linkedin.com/v1/people/~/connections", "GET", "")
# resp,content = client.request("http://api.linkedin.com/v1/people/~/connections:(headline,first-name,last-name,positions)?count=10", "GET", "")
resp,content = client.request("http://api.linkedin.com/v1/people/yAxz9X2Lvf:(headline,first-name,last-name,positions)", "GET", "")
# resp,content = client.request("http://api.linkedin.com/v1/people/~:(headline,first-name,last-name,skills,email-address)", "GET", "")

print content 
# By default, the LinkedIn API responses are in XML format. If you prefer JSON, simply specify the format in your call
# resp,content = client.request("http://api.linkedin.com/v1/people/~?format=json", "GET", "")

# from xml.etree import ElementTree

# # tree = ElementTree.parse("connections.xml")
# tree = ElementTree.fromstring(content)
# for node in tree.findall('./person'):
#     print u'{} {}, {}'.format(node.find('first-name').text.decode('ascii', 'ignore'), node.find('last-name').text.decode('ascii', 'ignore'), node.find('headline').text.encode('ascii'))


def send_message():
    consumer_key     =   '77pi0tgejrq7si'
    consumer_secret  =   'ZneKr9tbVPSSrm5O'

    user_key    = '92fdf41f-c4d4-48dd-9c75-c2d2c068c823'
    user_secret = '42ca5cb7-6837-4194-9a9c-922faeb2d8ba'
    
    url = "http://api.linkedin.com/v1/people/~/mailbox"
     
    consumer = oauth.Consumer(
            key=consumer_key,
            secret=consumer_secret)
            
    token = oauth.Token(
            key=user_key, 
            secret=user_secret)
     
     
    client = oauth.Client(consumer, token)
    body = {
        "recipients": {
            "values": [
                {
                  "person": {
                    "_path": "/people/~",
                   }
                }
                # {
                #   "person": {
                #     "_path": "/people/yAxz9X2Lvf",
                #    }
                # },
                # {
                #   "person": {
                #     "_path": "/people/dOo41AWRhm",
                #    }
                # }
                ]
        },
        "subject": "Congratulations - API message #1",
        "body": "You are certainly the best person for the job! http://mighty-shore-9697.herokuapp.com/movies"
    }
               
     
    resp, content = client.request(url, 'POST', body=simplejson.dumps(body), headers={'Content-Type':'application/json'})
    print resp
    print content

send_message()
