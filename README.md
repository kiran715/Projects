# Voice Driven Email Assistant and Schedular for visually impaired persons
## Project Overview
This project is a voice-controlled email assistant designed to help visually impaired users or anyone who prefers hands-free email management. It allows users to read, compose, and schedule emails using natural language voice commands, and also includes a spam detection feature to ensure email security. By integrating speech recognition, text-to-speech, and scheduling functionalities, the project aims to simplify email management and make it more accessible.

## Key features
+ **Voice-to-Text Conversion**: Captures and processes user speech inputs using the SpeechRecognition library.

+ **Email Management** :
  + **Read Emails** : Fetches and reads aloud the most recent emails.
  + **Compose Emails** : Allows users to compose and send emails entirely through voice commands.
  + **Email Scheduling** : Lets users schedule emails to be sent at a specific time using natural language input.

+ **Text-to-Speech**: Provides audio feedback, reading out emails, prompts, and confirmation messages using pyttsx3.

## Tech Stack
+ Python
+ SpeechRecognition
+ pyttsx3
+ smtplib
+ imaplib
+ sched
+ email.message


## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
