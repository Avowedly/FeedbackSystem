import telebot
from telebot import types
import json
import sqlite3


with open("token.txt", 'r') as file:
    token = file.readline()

with open("form.json", 'r', encoding="UTF-8") as file:
    data = json.load(file)

bot = telebot.TeleBot(token)
bot.delete_webhook()


@bot.message_handler(commands=['start'])
def send_welcome(message):
	"""
	Приветственный экран
	"""
	conn = sqlite3.connect('student_base.sql')
	cursor = conn.cursor()
	cursor.execute('CREATE TABLE IF NOT EXISTS users (id int primary key, group_name varchar(10))')
	conn.commit()
	cursor.close()
	conn.close()

	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	button1 = types.KeyboardButton('Семестровый опрос')
	button2 = types.KeyboardButton('Обратная связь')
	markup.row(button1)
	markup.row(button2)
	bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Чем могу помочь?", reply_markup=markup)
	print(message.from_user.id)
	bot.register_next_step_handler(message, start)


def base_page(message):
	"""
	Экран после прохождения опроса/отправки обращения
	"""
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	button1 = types.KeyboardButton('Семестровый опрос')
	button2 = types.KeyboardButton('Обратная связь')
	markup.row(button1)
	markup.row(button2)
	bot.send_message(message.chat.id, "Что-нибудь еще?", reply_markup=markup)
	print(message.from_user.id)
	bot.register_next_step_handler(message, start)

def start(message):
	"""
	Обработка выбранной на стартовом экране опции
	Семестровый опрос - пользователь отвечает на последовательность вопросов
	Обратная связь - пользователь пишет обращение в свободной форме
	"""

# _______________________________СЕМЕСТРОВЫЕ ФОРМЫ_____________________________________
	def semester_form(message):
		"""
		Последовательный вывод вопросов из вопросника и прием ответов
		"""

		requirement = ''
		def ask(message):
			"""
			Функция для вывода вопроса в чат
			Дополнительно использует requirement для проверки формата ответа пользователя далее
			"""
			question = bot.send_message(message.chat.id, quest['text'])
			nonlocal requirement
			requirement = quest["requirements"]
			bot.register_next_step_handler(question, read_answer)

		def read_answer(answer):
			"""
			Функция для чтения ответа пользователя
			Проверяет корректность ввода в зависимости от требований в переменной requirement
			Если ответ корректен по форме, то переходит к следующему вопросу,
			если нет - задает вопрос, пока не будет получен корректный ответ
			"""
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

		questions = (i for i in data.values())
		quest = next(questions)
		ask(message)

# _____________________________________FEEDBACK_____________________________________

	def read_feedback(message):
		"""
		Функция для чтения обращение пользователя
		Принимает только текст
		"""
		if message.content_type == 'text':
			print(message.text)
			bot.send_message(message.chat.id, "Спасибо за обратную связь!")
			bot.register_next_step_handler(message, base_page)
		else:
			bot.send_message(message.chat.id, "Словами, пожалуйста")
			bot.send_message(message.chat.id, "Ваши замечания/предложения:")
			bot.register_next_step_handler(message, read_feedback)

# ______________________Обработка нажатий на стартовом экране___________________________

	if message.text == 'Семестровый опрос':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		button1 = types.KeyboardButton('Физра')
		button2 = types.KeyboardButton('Матан')
		markup.row(button1)
		markup.row(button2)
		bot.send_message(message.chat.id, "Выбери предмет!", reply_markup=markup)
		bot.register_next_step_handler(message, semester_form)


	if message.text == 'Обратная связь':
		bot.send_message(message.chat.id, "Ваши замечания/предложения:")
		bot.register_next_step_handler(message, read_feedback)

# _____________________________________ПРОВЕРКИ___________________________________________
	def is_correct(message, requirement):
		"""
		Функция для проверки корректности ответа пользователя
		Проверяет, что ответ представляет собой строку,
		затем проверяет формат ответа, солгалсно переменной requirement
		"""
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
		"""
		Функция для сообщению пользователю о некорректности ввода
		дополнительно выводит пояснения, в каком формате необходим ответ
		"""
		if message.content_type == 'text':
			if requirement == 'scale':
				bot.send_message(message.chat.id, 'Введите целое число от 0 до 10')
			if requirement == 'string':
				bot.send_message(message.chat.id, 'Используйте буквы и числа!')
		else:
			bot.send_message(message.chat.id, 'Используйте буквы и числа!')


# _____________________________________ПРОЧИЕ КОМАНДЫ___________________________________________

@bot.message_handler(commands=['help'])
def help(message):
	pass

@bot.message_handler(content_types=['text'])
def info(message):
	bot.send_message(message.chat.id, f"Напиши /start, чтобы начать")


bot.infinity_polling()