import os
import re
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import pandas as pd
import speech_recognition as sr
import mysql.connector
import random
from translate import Translator
import tkinter.messagebox
import threading
import datetime
from passlib.hash import pbkdf2_sha256
from tkinter import StringVar
import nltk
from googletrans import Translator
import pandas as pd
import matplotlib.pyplot as plt

language_var = None
current_user_id = None


def generate_user_id():
    return random.randint(0, 100)

def new_user_window(root):
    new_user_root = tk.Toplevel(root)
    new_user_root.title("New User Registration")

    content_frame = ttk.Frame(new_user_root, padding="20")
    content_frame.pack()

    label_username = ttk.Label(content_frame, text="Username:", font=("Helvetica", 12,"bold"))
    label_username.grid(row=0, column=0, sticky="w")

    entry_username = ttk.Entry(content_frame, font=("Helvetica", 12))
    entry_username.grid(row=0, column=1)

    label_password = ttk.Label(content_frame, text="Password:", font=("Helvetica",12,"bold"))
    label_password.grid(row=1, column=0, sticky="w")

    entry_password = ttk.Entry(content_frame, show="*", font=("Helvetica", 12))
    entry_password.grid(row=1, column=1)

    button_register = ttk.Button(content_frame, text="Register",
                                 command=lambda: register(new_user_root, entry_username, entry_password))
    button_register.grid(row=2, column=0, columnspan=2, pady=(10,0))

    entry_username.focus_set()


def register(new_user_root, entry_username, entry_password):
    new_user_root.withdraw()
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        user_id = generate_user_id()
        hashed_password = pbkdf2_sha256.hash(password)

        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Aaryan22$",
            database="speech2text",
        )
        cursor = db.cursor()

        insert_query = "INSERT INTO users(id, username, password, creation_time) VALUES (%s, %s, %s, %s)"
        current_time = datetime.datetime.now()
        cursor.execute(insert_query, (user_id, username, hashed_password, current_time))
        db.commit()

        cursor.close()
        db.close()

        registration_message = f"Registration successful. Your user ID is: {user_id}"
        tkinter.messagebox.showinfo("Registration", registration_message)

        new_user_root.destroy()
    else:
        tkinter.messagebox.showwarning("Registration", "Username and password are required")


def existing_user_window(root):
    global language_var
    existing_user_root = tk.Toplevel(root)
    existing_user_root.title("Existing User Login")

    content_frame = ttk.Frame(existing_user_root, padding="20")
    content_frame.pack()

    label_user_id = ttk.Label(content_frame, text="User ID:",font=("Helvetica", 12,"bold"))
    label_user_id.grid(row=0, column=0, sticky="w")

    entry_user_id = ttk.Entry(content_frame)
    entry_user_id.grid(row=0, column=1)

    label_password = ttk.Label(content_frame, text="Password:", font=("Helvetica", 12,"bold"))
    label_password.grid(row=1, column=0, sticky="w")

    entry_password = ttk.Entry(content_frame, show="*")
    entry_password.grid(row=1, column=1)

    button_login = ttk.Button(content_frame, text="Login",
                              command=lambda: login(existing_user_root, entry_user_id, entry_password))
    button_login.grid(row=2, column=0, columnspan=2, pady=(10,0))

    entry_user_id.focus_set()

def speak_text(selected_language):
    global current_user_id

    if not current_user_id:
        tkinter.messagebox.showwarning("Conversion", "Please log in first.")
        return

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    def recognize_audio():
        with microphone as source:
            print("Listening...")
            audio = recognizer.listen(source)

            try:
                print("Translating...")
                text = recognizer.recognize_google(audio)

                db = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="Aaryan22$",
                    database="speech2text",
                )
                cursor = db.cursor()

                insert_query = "INSERT INTO transcriptions (user_id, text, language, speech_time) VALUES (%s, %s, %s, %s)"
                current_time = datetime.datetime.now()
                transcription_data=(current_user_id, text,selected_language, current_time)
                cursor.execute(insert_query, transcription_data)
                db.commit()

                cursor.close()
                db.close()

                # Initialize the translation client
                translator = Translator(service_urls=['translate.google.com'])

                # Retrieve the proper nouns from the original text
                proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', text)

                # Translate the rest of the sentence while keeping proper nouns unchanged
                translated_text = translator.translate(text, dest=selected_language).text

                # Replace the placeholders with the original proper nouns
                for noun in proper_nouns:
                    translated_text = translated_text.replace(f'[{noun}]', noun)

                command = 'PowerShell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'' + translated_text.replace(
                    "'", "''") + '\');"'
                os.system(command)

            except sr.UnknownValueError:
                print("Speech recognition could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service: {0}".format(e))

    threading.Thread(target=recognize_audio).start()
