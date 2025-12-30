## Installation

### 1. Python Setup
Once `wkhtmltopdf` is installed, run the following command in the project root:
```bash
pip install .
```

### 2. Google Gmail API Authentication Steps
To run this tool, you need to create a "Desktop App" credential in Google Cloud:

1. **Create Project**: Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2. **Enable API**: Go to "APIs & Services > Library", search for **Gmail API**, and click **Enable**.
3. **OAuth Consent Screen**:
   - Go to "APIs & Services" > "OAuth consent screen".
   - Select **Overview** and click Get Started.
   - Enter an App Name (e.g., "Gmail PDF Tool") and your email.
   - **Important**: Under "Test users", click **Add Users** and enter your own Gmail address. The tool will not work without this while in "Testing" mode.
4. **Create Credentials**:
   - Go to "Credentials" > "Create Credentials" > "OAuth client ID".
   - Select **Desktop app** as the application type.
   - Name it whatever you like and click Create.
5. **Download JSON**: Click the download icon (Download JSON) for the credential you just created. 
6. **Rename and Move**: Rename the file to `credentials.json` and move it into your project folder (`<path-to-gmail-collector\>`).

## How to Run the Tool

Follow these steps once you have completed the installation and Google API setup.

### 1. Configure your Search
Open `config.json` in your project folder. This file tells the tool exactly which emails to look for and where to save them.

```json
{
  "search_query": "category:primary label:work-project after:2024/01/01",
  "output_folder": "archived_emails",
  "pdf_filename": "consolidated_archive.pdf"
}
```

### 2. Execute the script
Open your terminal or Command Prompt in the project directory (`<path-to-gmail-collector/>`) and run:
```bash
python -m gmail_to_pdf
```

### 3. Authorize the App
- On the first run, your default web browser will open.
- Log in to your Gmail account.
- You may see a screen saying "Google hasn't verified this app" (this is normal for personal projects). Click Advanced > Go to [App Name] (unsafe).
- Click Allow to grant the tool read-only access to your emails.
- A file named token.json will be created in your folder. You won't need to log in again unless this file is deleted.

### 4. View Results
A progress bar will appear in your terminal. Once complete, navigate to your output_folder. You will find:
- A single PDF containing all email threads with their original formatting.
- All attachments from those emails saved individually in the same folder.