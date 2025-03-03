import email
import imaplib
import smtplib
import speech_recognition as sr
import pyttsx3
from email.message import EmailMessage
import sched
import time
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup  
import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Initialize scheduler for email scheduling
scheduler = sched.scheduler(time.time, time.sleep)

# Initialize speech recognition and text-to-speech engine
listener = sr.Recognizer()
tts = pyttsx3.init()

# Configure voice properties
tts.setProperty('rate', 140)
tts.setProperty('volume', 1)
voices = tts.getProperty('voices')
tts.setProperty('voice', voices[1].id)

# Email credentials (Replace with your email and app password)
SENDER_EMAIL = "toby26336@gmail.com"
APP_PASSWORD = "rrobinwbwvktyrdb"  # Use an App Password for security

def speak(text):
    """Converts text to speech."""
    tts.say(text)
    tts.runAndWait()

def mic(duration=5):
    """Captures speech input and converts it to text."""
    with sr.Microphone() as source:
        speak("Your assistant is listening...")
        listener.adjust_for_ambient_noise(source, duration=1)
        voice = listener.listen(source, phrase_time_limit=duration)
    try:
        data = listener.recognize_google(voice).lower()
        print(f"Recognized: {data}")
        speak(f'You have said {data} ')
        return data
    except:
        speak("Sorry, I didn't catch that. Please try again.")
        return mic(duration)  # Retry
    
def get_email_count():
    """Capture the number of emails to read using voice input."""
    speak("How many recent emails do you want to read?")
    spoken_text = mic(3)  # Capture speech input
    
    # First try to extract numeric digits
    digits = re.findall(r'\d+', spoken_text)
    if digits:
        return int(digits[0])  # Convert the first detected number to an integer
    
    # If no digits found, try to convert word numbers to integers
    word_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50
    }
    
    # Clean up the spoken text and split into words
    cleaned_text = spoken_text.lower().replace('-', ' ').replace(' and ', ' ')
    words = cleaned_text.split()
    
    # Check for direct number words
    for word in words:
        if word in word_to_num:
            return word_to_num[word]
    
    # Check for compound number words (like twenty one)
    for i in range(len(words) - 1):
        if words[i] in word_to_num and words[i+1] in word_to_num:
            tens = words[i]
            ones = words[i+1]
            # Check if tens is actually a tens value
            if tens in ['twenty', 'thirty', 'forty', 'fifty']:
                return word_to_num[tens] + word_to_num[ones]
    
    # If no number was found
    speak("I couldn't detect a number. Let's try once more. Please say a number between 1 and 50.")
    spoken_text = mic(3)
    
    # Try one more time with the same approach
    digits = re.findall(r'\d+', spoken_text)
    if digits:
        return int(digits[0])
    
    # If still no success, default to a reasonable number
    for word in spoken_text.lower().split():
        if word in word_to_num:
            return word_to_num[word]
    
    speak("I still couldn't detect a number. I'll read 2 emails by default.")
    return 2  # Default value if we can't detect a number after two attempts

def get_email_from_user():
    """Captures email address and converts spoken format to correct format."""
    speak("Please say the full email address, using 'at' instead of '@' and 'dot' instead of '.'")

    while True:
        raw_email = mic(8)  # Allow enough time for longer emails

        # Convert spoken words to proper email format
        email_address = (
            raw_email.replace(" at ", "@")  # Replace "at" with "@"
            .replace(" dot ", ".")  # Replace "dot" with "."
            .replace(" ", "")  # Remove unintended spaces
        )

        speak(f"Did you mean {email_address}? Say yes or no.")
        confirmation = mic(3)

        if "yes" in confirmation:
            return email_address
        else:
            speak("Let's try again. Please say the email address clearly.")


def preprocess_text(text):
    """Clean and normalize text for ML model."""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r'[^\w\s]', '', text)
    return text

