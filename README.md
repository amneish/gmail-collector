## Installation

### 1. Python Setup
Run the following command in the project root:
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
Open `config.json`. This file tells the tool exactly which emails to look for and where to save them. You can edit this file with `notepad` or any other basic text editor.

```json
{
  "search_query": "subject:(the contract) label:work-project after:2024/01/01",
  "output_folder": "archived_emails",
  "pdf_filename": "consolidated_archive.pdf"
}
```

### 2. Execute the script

#### 2a. Using gmail_to_pdf.bat for Windows Users
double click on the file `gmail_to_pdf.bat`. A temporary terminal window will open displaying the progress of the tool. The terminal will display the output directory and consolidated email PDF created.

#### 2b. Using Python
Open your terminal or Command Prompt in the project directory (`<path-to-gmail-collector/>`) and run:
```bash
python -m gmail_to_pdf
```

### 3. Authorize the App (First run only)
- On the first run, your default web browser will open.
- Log in to your Gmail account.
- You may see a screen saying "Google hasn't verified this app" (this is normal for personal projects). Click Advanced > Go to [App Name] (unsafe).
- Click Allow to grant the tool read-only access to your emails.
- A file named token.json will be created in your folder. You won't need to log in again unless this file is deleted.

### 4. View Results
A progress bar will appear in your terminal. Once complete, navigate to your output_folder. You will find:
- A single PDF containing all email threads with their original formatting.
- All attachments from those emails saved individually in the same folder. Their names will be prepended with an ID to order them and make them easier to associate with the emails in the PDF.
   - Eg. `1 - <first_attachment_name>`, `2 - <second_attachment_name>`, etc.

## 🔍 Gmail Search Filter Guide

The `search_query` in your `config.json` uses standard Gmail syntax. You can combine multiple filters by simply listing them with spaces. For all query options see this [Help Page](https://support.google.com/mail/answer/7190)

### Essential Filters
| Filter | Description | Example |
| :--- | :--- | :--- |
| `from:` | Emails from a specific person | `from:name@example.com` |
| `to:` | Emails sent to a specific person | `to:name@example.com` |
| `cc:` | Finds emails where the address was Carbon Copied. | `cc:name@example.com` |
| `subject:` | Look for words in the subject line. Parentheses can be used to query a subject that uses multiple words | `subject:(company invoice)` |
| `has:attachment` | Only include emails with files | `has:attachment` |
| `newer_than:` / `older_than:` | Time-based from current date (d=days, m=months, y=years) | `newer_than:30d` |
| `after:` / `before:` | Specific date ranges (YYYY/MM/DD) | `before:2024/01/01` |
| `'Exact Phrase'` | Use single quotes to find a specific phrase (not case sensitive) | `'Contract'` |
| `label:` | Finds emails that you have tagged with a specific Gmail label | `label:Work` |
| `is:unread` | Only finds emails that you have not read yet | `is:unread` |

### Combining Filters with Operators

The filter operators can be combined using AND, OR, NOT, and Grouping logic.
| Operator Type | How to use it | Example query |
| :--- | :--- | :--- |
| AND | Space between filters | `from:boss has:attachment subject:Urgent` |
| OR | Capital `OR` | `from:apple OR from:google` |
| NOT | `-` (Minus: Excludes certain results) | `-from:noreply@ads.com` |
| Grouping | Parentheses `()` | `from:me (subject:Report OR subject:Update)` |

### Examples for how to use these in the config.json file

The following example will return every email that contains the word `Contract` or `contract` during 2023 and 2024.

```json
{
  "search_query": "'Contract' after:2023/01/01 before:2024/12/31",
  "output_folder": "archived_emails",
  "pdf_filename": "consolidated_archive.pdf"
}
```