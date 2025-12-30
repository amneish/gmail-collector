import os
import json
import base64
import re
from tqdm import tqdm
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from xhtml2pdf import pisa
from bs4 import BeautifulSoup  # New cleaning library

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_html_body(payload):
    if payload.get('mimeType') == 'text/html':
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    if 'parts' in payload:
        for part in payload['parts']:
            html = get_html_body(part)
            if html: return html
    return ""

def clean_html(raw_html):
    if not raw_html:
        return ""
    
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # 1. Remove scripts, styles, meta, and images
    for tag in soup(["script", "style", "link", "meta", "img"]):
        tag.decompose()

    # 2. To prevent the PmlTable crash, we convert tables to divs 
    # but we will use CSS to make them invisible.
    for tag in soup.find_all(["table", "tr", "td", "th", "tbody", "thead"]):
        # Unwrapping keeps the content inside but removes the tag itself
        # This is the most "bulletproof" way to avoid the row-height error
        tag.unwrap() 

    # 3. Final scrub of remaining attributes
    for tag in soup.find_all(True):
        tag.attrs = {} # Clear all attributes (removes borders, colors, widths)

    return str(soup)

def convert_html_to_pdf(source_html, output_filename):
    with open(output_filename, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(source_html, dest=result_file, encoding='utf-8')
    return pisa_status.err

def main():
    with open('config.json') as f:
        config = json.load(f)

    service = get_gmail_service()
    results = service.users().messages().list(userId='me', q=config['search_query']).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return

    config['output_folder'] = 'output_folder/' + config['output_folder']

    if not os.path.exists(config['output_folder']):
        os.makedirs(config['output_folder'])

    combined_html = """
    <html>
    <head><meta charset="UTF-8"><style>
        @page { size: letter; margin: 0.75in; }
        body { 
            font-family: Helvetica, Arial, sans-serif; 
            font-size: 10pt; 
            line-height: 1.5; 
            color: #000000;
        }
        .email-container { 
            page-break-after: always; 
            margin-bottom: 30px;
        }
        .header { 
            background-color: #f8f8f8; 
            border-bottom: 1px solid #eeeeee;
            padding: 15px; 
            margin-bottom: 20px;
        }
        b { color: #333333; }
        /* Ensure no stray lines appear */
        div, p { border: none !important; outline: none !important; }
    </style></head>
    <body>
    """

    print(f"Found {len(messages)} messages. Processing...")
    for msg in tqdm(messages, desc="Processing Emails", unit="email"):
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = m['payload']
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        date = next((h['value'] for h in headers if h['name'] == 'Date'), "")

        raw_email_html = get_html_body(payload)
        safe_email_html = clean_html(raw_email_html)

        combined_html += f"<div class='email-container'>"
        combined_html += f"<div class='header'><b>Subject:</b> {subject}<br>"
        combined_html += f"<b>From:</b> {sender}<br><b>Date:</b> {date}</div>"
        combined_html += safe_email_html
        combined_html += "</div>"

        # Attachment logic
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    att_id = part['body'].get('attachmentId')
                    if att_id:
                        attachment = service.users().messages().attachments().get(
                            userId='me', messageId=msg['id'], id=att_id).execute()
                        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                        with open(os.path.join(config['output_folder'], part['filename']), 'wb') as f:
                            f.write(file_data)

    combined_html += "</body></html>"
    output_path = os.path.join(config['output_folder'], config['pdf_filename'])
    
    print("\nGenerating PDF...")
    error = convert_html_to_pdf(combined_html, output_path)
    
    if not error:
        print(f"\nSuccess! PDF created at: {output_path}")
    else:
        print("\nPDF Engine encountered minor layout issues, but the file may still be usable.")

if __name__ == '__main__':
    main()