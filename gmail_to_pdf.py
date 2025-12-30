import os
import json
import base64
import shutil
from tqdm import tqdm
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from xhtml2pdf import pisa
from bs4 import BeautifulSoup
from email.utils import parseaddr

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

    # 2. Prevent PmlTable crashes by converting tables to divs
    for tag in soup.find_all(["table", "tr", "td", "th", "tbody", "thead"]):
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

    # Calculate full paths for clarity
    full_output_dir = os.path.abspath(config['output_folder'])
    full_pdf_path = os.path.join(full_output_dir, config['pdf_filename'])
    full_config_path = os.path.abspath('config.json')

    print("\n" + "="*60)
    print("              GMAIL ARCHIVE SESSION")
    print("="*60)
    print(f"Config File:   {full_config_path}")
    print(f"Search Query:  {config.get('search_query')}")
    print(f"Output Dir:    {full_output_dir}")
    print(f"PDF Filename:  {config.get('pdf_filename')}")
    print("="*60 + "\n")

    service = get_gmail_service()
    results = service.users().messages().list(userId='me', q=config['search_query']).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return

    # Reverse order of messages so the appear from oldest to newest
    messages.reverse()

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

    # Initialize the email_id_counter    
    email_id_counter = 1

    print(f"Found {len(messages)} messages. Processing...")
    for msg in tqdm(messages, desc="Processing Emails", unit="email"):
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = m['payload']
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        full_from = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        _, sender = parseaddr(full_from)
        full_to = next((h['value'] for h in headers if h['name'] == 'To'), "Unknown")
        _, receiver = parseaddr(full_to)
        date = next((h['value'] for h in headers if h['name'] == 'Date'), "")

        # 1. Collect Attachment Filenames and Save Them
        attachment_names = []
        attachment_counter = 1
        if 'parts' in payload:
            for part in payload['parts']:
                original_filename = part.get('filename')
                if original_filename:
                    new_filename = f"{email_id_counter}-{attachment_counter} - {original_filename}"
                    attachment_names.append(new_filename)
                    
                    att_id = part['body'].get('attachmentId')
                    if att_id:
                        attachment = service.users().messages().attachments().get(
                            userId='me', messageId=msg['id'], id=att_id).execute()
                        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                        
                        with open(os.path.join(config['output_folder'], new_filename), 'wb') as f:
                            f.write(file_data)
                        
                        # Increment the counter for the next attachment found
                        attachment_counter += 1

        # 2. Use the list of new filenames for the PDF header
        att_str = ", ".join(attachment_names) if attachment_names else "None"

        # 3. Build the Header with Attachment Metadata
        raw_email_html = get_html_body(payload)
        safe_email_html = clean_html(raw_email_html)

        combined_html += f"<div class='email-container'>"
        combined_html += f"<div class='header'>"
        combined_html += f"<b>Email #:</b> {email_id_counter}/{len(messages)}<br>"
        combined_html += f"<b>Subject:</b> {subject}<br>"
        combined_html += f"<b>From:</b> {sender}<br>"
        combined_html += f"<b>To:</b> {receiver}<br>"
        combined_html += f"<b>Date:</b> {date}<br>"
        combined_html += f"<b>Attachments:</b> {att_str}" # New metadata line
        combined_html += f"</div>"
        combined_html += safe_email_html
        combined_html += "</div>"

        email_id_counter += 1

    combined_html += "</body></html>"
    output_path = os.path.join(config['output_folder'], config['pdf_filename'])
    
    print("\nGenerating PDF...")
    error = convert_html_to_pdf(combined_html, output_path)
    
    if error:
        print("\nPDF Engine encountered minor layout issues, but the file may still be usable.")

    # Copy config.json to the output folder
    try:
        config_destination = os.path.join(config['output_folder'], 'config.json')
        shutil.copy2('config.json', config_destination)
    except Exception as e:
        print(f"Could not copy config file: {e}")

    # Print summary of run
    print("\n" + "="*60)
    print("SUCCESS: ARCHIVE GENERATED")
    print("="*60)
    print(f"Consolidated PDF: {full_pdf_path}")
    print(f"Reference Config: {os.path.join(full_output_dir, 'config.json')}")
    print("="*60)

if __name__ == '__main__':
    main()