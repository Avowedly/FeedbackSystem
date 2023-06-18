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


def base_page(message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	button1 = types.KeyboardButton('Семестровый опрос')
	button2 = types.KeyboardButton('Обратная связь')
	markup.row(button1)
	markup.row(button2)
	bot.send_message(message.chat.id, "Что-нибудь еще?", reply_markup=markup)
	print(message.from_user.id)
	bot.register_next_step_handler(message, start)


def start(message):
	def ask(message):
		global requirement
		question = bot.send_message(message.chat.id, quest['text'])
		requirement = quest["requirements"]
		bot.register_next_step_handler(question, read_answer)

	def read_answer(answer):
		nonlocal quest
		try:
			if is_correct(answer, requirement):
				print(f"{quest['text']} correct answer text -> {answer.text} from {answer.from_user.first_name}")
				quest = next(questions)
				ask(answer)
			else:
				print(f"{quest['text']} incorrect answer text -> {answer.text} from {answer.from_user.first_name}")
				wrong_input(answer, requirement)
				ask(answer)
		except StopIteration:
			bot.send_message(message.chat.id, "Спасибо за ответы!")
			bot.register_next_step_handler(message, base_page)


	if message.text == 'Семестровый опрос':
		questions = (i for i in data.values())
		quest = next(questions)
		ask(message)

	if message.text == 'Обратная связь':
		pass


def is_correct(message, requirement):

	if message.content_type == 'text':
		text = message.text
		if requirement == 'scale':
			if text.isdigit():
				x = int(text)
				if (x >= 0) and (x <= 10):
					return True
				else:
					return False
			return False

		if requirement == 'string':
			return True
	else:
		return False



def wrong_input(message, requirement):
	if message.content_type == 'text':
		if requirement == 'scale':
			bot.send_message(message.chat.id, 'Введите целое число от 0 до 10')
		if requirement == 'string':
			bot.send_message(message.chat.id, 'Используйте буквы и числа!')
	else:
		bot.send_message(message.chat.id, 'Используйте буквы и числа!')

@bot.message_handler(commands=['help'])
def help(message):
	pass

@bot.message_handler(content_types=['text'])
def info(message):
	bot.send_message(message.chat.id, f"Напиши /start, чтобы начать")


bot.infinity_polling()