def login(existing_user_root, entry_user_id, entry_password):
    global current_user_id
    existing_user_root.withdraw()
    user_id = entry_user_id.get()
    password = entry_password.get()

    if user_id and password:
        if user_id.isdigit():
            user_id = int(user_id)

            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Aaryan22$",
                database="speech2text",
            )
            cursor = db.cursor()

            select_query = "SELECT id, password FROM users WHERE id = %s "
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchone()

            if result:
                stored_password = result[1]

                if pbkdf2_sha256.verify(password, stored_password):
                    current_user_id = result[0]
                    current_time = datetime.datetime.now()
                    print("Login successful! User ID:", current_user_id)
                    print("Login time:", current_time)

                    insert_query = "INSERT INTO user_login (user_id, login_time) VALUES (%s, %s)"
                    cursor.execute(insert_query, (current_user_id, current_time))
                    db.commit()

                    cursor.close()
                    db.close()

                    existing_user_root.destroy()
                    conversation_window()
                else:
                    print("Login failed. Invalid user ID or password.")
                    tkinter.messagebox.showinfo("Login failed", "Invalid user ID or password.")

            cursor.close()
            db.close()
        else:
            print("Login failed. Invalid user ID or password.")
            tkinter.messagebox.showwarning("Login Failed", "User ID must be a number.")
    else:
        print("Login failed. Invalid user ID or password.")
        tkinter.messagebox.showwarning("Login Failed", "User ID and password are required.")


def conversation_window():
    global language_var
    conversation_root = tk.Toplevel()
    conversation_root.title("Conversation")

    content_frame = ttk.Frame(conversation_root, padding="20",)
    content_frame.pack()

    label_language = ttk.Label(content_frame, text="Select Language:", font=("Helvetica",12,"bold"))
    label_language.grid(row=0, column=0, sticky="w")

    def on_language_change(*args):
        selected_language = language_var.get()
        print("Selected Language:", selected_language)

    language_var = StringVar()
    combobox_language= ttk.Combobox(content_frame, textvariable=language_var)
    combobox_language["values"] =("French", "German", "Spanish")
    combobox_language.current(0)
    combobox_language.grid(row=0,column=1)

    button_convert = ttk.Button(content_frame, text="Convert Speech to Text", style="AccentButton.TButton",
                                command=lambda: speak_text(language_var.get()))
    button_convert.grid(row=1, column=0, columnspan=2, pady=10)

    button_transcriptions = ttk.Button(content_frame, text="Generate Transcriptions Report", style="Accent.TButton", command=generate_transcriptions_report)
    button_transcriptions.grid(row=2, column=0, pady=(10,0))

    button_language_distribution = ttk.Button(content_frame, text="Generate Lang Distribution Report", style="Accent.TButton", command=generate_language_distribution_report)
    button_language_distribution.grid(row=2, column=1, pady=(10,0))
def generate_transcriptions_report():
    db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Aaryan22$",
    database="speech2text",
    )
    cursor = db.cursor()

    select_query = "SELECT user_id, COUNT(*) FROM transcriptions GROUP BY user_id"
    cursor.execute(select_query)
    result = cursor.fetchall()

    user_ids = []
    transcription_counts = []
    for row in result:
        user_id=row[0]
        transcription_count=row[1]

        if user_id is not None:
            user_ids.append(user_id)
            transcription_counts.append(transcription_count)
    data = {'User ID': user_ids, 'Transcription Count': transcription_counts}
    df = pd.DataFrame(data)

    plt.bar(df['User ID'], df['Transcription Count'])
    plt.xlabel('User ID')
    plt.ylabel('Transcription Count')
    plt.title('Number of Transcriptions by User')
    plt.show()

    cursor.close()
    db.close()

def generate_language_distribution_report():
    db=mysql.connector.connect(
        host="localhost",
        user="root",
        password="Aaryan22$",
        database="speech2text",
    )
    cursor=db.cursor()

    select_query="SELECT language, COUNT(*) FROM transcriptions GROUP BY language"
    cursor.execute(select_query)
    result=cursor.fetchall()

    languages=[]
    transcription_counts=[]
    for row in result:
        language=row[0]
        transcription_count=row[1]

        if language is not None:
            languages.append(language)
            transcription_counts.append(transcription_count)

    if languages and transcription_counts:

        data ={'Language': languages, 'Transcription Count': transcription_counts}
        df=pd.DataFrame(data)

        plt.bar(df['Language'],df['Transcription Count'])
        plt.xlabel('Language')
        plt.ylabel('Transcription Count')
        plt.title('Language Distrinbution')
        plt.xticks(rotation=45)
        plt.show()

    else:
        print("No data available")

# Create the main root window
root = tk.Tk()
root.title("Speech to Text")
root.geometry("400x250")


style=ttk.Style()
style.configure("AccentButton.TButton", background="#007bff", foreground="black", font=("Helvetica", 12, "bold"),padding=10)

content_frame = ttk.Frame(root, padding="20")
content_frame.pack()

label_title = ttk.Label(content_frame, text="Speech Transalator", foreground="black",font=("Helvetica",16,"bold"))
label_title.grid(row=0,column=0,columnspan=2, pady=20, sticky="n")

button_new_user = ttk.Button(content_frame, text="New User", command=lambda: new_user_window(root))
button_new_user.grid(row=1, column=0,columnspan=2, pady=10, sticky="n", rowspan=2)

button_existing_user = ttk.Button(content_frame, text="Existing User", command=lambda: existing_user_window(root))
button_existing_user.grid(row=3, column=0, columnspan=2, pady=10, sticky="n", rowspan=2)


root.mainloop()
