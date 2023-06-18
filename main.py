import telebot
from telebot import types
import json


with open("token.txt", 'r') as file:
    token = file.readline()

with open("form.json", 'r', encoding="UTF-8") as file:
    data = json.load(file)

bot = telebot.TeleBot(token)
bot.delete_webhook()


@bot.message_handler(commands=['start'])
def send_welcome(message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	button1 = types.KeyboardButton('Семестровый опрос')
	button2 = types.KeyboardButton('Обратная связь')
	markup.row(button1)
	markup.row(button2)
	bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Чем могу помочь?", reply_markup=markup)
	print(message.from_user.id)
	bot.register_next_step_handler(message, start)


def start(message):
	def ask(message):
		try:
			quest = next(questions)
			question = bot.send_message(message.chat.id, quest['text'])
			bot.register_next_step_handler(question, read_answer)

		except StopIteration:
			bot.send_message(message.chat.id, "Спасибо за ответы!")
			bot.register_next_step_handler(message, send_welcome)

	def read_answer(answer):
		print("answer ->", answer.text)
		ask(answer)

	if message.text == 'Семестровый опрос':
		questions = (i for i in data.values())
		ask(message)

	if message.text == 'Обратная связь':
		pass






@bot.message_handler(commands=['help'])
def help(message):
	pass

@bot.message_handler(content_types=['text'])
def info(message):
	bot.send_message(message.chat.id, f"Напиши /start, чтобы начать")


bot.infinity_polling()