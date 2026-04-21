import pytest
import json
from unittest.mock import patch, mock_open
from webapp import app, phishing_email
from scrapy.http import HtmlResponse, Request
from crawler.webcrawler.webcrawler.spiders.website_crawler import UniWebCrawler


@pytest.fixture
def client():
    app.config['Testing'] = True
    with app.test_client() as client:
        yield client 


def test_home(client):
    response = client.get('/')
    assert response.status_code == 200 #testing that home page loads
    
def test_crawler(client):
    response = client.get('/crawler')
    assert response.status_code == 200 #test that crawler page loads

def test_email(client):
    response = client.get('/email')
    assert response.status_code == 200 # test that email page loads

def test_email_address(client):
    mock_email = [{
        'subject': 'test',
        'body': 'body',
        'sender_name': 'IT',
        'sender_email': 'it@test.local',
        'target_email': 'sandbox@test.local'
    }]
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_email))):
        with patch('webapp.mail.send'):
            response = client.post('/send_email', json={
                'recipient': 'sandbox@test.local',
                'emailIndex': 0
            })
            data=json.loads(response.data)
            assert data['status']=='success' # test that email info is made and sent correctly


def test_crawler_run(client):
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode=0
        mock_results = [{'type':'staff_profile','name': 'Test Name'}]
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_results))): #test to check that crawler outputs results
            response = client.post('/run-crawler')
            assert response.content_type == 'application/json'


# TESTS FOR EMAIL GENERATOR


def mock_ollama(content):
    """returns a mock ollama response with given string"""
    return{'message': {'content': content}}

def test_json_parsed():
    valid_json = json.dumps({
        'subject': 'Urgent',
        'body': 'Dear Dr Example...',
        'sender_name': 'example name',
        'sender_email': 'example@email.com'
    })
    with patch('ollama.chat', return_value=mock_ollama(valid_json)):
        profile = {'name': 'Dr Example', 'research_interests': ['AI']}
        result = phishing_email(profile, 'Urgent')
        assert result is not None
        assert result ['subject']== 'Urgent'
        assert result ['target_name'] == 'Dr Example'


def test_sandbox_defaults(): #test for if email is not there or encrypted, default to 'sandbox@test.local'
    valid_json = json.dumps({
        'subject': 'Test',
        'body': 'body',
        'sender_name': 'example name',
        'sender_email': 'example@email.com'
    })
    with patch('ollama.chat', return_value=mock_ollama(valid_json)):
        profile = {'name': 'Dr Example', 'research_interests': []}
        result = phishing_email(profile, 'Urgent')
        
        assert result ['target_email'] == 'sandbox@test.local'


#TESTS FOR WEBSITE CRAWLER

def fake_response(url, body):
    """Create a fake Scrapy HtmlResponse from an HTML string."""
    request = Request(url=url)
    return HtmlResponse(url=url, request=request, body=body, encoding='utf-8')



def test_staff_profile(): #test for staff profile extraction
    html = "<html><body><h1>Test Name</h1></body></html>"
    spider= UniWebCrawler()
    response = fake_response('https://research.brighton.ac.uk/persons/test_name', html)

    mock_ollama_response = {'message': {'content': json.dumps({
        'name': 'Test Name', 'job_name': None,
        'email':None,
        'research_interests': [], 'qualifications': []
    })}}

    with patch('ollama.chat', return_value=mock_ollama_response):
        results = list(spider.parse_staff_profile(response))

    assert results[0]['type'] == 'staff_profile'