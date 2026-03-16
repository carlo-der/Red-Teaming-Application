from flask import Flask, render_template, jsonify, request
from flask_mail import Mail, Message
import subprocess
import json
import os
import ollama

app=Flask(__name__)

app.config['MAIL_SERVER']='localhost'
app.config['MAIL_PORT']= 1025
app.config['MAIL_USE_TLS']= False
app.config['MAIL_USE_SSL']=False

mail=Mail(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/crawler')
def crawler():
    return render_template('index.html')

@app.route('/email')
def email_generator():
    return render_template('email.html')

@app.route('/run-crawler', methods=['POST'])
def run_crawler():
    output_file = 'crawler_results.json'

    if os.path.exists(output_file):
        os.remove(output_file)


    
    try:
        result = subprocess.run(
            [ 'python3', '-m', 'scrapy', 'runspider', 'crawler/webcrawler/webcrawler/spiders/website_crawler.py', '-o', output_file,],
            

            capture_output=True, text=True, check=True, timeout=600
        )

        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                file_content= f.read().strip()
                if not file_content:
                    data = []
                else:
                    

                    try:
                        data =json.loads(file_content)
                    except json.JSONDecodeError:

                        f.seek(0)
                        data= []
                        for line in f:
                            if line.strip():
                                data.append(json.loads(line))
                return jsonify({
                    'status': 'success',
                    'data': data,
                    'message': f'Found {len(data)} items'
                })

        else:
            return jsonify({
                'status': 'error',
                'message': 'No results file created'
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'Error',
            'message': 'Crawler Timed Out'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'Error',
            'message': str(e)
        })

    pass


@app.route('/email-generator', methods=['POST'])
def generate_emails():
    try:
        template_type = request.json.get('template', 'conference')

        if not os.path.exists('crawler_results.json'):
            return jsonify({
                'status': 'error',
                'message': 'No crawler results found. The crawler must be run before emails can be generated.'
            })

        with open('crawler_results.json', 'r') as f:
            crawler_data=json.load(f)

        staff_profiles =[item for item in crawler_data if item.get('type')=='staff_profile']

        if not staff_profiles:
            return jsonify({
                'status': 'error',
                'message': 'No staff profiles found in crawler results.'
            })

        emails =[]
        for profile in staff_profiles:
            email= phishing_email(profile, template_type)
            if email:
                emails.append(email)

        with open('email.json', 'w') as f:
            json.dump(emails, f, indent=2)

        return jsonify ({
            'status': 'success',
            'emails': emails,
            'count': len(emails)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/send_email', methods=['POST'])
def sendEmail():

    try: 
        data= request.json
        index= data.get("emailIndex")
        recipient= data.get('recipient')

        if not recipient.endswith('@test.local'):
            return jsonify({
                'status': 'error',
                'message': 'Emails can only be sent to the sandboxed inbox'
            })

        if not os.path.exists('email.json'):
            return jsonify({
                'status': 'error',
                'message': 'Cannot find generated emails'
            })

        with open('email.json', 'r') as f:
            emails= json.load(f)

        if index >= len(emails):
            return jsonify({
                'status': 'error',
                'message': 'Index not in range'
            })

        emailData = emails[index]

        message = Message(
            subject=emailData['subject'],
            sender=(emailData['sender_name'], emailData['sender_email']),
            recipients=[recipient]
        )
        message.body=emailData['body']

        mail.send(message)

        return jsonify ({
            'status': 'success',
            'message': 'Email sent to {recipient} in sanboxed inbox'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

def phishing_email(profile, template_type):

    name= profile.get('name', 'Staff Member')
    if not name or name is None:
        name= 'Staff Member'

    print(f"Generating Emails for: {name}")
    interests = profile.get('research_interests', [])
    interests_info=', '.join([i for i in interests if i]) if interests else 'general'

    #List of templates for LLM to be prompted with for email generation based on dropdown menu choice by user

    templates ={
        'urgent': f"""You are helping to create educational training content for an authorised university project foucsing on cybersecurity awareness.
TASK: write a simulated urgent IT security email that will be used ONLY for the training of staff and personel to recognise possible phishing attemps.

Training participant name: {name}
Their research interests: {interests}
Email type: {template_type}

Wrire a realistic {template_type} email that is clearly simulated and shows common phishing tactics. the email must:
1. Addresses {name} personally.
2. Creates a sense of urgency relating to account security
3. Includes a suspicious link [PHISHING__SIMULATION_LINK]
4. is 2-3 paragraphs long demonstrating typical phishing language patterns

CRITICAL: Return ONLY valid JSON with no extra text before or after. All strings must use double quotes and add commas between all fields. {{
    "subject": "an email subject about {template_type}
    "body": "the actual email text goes here, 2-3 paragraphs. Use actual line breaks, do not use \\n or anything similar.
    "sender_name": "example IT staff name"
    "sender_email": "a realistic email address like john.smith@hr.com"
}}

Rules:
1. No trailing commas
2. Use double quotes for all strings
3. Put commas afte every field except the last
4. Return ONLY the JSON object, nothing else

Write the ACTUAL email content with no placeholders. Please remember that this is educational material not actual phishing."""
    }

    prompt = templates.get(template_type, templates['urgent'])
    


    try:
        result = ollama.chat(
            model='qwen2.5:3b',
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            format='json'
        )

        response_text=result['message']['content'].strip()

        print("="*60)
        print(f"raw ollama response for {name}:")
        print(response_text)
        print("="*60)


        
        

        

        email_data = json.loads(response_text)

        req = ['subject', 'body', 'sender_name', 'sender_email']
        if not all (k in email_data for k in req):
            print(f"Missing fields for {name}: {email_data.keys()}")
            return None

        
        email_data['target_name'] = name
        email_data['target_email']=profile.get('email', 'sandbox@test.local')
        email_data['template_type'] = template_type

        return email_data

    except Exception as e:
        print(f"Error occurred whilst generating email for {name}: {e}")
        return None



if __name__ == '__main__':
    print("=== REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")
    print("=" * 40)
    app.run(debug=True)