def train_spam_model():
    """Train a ML model to detect spam emails and save it."""
    # Sample training data (in a real scenario, load from a proper dataset)
    data = {
        'sender': [
            'service@paypal.com', 'noreply@amazon.com', 'friend@gmail.com', 
            'win@lottery.xyz', 'verify@bank-secure.info', 'newsletter@company.com',
            'support@microsoft.com', 'relative@hotmail.com', 'prize@winner.xyz',
            'security@bank.com', 'friend@yahoo.com', 'newsletter@deals.com',
            'admin@netflix.com', 'service@yourbank.com', 'alerts@linkedin.com'
        ],
        'subject': [
            'Your receipt from PayPal', 'Your Amazon order', 'Coffee tomorrow?',
            'URGENT: YOU WON $1,000,000!!!', 'Verify your bank account immediately!', 'Weekly newsletter',
            'Your Microsoft subscription', 'Family photos', 'Claim your FREE prize now!!',
            'Security alert', 'Dinner plans', 'SPECIAL DEALS INSIDE!!!!',
            'New sign-in detected', 'Important account notice', 'Connection request'
        ],
        'body': [
            'Here is your transaction receipt for your recent purchase.',
            'Your order #12345 has shipped and will arrive on Friday.',
            'Do you want to meet for coffee tomorrow afternoon?',
            'You have been selected as our lucky winner! Send your bank details to claim your prize now!',
            'Your account has been compromised. Click here to verify your password and bank details immediately!',
            'Here are this week\'s top stories and updates from our company.',
            'Your subscription will renew on 01/15. No action needed.',
            'Attached are the photos from our family reunion last weekend.',
            'Congratulations! You\'ve been selected to receive a free iPhone! Click here to claim now before time runs out!',
            'We detected a login from a new device. If this wasn\'t you, reset your password.',
            'How about dinner at the new Italian place on Friday?',
            'FLASH SALE!!! Everything 90% OFF! Limited time offer! BUY NOW!!! Credit card required!!!',
            'A new device signed into your account. If this was you, no action is needed.',
            'Please review your recent account statement for important information.',
            'John Smith has requested to connect with you on LinkedIn.'
        ],
        'is_spam': [
            0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Feature preparation - combine sender, subject, body for more signal
    df['content'] = df['sender'] + ' ' + df['subject'] + ' ' + df['body']
    df['content'] = df['content'].apply(preprocess_text)
    
    # Split into features and target
    X = df['content']
    y = df['is_spam']
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train the TF-IDF vectorizer
    vectorizer = TfidfVectorizer(max_features=5000)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    # Train the classifier
    classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    classifier.fit(X_train_tfidf, y_train)
    
    # Evaluate
    y_pred = classifier.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")
    print(classification_report(y_test, y_pred))
    
    # Save the trained model and vectorizer
    model_data = {
        'vectorizer': vectorizer,
        'classifier': classifier
    }
    
    with open('spam_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    
    return model_data

def spam_predict(email_from, email_subject, email_body, model_data=None):
    """
    Predict if an email is spam using the trained ML model.
    Returns a tuple (is_spam, confidence, reason)
    """
    # Load the model if not provided
    if model_data is None:
        try:
            with open('spam_model.pkl', 'rb') as f:
                model_data = pickle.load(f)
        except FileNotFoundError:
            # Train a new model if not found
            model_data = train_spam_model()
    
    # Extract the vectorizer and classifier
    vectorizer = model_data['vectorizer']
    classifier = model_data['classifier']
    
    # Preprocess and combine email content
    combined_content = preprocess_text(f"{email_from} {email_subject} {email_body}")
    
    # Transform the content
    content_tfidf = vectorizer.transform([combined_content])
    
    # Get the prediction and probability
    is_spam = classifier.predict(content_tfidf)[0]
    probabilities = classifier.predict_proba(content_tfidf)[0]
    
    # Get confidence score
    spam_confidence = probabilities[1] if is_spam else 1 - probabilities[0]
    
    # Generate reasons based on feature importance
    feature_names = vectorizer.get_feature_names_out()
    
    # Get top features that contribute to the decision
    if len(feature_names) > 0:
        content_tfidf_array = content_tfidf.toarray()[0]
        
        # Get indices of non-zero elements
        non_zero_indices = content_tfidf_array.nonzero()[0]
        
        # Get feature importance for these indices
        importances = []
        for idx in non_zero_indices:
            # For simplicity, use the TF-IDF value as importance
            if idx < len(feature_names):
                importances.append((feature_names[idx], content_tfidf_array[idx]))
        
        # Sort by importance
        importances.sort(key=lambda x: x[1], reverse=True)
        
        # Generate reason based on top features
        top_features = [f'"{word}"' for word, _ in importances[:3]]
        
        if is_spam:
            reason = f"Detected spam indicators: {', '.join(top_features)}"
        else:
            reason = "Not classified as spam"
    else:
        reason = "Insufficient features to determine specific reason"
    
    return (bool(is_spam), spam_confidence, reason)
def send_mail(receiver, subject, body):
    """Sends an email using SMTP."""
    try:
        # Check for spam before sending
        spam_status, confidence, reason = spam_predict(SENDER_EMAIL, subject, body)
        if spam_status:
            speak(f"Warning: This message may appear as spam to the recipient. Confidence: {confidence:.0%}.")
            speak(f"Reason: {reason}")
            speak("Do you still want to send this email? Say yes or no.")
            confirmation = mic(3)
            if "no" in confirmation:
                speak("Email sending cancelled.")
                return False

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, APP_PASSWORD)

        email = EmailMessage()
        email["From"] = SENDER_EMAIL
        email["To"] = receiver
        email["Subject"] = subject
        email.set_content(body)

        server.send_message(email)
        server.quit()

        speak("Your email has been sent successfully.")
        return True
    except Exception as e:
        speak("An error occurred while sending the email.")
        print("Error:", e)
        return False

def schedule_mail(receiver, subject, body, send_time):
    """Schedules an email to be sent at a later time."""
    # Check for spam before scheduling
    spam_status, confidence, reason = spam_predict(SENDER_EMAIL, subject, body)
    if spam_status:
        speak(f"Warning: This message may appear as spam to the recipient. Confidence: {confidence:.0%}.")
        speak(f"Reason: {reason}")
        speak("Do you still want to schedule this email? Say yes or no.")
        confirmation = mic(3)
        if "no" in confirmation:
            speak("Email scheduling cancelled.")
            return

    def send_scheduled_mail():
        send_mail(receiver, subject, body)
        speak("Your scheduled email has been sent successfully.")

    scheduler.enterabs(send_time, 1, send_scheduled_mail)
    speak("Your email has been scheduled successfully.")
    scheduler.run()

def read_mail(num_emails):
    """Reads the most recent email from the inbox with improved body extraction."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(SENDER_EMAIL, APP_PASSWORD)
        mail.select("inbox")
        result, data = mail.search(None, '(X-GM-RAW "category:primary")')

        mail_ids = data[0].split()
        if not mail_ids:
            speak("Your inbox is empty.")
            return

        num_emails = min(num_emails, len(mail_ids))  # Ensure we don't exceed available emails
        latest_emails = mail_ids[-num_emails:]  # Get the latest 'num_emails' email IDs

        for email_id in reversed(latest_emails):  # Read in reverse order (newest first)
            result, data = mail.fetch(email_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            email_from = msg.get("From", "Unknown Sender")
            email_subject = msg.get("Subject", "No Subject")
            email_body = ""

            # Better content extraction
            if msg.is_multipart():
                # First try to find a plain text part
                plain_text_part = None
                html_part = None
                
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    # Prefer plain text
                    if content_type == "text/plain":
                        plain_text_part = part
                        break
                    elif content_type == "text/html":
                        html_part = part
                
                # Use plain text if available, otherwise use HTML
                if plain_text_part:
                    email_body = plain_text_part.get_payload(decode=True).decode(errors="ignore")
                elif html_part:
                    html_content = html_part.get_payload(decode=True).decode(errors="ignore")
                    # Better HTML cleaning
                    soup = BeautifulSoup(html_content, "html.parser")
                    
                    # Remove style and script elements
                    for element in soup(["style", "script", "head", "title", "meta", "[document]"]):
                        element.extract()
                    
                    # Get text content
                    email_body = soup.get_text(separator=' ', strip=True)
            else:
                # If the email isn't multipart, get the payload directly
                content_type = msg.get_content_type()
                if content_type == "text/html":
                    html_content = msg.get_payload(decode=True).decode(errors="ignore")
                    soup = BeautifulSoup(html_content, "html.parser")
                    
                    # Remove style and script elements
                    for element in soup(["style", "script", "head", "title", "meta", "[document]"]):
                        element.extract()
                    
                    # Get text content
                    email_body = soup.get_text(separator=' ', strip=True)
                else:
                    email_body = msg.get_payload(decode=True).decode(errors="ignore")
            
            # Clean up the body text further
            # Remove URLs
            email_body = re.sub(r'http\S+', '', email_body)
            # Replace multiple whitespace characters with a single space
            email_body = re.sub(r'\s+', ' ', email_body).strip()
            # Remove common email signature indicators
            email_body = re.sub(r'--+\s*[\r\n]+.*', '', email_body)
            # Remove CSS property patterns
            email_body = re.sub(r'[a-z-]+:[^;]+;', '', email_body)
            # Remove any remaining HTML tags
            email_body = re.sub(r'<[^>]+>', '', email_body)
            # Fix common HTML escape character issues
            email_body = email_body.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            
            # Normalize multiple consecutive spaces
            email_body = re.sub(r'\s{2,}', ' ', email_body).strip()
            
            # Truncate extremely long messages for speech
            max_chars_to_speak = 500  # Adjust this value as needed
            speaking_text = email_body[:max_chars_to_speak]
            if len(email_body) > max_chars_to_speak:
                speaking_text += "... Message truncated for readability."

            # Check if the email is spam using the ML model
            spam_status, confidence, reason = spam_predict(email_from, email_subject, email_body)
            
            # Add spam indicator to the speech output
            if spam_status:
                speak(f"Warning: This email appears to be spam. Confidence: {confidence:.0%}.")
                speak(f"Reason: {reason}")
                speak("Do you want to hear this email anyway? Say yes or no.")
                user_response = mic(3)
                if "no" in user_response:
                    speak("Moving to the next email.")
                    mail.store(email_id, '+X-GM-LABELS', '\\Spam')  # Mark as Spam
                    speak("Email has been marked as spam.")
                    continue

            # Speak and print email details
            speak(f"Email from {email_from}")
            speak(f"Subject: {email_subject}")
            speak("Here is the message.")
            speak(speaking_text)  # Now with better text cleaning and length limiting

            print(f"\nEmail from: {email_from}")
            print(f"Subject: {email_subject}")
            print(f"Body: {speaking_text}\n")
            print("-" * 50)

            speak("What would you like to do with this email? Say 'important', 'spam', or 'next'.")
            user_response = mic(3)
            
            if "important" in user_response:
                mail.store(email_id, '+X-GM-LABELS', '\\Important')  # Mark as Important
                speak("Email has been added to Important.")
            elif "spam" in user_response:
                mail.store(email_id, '+X-GM-LABELS', '\\Spam')  # Mark as Spam
                speak("Email has been marked as spam.")
                
                # Use this feedback to improve the model
                if not spam_status:
                    # Save this false negative for potential retraining
                    try:
                        with open('spam_training_data.txt', 'a') as f:
                            f.write(f"SPAM\t{email_from}\t{email_subject}\t{email_body[:200]}\n")
                    except:
                        pass
            else:
                speak("Continuing to the next email.")
                
                # If model predicted spam but user didn't mark it as spam
                if spam_status:
                    # Save this false positive for potential retraining
                    try:
                        with open('spam_training_data.txt', 'a') as f:
                            f.write(f"HAM\t{email_from}\t{email_subject}\t{email_body[:200]}\n")
                    except:
                        pass

    except Exception as e:
        speak("An error occurred while reading emails.")
        print("Error:", e)

def get_time_from_user():
    """Captures and processes the time for scheduling an email."""
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
    """Parses time input and converts to timestamp."""
    try:
        return datetime.strptime(input_time, '%Y-%m-%d %H:%M:%S').timestamp()
    except ValueError:
        speak("Sorry, the time format is incorrect. Please provide the time in the format YYYY-MM-DD HH:MM:SS.")
        return None

def main_code():
    """Main voice assistant function."""
    speak("Hi, this is your email voice assistant.")
    speak("Do you want to read mail, compose mail, or schedule mail?")
    
    choice = mic(3)

    if "read" in choice:
        speak("How many recent emails do you want to read?")
        num_emails = get_email_count()  # Now properly capturing the number
        speak(f"Reading {num_emails} recent emails from your inbox")
        read_mail(num_emails)
    elif "compose" in choice:
        speak("Please provide the receiver's email.")
        receiver = get_email_from_user()

        speak("Speak the subject of the mail.")
        subject = mic(3)

        speak("Speak the message you want to send.")
        body = mic(5)  # Extended time for longer messages

        send_mail(receiver, subject, body)
    elif "schedule" in choice:
        speak("Please provide the receiver's email.")
        receiver = get_email_from_user()

        speak("Speak the subject of the mail.")
        subject = mic(3)

        speak("Speak the message you want to send.")
        body = mic(5)  # Extended time for longer messages

        send_time = get_time_from_user()
        
        if send_time:
            schedule_mail(receiver, subject, body, send_time)
        else:
            speak("Say it again correctly.")
            send_time = get_time_from_user()
    else:
        speak("Invalid choice. Please try again.")
        main_code()

# Start the program
main_code()
