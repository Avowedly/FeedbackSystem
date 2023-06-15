import telebot
from telebot import types

with open("token.txt", 'r') as file:
    token = file.readline()

bot = telebot.TeleBot(token)
bot.delete_webhook()

@bot.message_handler(commands=['start'])
def send_welcome(message):
	markup = types.ReplyKeyboardMarkup()
	button1 = types.KeyboardButton('Полезные ссылки')
	button2 = types.KeyboardButton('Семестровый опрос')
	button3 = types.KeyboardButton('Обратная связь')
	markup.row(button1)
	markup.row(button2, button3)
	bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Чем могу помочь?", reply_markup=markup)
	print(message.from_user.id)
	bot.register_next_step_handler(message, start)


def start(message):
	if message.text == 'Полезные ссылки':
		pass
		markup = types.InlineKeyboardMarkup()
		button1 = types.InlineKeyboardButton('Канал БМТ 🧬', url="https://t.me/biomedt")
		button2 = types.InlineKeyboardButton('Электронный университет', url="https://lks.bmstu.ru")
		markup.row(button1)
		markup.row(button2)
		bot.send_message(message.chat.id, f"Куда хочешь перейти?", reply_markup=markup)

	elif message.text == 'Семестровый опрос': # Начало семестрового опросника
		bot.send_message(message.chat.id, "Cеместровый опрос:")
		bot.register_next_step_handler(message, semester_form)

	elif message.text == 'Обратная связь': # Начало обращения
		bot.send_message(message.chat.id, "Жду твою обратную связь:")
		bot.register_next_step_handler(message, feedback)


def semester_form():
	pass

def feedback():
	pass


@bot.message_handler(commands=['help'])
def help(message):
	pass

@bot.message_handler(content_types=['text'])
def info(message):
	if message.text.lower().startswith('привет'):
		bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}")


bot.infinity_polling()