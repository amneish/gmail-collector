from setuptools import setup, find_packages

setup(
    name="gmail_consolidator",
    version="0.1.0",
    description="A tool to consolidate Gmail emails into a single formatted PDF with attachments.",
    author="Andrew Neish",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "xhtml2pdf",
        "tqdm",
        "beautifulsoup4",
    ],
    entry_points={
        "console_scripts": [
            "gmail-pdf=gmail_to_pdf:main",
        ],
    },
    python_requires=">=3.7",
)