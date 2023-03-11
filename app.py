from flask import Flask, render_template, request,redirect, url_for,session
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from googlesearch import search

import os
from dotenv import load_dotenv
load_dotenv()
email_token = os.getenv('EMAIL_TOKEN')

# Create a new chatbot instance
chatbot = ChatBot('MyChatBot')
# Create a connection to the MySQL database
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="6984125oO",
  database="chatbot"
)
app = Flask(__name__)
app.secret_key = '5800d5d9e4405020d527f0587538abbe'  # Set a secret key for session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# Create a new chatbot
# chatbot = ChatBot('MyChatBot')

# Create a new trainpython er for the chatbot
conversation = [
    'Hello',
    'Hi there!',
    'How are you?',
    'I am doing well.',
    'That is good to hear.',
    'Thank you.',
    'You are welcome.',
    'Goodbye',
    'Goodbye!'
]

# Train the chatbot on the English corpus
trainer = ListTrainer(chatbot)
trainer.train(conversation)

@app.route("/")
def login():
    return render_template("info.html")
@app.route('/process_form', methods=['POST','GET'])
def process_form():
    name = request.form['username']
    email = request.form['email']
    print("FOrm entered")
    session['filled_form'] = True  # Set session variable indicating form filled out
    # Do something with the form data
    return redirect(url_for('chat', username=str(name), email= str(email)))


@app.route("/chat/<username>/<email>")
def chat(username,email):
    if session.get('filled_form'):
        context = {"username":username, "email":email}
        return render_template("chat.html",**context)
    else:
        return redirect(url_for('login'))

@app.route("/get/<username>/<email>")
def get_bot_response(username,email):
    user_text = request.args.get("msg")
    if user_text.startswith("/google"):
        result="Here are the links that we found related to the search query: \\n"
        search_text = user_text.replace("/google","")
        for j in search(search_text, tld="co.in", num=5, stop=5, pause=2):
            result=f'{result}'+j+"\\n"
        bot_response= f'{result}'
    else:
        bot_response = str(chatbot.get_response(user_text))

    mycursor = mydb.cursor()
    sql = "INSERT INTO chat_history (username,email,user_msg, bot_message) VALUES (%s,%s,%s, %s)"
    val = (username,email,user_text, bot_response)
    mycursor.execute(sql, val)
    mydb.commit()
    return bot_response

@app.route("/send_mail/<username>/<email>")
def send_mail(username,email):
    mycursor = mydb.cursor()
    # Collect all the conversations matching the email
    sql = "SELECT user_msg, bot_message FROM chat_history WHERE email = %s"
    val = (email,)
    mycursor.execute(sql, val)
    conversations = mycursor.fetchall()

    # Write the conversations to a text file
    filename = f"{email}_conversations.txt"
    with open(filename, "w") as f:
        for conversation in conversations:
            f.write(f"User: {conversation[0]}\n")
            f.write(f"Bot: {conversation[1]}\n")
            f.write("\n")

    # Send the file as an email attachment
    with open(filename, "r") as f:
        contents = f.read()

    msg = MIMEMultipart()
    msg['From'] = "noormd0021@gmail.com"
    msg['To'] = email
    msg['Subject'] = "Chatbot Conversation History"
    body = "Please find attached the conversation history with the chatbot."
    msg.attach(MIMEText(body, 'plain'))
    attachment = MIMEText(contents, 'plain')
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(attachment)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("noormd0021@gmail.com", email_token) # replace with actual email and password
    text = msg.as_string()
    server.sendmail("noormd0021@gmail.com", email, text)
    server.quit()
    return redirect(url_for('chat', username=str(username), email= str(email)))
if __name__ == "__main__":
    app.run()
