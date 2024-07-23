import email
import imaplib
import smtplib
import speech_recognition as sr
from email.message import EmailMessage
import pyttsx3
import sched
import time
from datetime import datetime, timedelta


scheduler = sched.scheduler(time.time, time.sleep)

listener = sr.Recognizer()
tts = pyttsx3.init()

rate = tts.getProperty('rate')
volume = tts.getProperty('volume')
voices = tts.getProperty('voices')

tts.setProperty('rate', 140)
tts.setProperty('volume', 1)
tts.setProperty('voice', voices[1].id)

def speak(text):
    tts.say(text)
    tts.runAndWait()

def mic(duration):
    with sr.Microphone() as source:
        speak("program is listening....")
        listener.adjust_for_ambient_noise(source, duration = 1)
        voice = listener.listen(source, phrase_time_limit = duration)
    try:
        data = listener.recognize_google(voice)
        speak("you have said " + data)
        print("the text you said " + data)
        return data.lower()
    except:
        speak("Sorry i could not catch the phrase, could you please repeat that again")
        mic(3)


def send_mail(receiver, subject, body):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("toby26336@gmail.com", "hqgibwvvqmgriaaq")
    email = EmailMessage()
    email['From'] = "toby26336@gmail.com"
    email['To'] = receiver
    email['Subject'] = subject
    email.set_content(body)
    server.send_message(email)

def schedule_mail(receiver, subject, body, send_time):
    def send_scheduled_mail():
        send_mail(receiver, subject, body)
        speak("Your scheduled email has been sent successfully to the receiver.")
    
    scheduler.enterabs(send_time, 1, send_scheduled_mail)
    speak("Your email has been scheduled successfully.")
    scheduler.run()



def read_mail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("toby26336@gmail.com", "hqgibwvvqmgriaaq")
    mail.select("inbox")
    result, data = mail.search(None, "ALL")

    mail_ids = data[0].split()
    latest_email_id = mail_ids[-1]
    
    result, data = mail.fetch(latest_email_id, "(RFC822)")
    
    raw_email = data[0][1]
    msg = email.message_from_bytes(raw_email)
    
    email_from = msg["from"]
    email_subject = msg["subject"]
    email_body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                email_body = part.get_payload(decode=True).decode()
                break
    else:
        email_body = msg.get_payload(decode=True).decode()
    
    speak(f"Email from {email_from}")
    speak(f"Subject: {email_subject}")
    speak(f"Body: {email_body}")
    print(f"Email from: {email_from}")
    print(f"Subject: {email_subject}")
    print(f"Body: {email_body}")

def get_time_from_user():
    speak("Please say the time to send the email. For example, say 'in 10 minutes' or 'tomorrow at 3 PM'.")
    time_phrase = mic(5)

    current_time = datetime.now()
    
    if "minute" in time_phrase:
        number = int([word for word in time_phrase.split() if word.isdigit()][0])
        send_time = current_time + timedelta(minutes=number)
    elif "hour" in time_phrase:
        number = int([word for word in time_phrase.split() if word.isdigit()][0])
        send_time = current_time + timedelta(hours=number)
    elif "tomorrow" in time_phrase:
        time_part = time_phrase.split("at")[-1].strip()
        send_time = datetime.strptime(f"{current_time.year}-{current_time.month}-{current_time.day} {time_part}", '%Y-%m-%d %I %p') + timedelta(days=1)
    else:
        send_time = parse_time(time_phrase)
    
    return send_time.timestamp() if send_time else None


def parse_time(input_time):
    try:
        return datetime.strptime(input_time, '%Y-%m-%d %H:%M:%S').timestamp()
    except ValueError:
        speak("Sorry, the time format is incorrect. Please provide the time in the format YYYY-MM-DD HH:MM:SS.")
        return None

def main_code():
    speak("Hi, this is your email voice assistant.")
    speak("Do you want to read mail, compose mail, or schedule mail?")
    choice = mic(3)
    
    if "read" in choice:
        speak("Reading recent mail from your inbox")
        read_mail()
    elif "compose" in choice:
        speak("Whom do you want to send the email?")
        name = mic(3)
        
        speak("Speak the receiver email")
        receiver = mic(4).replace(" ", "") + "@gmail.com"
        
        speak("Speak the subject of the mail")
        subject = mic(3)
        
        speak("Speak the message you want to send")
        body = mic(3)
        
        try:
            send_mail(receiver, subject, body)
        except:
            speak("Sorry, you have given an invalid receiver email. Please repeat the receiver email again.")
            receiver = mic(5).replace(" ", "") + "@gmail.com"
            send_mail(receiver, subject, body)
        speak("Your email has been sent successfully to the receiver.")
    elif "schedule" in choice:
        speak("Whom do you want to send the email?")
        name = mic(3)
        
        speak("Speak the receiver email")
        receiver = mic(4).replace(" ", "") + "@gmail.com"
        
        speak("Speak the subject of the mail")
        subject = mic(3)
        
        speak("Speak the message you want to send")
        body = mic(3)
        
        send_time = get_time_from_user()
        
        if send_time:
            try:
                schedule_mail(receiver, subject, body, send_time)
            except:
                speak("There was an error scheduling your email. Please try again.")
        else:
            speak("Say it again Correctly")
            send_time = get_time_from_user()
    else:
        speak("Sorry, I didn't understand your choice. Please say 'read mail', 'compose mail', or 'schedule mail'.")
        main_code()
main_code()