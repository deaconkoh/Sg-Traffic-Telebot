import traffic_info
import telebot
import os
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time

load_dotenv()
LTA_headers = {'AccountKey': os.getenv("LTA_KEY")}
TELE_KEY = os.getenv("TELE_KEY")
filtered_info = traffic_info.get_traffic_info(LTA_headers)
filtered_time = traffic_info.get_travel_time(LTA_headers)

bot = telebot.TeleBot(TELE_KEY)
options = {
    "Traffic Info": ["AYE", "CTE", "TPE", "BKE", "PIE", "SLE", "ECP", "Others"],
    "Est Time": ["AYE", "CTE", "TPE", "BKE", "PIE", "SLE", "ECP"]
}

# Current selected category
user_state = {}
def show_Back_menu(chat_id):
    """Display the main menu with categories."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("Traffic Info"), KeyboardButton("Est Time"))
    bot.send_message(chat_id, "Choose a category:", reply_markup=keyboard)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    """Send the main menu when the user sends /start."""
    show_Back_menu(message.chat.id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global user_state

    # If the user clicks "Back", bring them back to the main menu
    if message.text == "Back":
        show_Back_menu(message.chat.id)
        user_state.pop(message.chat.id, None)  # Clear the user's current state
        return

    # Handle main menu selection
    if message.text in options.keys():
        user_state[message.chat.id] = message.text  # Track user state

        # Create a keyboard for the selected category with a "Back" button
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons = [KeyboardButton(option) for option in options[message.text]]
        buttons.append(KeyboardButton("Back"))  # Add Back button
        keyboard.add(*buttons)

        bot.send_message(message.chat.id, f"Choose an option for {message.text}:", reply_markup=keyboard)

    # Handle sub-option selection
    elif message.chat.id in user_state and message.text in options[user_state[message.chat.id]]:
        category = user_state[message.chat.id]
        if category == "Traffic Info":
            bot.send_message(message.chat.id, f"Fetching traffic information for {message.text}...")
            try:
                # Load and save the map
                map_file = traffic_info.load_map(filtered_info, message.text.upper())  # Load the map
                image_file = traffic_info.save_map_as_image(map_file=f"{message.text.upper()}_expressway_map.html")  # Save as image

                # Send the image to the user
                with open(image_file, "rb") as photo:
                    bot.send_photo(message.chat.id, photo, caption=f"Traffic map for {message.text.upper()}")
                
                table_text = traffic_info.traffic_info_as_text(filtered_info, message.text.upper())
                bot.send_message(message.chat.id, table_text)
                
            except Exception as e:
                # Handle errors and inform the user
                bot.send_message(message.chat.id, f"An error occurred while fetching data: {str(e)}")
                
        elif category == "Est Time":
            bot.send_message(message.chat.id, f"Fetching estimated time for {message.text}...")
            est_time_text = traffic_info.travel_time_as_text(filtered_time, message.text.upper())
            bot.send_message(message.chat.id, est_time_text)

    # Handle invalid inputs
    else:
        bot.send_message(message.chat.id, "Invalid option. Please select a valid category using /start or click 'Back'.")

# Start polling
bot.infinity_polling()