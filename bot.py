import telebot
import sqlite3
import logging
from credentials import get_credentials



logging.basicConfig(level=logging.INFO)

API_TOKEN, DATABASE_NAME = get_credentials()

# Setup the bot
bot = telebot.TeleBot(API_TOKEN)

# Database setup
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False) #added check_same_thread=False
cursor = conn.cursor()


def create_database():
    """Creates the SQLite database and table if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            chat_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

create_database()

commands = [
    telebot.types.BotCommand("start", "Start the bot"),
    telebot.types.BotCommand('tag', 'Tags everyone'),
    telebot.types.BotCommand('list_users', 'Lists existing users '),
]
bot.set_my_commands(commands)

@bot.message_handler(commands=['start'])
def start_command(message):
    """Sends a welcome message when the bot is started."""
    bot.send_message(message.chat.id, "Hoş geldiniz! Botu kullanmaya başlayabilirsiniz.")


@bot.message_handler(commands=['tag'])
def tag_users(message):
    """Tags all users in the database."""
    chat_id = message.chat.id
    
    
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, first_name FROM users WHERE chat_id = ?", (chat_id,))
    users = cursor.fetchall()
    

    if not users:
        bot.reply_to(message, "No users found in the database for this group.")
        return

    tag_string = ""
    for user_id, first_name in users:
        tag_string += f"[{first_name}](tg://user?id={user_id}) "

    if tag_string:
        bot.reply_to(message, tag_string, parse_mode="Markdown")


@bot.message_handler(commands=['list_users'])
def list_users(message):
    """Veritabanındaki kullanıcıları listeler."""
    chat_id = message.chat.id

    #conn = sqlite3.connect(DATABASE_NAME)
    #cursor = conn.cursor()

    # Query all users for the group (or just the users with that chat_id if you want to limit it)
    cursor.execute("SELECT username, first_name FROM users WHERE chat_id = ?", (chat_id,))
    users = cursor.fetchall()
   

    # If no users are found, send a message indicating so
    if not users:
        bot.reply_to(message, "Bu grup için veritabanında kullanıcı bulunamadı.")
        return

    # Format and send the list of users
    user_list = "\n".join([f"{first_name} (@{username})" for username, first_name in users if username])
    bot.send_message(message.chat.id, f"Grup kullanıcıları:\n{user_list}")


@bot.message_handler(func=lambda message: True)
def log_messages(message):
    print(f"Gruba gelen mesaj: {message.text} - Chat Type: {message.chat.type}")

    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Kullanıcıyı veritabanına ekle
    cursor.execute("INSERT OR IGNORE INTO users (chat_id, user_id, username, first_name) VALUES (?, ?, ?, ?)",
                   (chat_id, user_id, username, first_name))
    conn.commit()

bot.infinity_polling()