import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

def course_extractor(url_moodle):
    url_text = requests.get(url_moodle).text

    cleaned_text = BeautifulSoup(url_text, "html.parser").get_text()
    cleaned_text = cleaned_text.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()
    cleaned_text_split = cleaned_text.split("Aktion")[1]

    text = re.split(r'(?=\d{6})', cleaned_text_split)
    text = [i for i in text if len(i) > 2]

    subjects = []
    status = []
    for enum, i in enumerate(text):
        try:
            parsed_text, status_text = i.rsplit("-", 1)
        except:
            parsed_text = i
            status_text = i 
        subjects.append(parsed_text.strip())
        status.append(status_text.strip())

    df = pd.DataFrame({"subject": subjects, "status": status})
    df['apply'] = df['status'].apply(lambda x: 1 if "belegen" in x or "abmelden" in x else 0)
    df = df.dropna(subset=['subject', 'status'])
    return df

def send_email():
    load_dotenv()
    url_moodle = os.environ["moodle_link"]
    df = course_extractor(url_moodle)
    df_filtered = df[df['apply'] == 1]
    df_filtered_subjects = df_filtered['subject'].tolist()
    
    if not df_filtered.empty:
        msg = EmailMessage()
        msg["From"] = os.environ["GMAIL_ADDRESS"]
        msg["To"] = os.environ["RECIPIENT_EMAIL"]
        msg["Subject"] = "Apply"
        msg.set_content(f"The following courses are available for enrollment or deregistration: {', '.join(df_filtered_subjects)}")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(
                os.environ["GMAIL_ADDRESS"],
                os.environ["GMAIL_APP_PASSWORD"]
            )
            smtp.send_message(msg)

        print("Email sent successfully!", msg)
    else:
        print("No courses available for enrollment or deregistration.", msg)

if __name__ == "__main__":
    send_email()
