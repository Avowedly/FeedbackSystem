import telebot
from telebot import types
import json
import sqlite3
import re
import datetime

with open("token.txt", 'r') as file:
	token = file.readline()

with open("form.json", 'r', encoding="UTF-8") as file:
	form_data = json.load(file)

with open("disciplines.json", 'r', encoding="UTF-8") as file:
	disciplines_data = json.load(file)

bot = telebot.TeleBot(token)
bot.delete_webhook()


# ___________________________________БАЗА ДАННЫХ_________________________________________
def create_database(name):
	"""
	Создает базу данных, если она еще не была создана
	Поля: id, группа
	"""
	conn = sqlite3.connect(f'{name}.sql')
	cursor = conn.cursor()
	cursor.execute('CREATE TABLE IF NOT EXISTS users (id int primary key, group_name varchar(10))')
	cursor.execute('CREATE TABLE IF NOT EXISTS forms (id int, datetime varchar(25) primary key, discipline varchar(25), \
												  lection int, lector int, seminar int, seminarist int, comments varchar(500))')
	conn.commit()
	cursor.close()
	conn.close()


def get_ids_from_database(name):
	"""
	Получение id всех пользователей
	"""
	conn = sqlite3.connect(f'{name}.sql')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM users")
	user_ids = dict(cursor.fetchall()).keys()
	cursor.close()
	conn.close()
	return user_ids


def get_group_by_id(name, tg_id):
	"""
	Получение группы по id пользователя
	"""
	conn = sqlite3.connect(f'{name}.sql')
	cursor = conn.cursor()
	cursor.execute("SELECT group_name FROM users WHERE id = '%s'" % tg_id)
	group = cursor.fetchone()[0]
	cursor.close()
	conn.close()
	return group


def insert_field(name, type, args):
	"""
	Добавление нового поля в таблицу
	"""
	conn = sqlite3.connect(f'{name}.sql')
	cursor = conn.cursor()
	if type == 'users':
		tg_id, group = args
		cursor.execute("INSERT INTO users (id, group_name) VALUES('%s', '%s')" % (tg_id, group))
	if type == 'forms':
		tg_id, datetime, discipline, lector, lection, seminar, seminarist, comments = args
		cursor.execute("INSERT INTO forms (id, datetime, discipline, lector, lection, seminar, seminarist, comments) \
		 								VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
					   					(tg_id, datetime, discipline, lector, lection, seminar, seminarist, comments))
	conn.commit()
	cursor.close()
	conn.close()


def update_group(name, tg_id, group):
	"""
	Обновление группы пользователя
	"""
	conn = sqlite3.connect(f'{name}.sql')
	cursor = conn.cursor()
	cursor.execute("UPDATE users SET group_name = '%s' WHERE id = '%s'" % (group, tg_id))
	conn.commit()
	cursor.close()
	conn.close()


def show_database(name, type):
	"""
	Отображение таблицы
	"""
	conn = sqlite3.connect(f'{name}.sql')
	cursor = conn.cursor()
	if type == 'users':
		cursor.execute("SELECT * FROM users")
		users_data = dict(cursor.fetchall())
		for ids, group in users_data.items():
			print(f'User {ids} group -> {group}')
	if type == 'forms':
		cursor.execute("SELECT * FROM forms")
		forms_data = cursor.fetchall()
		print(forms_data)
		for ids, date, discipline, *values in forms_data:
			print(f'User {ids} date {date} discipline {discipline} -> answers: {values}')

	cursor.close()
	conn.close()

def is_group_correct(group):
	"""
	Проверка корректности ввода группы
	"""
	s = group.strip().upper()
	res = re.match(r'БМТ[1-5]-[1-8][1-3][Б, М]$', s)
	if res is None:
		return False
	else:
		return True


registration_counter = 0
def user_registration(message):
	"""
	Регистрация пользователя по группе и id в телеграме
	"""
	global registration_counter
	group = message.text.strip().upper()
	if is_group_correct(group):
		registration_counter = 0
		insert_field(name='semester_forms', type='users', args=(message.from_user.id, group))
		bot.send_message(message.chat.id, f"Приятно познакомиться! \nТеперь я смогу персонализировать твои анкеты!")
	else:
		registration_counter += 1
		if registration_counter>=3:
			bot.send_message(message.chat.id, f"Издеваешься? :c")
		bot.send_message(message.chat.id, f"Обрати внимание на формат!\nФормат: БМТX-XX(Б|М) ")
		bot.register_next_step_handler(message, user_registration)



# _________________________________ПРИВЕТСТВЕННЫЙ ЭКРАН________________________________________
@bot.message_handler(commands=['start'])
def send_welcome(message):
	"""
	Приветственный экран
	"""
	create_database(name='semester_forms')
	users_ids = get_ids_from_database(name='semester_forms')
	show_database(name='semester_forms', type='users')
	show_database(name='semester_forms', type='forms')

	if message.from_user.id in users_ids:
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		button1 = types.KeyboardButton('Семестровый опрос')
		button2 = types.KeyboardButton('Обратная связь')
		markup.row(button1)
		markup.row(button2)
		bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Чем могу помочь?", reply_markup=markup)
		print(message.from_user.id)
		bot.register_next_step_handler(message, start)

	else:
		bot.send_message(message.chat.id, f"Привет! Кажется мы еще не знакомы. \nПожалуйста, введи свою группу! \nФормат: БМТX-XX(Б|М)")
		bot.register_next_step_handler(message, user_registration)


def start(message):
	"""
	Обработка выбранной на стартовом экране опции
	Семестровый опрос - пользователь отвечает на последовательность вопросов
	Обратная связь - пользователь пишет обращение в свободной форме
	"""

# _______________________________СЕМЕСТРОВЫЕ ФОРМЫ_____________________________________
	@bot.callback_query_handler(func=lambda callback: True)
	def semester_form(callback):
		"""
		Последовательный вывод вопросов из вопросника и прием ответов
		"""

		requirement = ''
		discipline = disciplines[int(callback.data)]
		user_id = callback.from_user.id
		date = datetime.datetime.fromtimestamp(callback.message.date).strftime('%Y-%m-%d %H:%M:%S')
		arguments = [user_id, date, discipline]
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
					arguments.append(answer.text)
					ask(answer)
				else:
					print(f"{quest['text']} incorrect answer text -> {answer.text} from {answer.from_user.first_name}")
					wrong_input(answer, requirement)
					ask(answer)
			except StopIteration:
				arguments.append(answer.text)
				insert_field('semester_forms', type='forms', args=tuple(arguments))
				bot.send_message(message.chat.id, "Спасибо за ответы!")

		questions = (q for q in form_data.values())
		quest = next(questions)
		ask(message)

# _____________________________________FEEDBACK_____________________________________

	def read_feedback(message):
		"""
		Функция для чтения обращение пользователя
		Принимает только текст
		"""
		if message.content_type == 'text':
			date = datetime.datetime.fromtimestamp(message.date).strftime('%Y-%m-%d %H:%M:%S')
			with open("feedback.txt", "a", encoding='UTF-8') as file:
				file.write(f'From {message.from_user.first_name} {message.from_user.last_name} at {date}: {message.text}\n')
			bot.send_message(465825972, f"*Feedback from* {message.from_user.first_name} {message.from_user.last_name}: {message.text}", parse_mode='markdown')
			bot.send_message(message.chat.id, "Спасибо за обратную связь!")
		else:
			bot.send_message(message.chat.id, "Словами, пожалуйста")
			bot.send_message(message.chat.id, "Ваши замечания/предложения:")
			bot.register_next_step_handler(message, read_feedback)

# ______________________Обработка нажатий на стартовом экране___________________________

	if message.text == 'Семестровый опрос':
		group = get_group_by_id(name='semester_forms', tg_id=message.from_user.id)
		try:
			disciplines = disciplines_data[group]
			markup = types.InlineKeyboardMarkup()
			for i, discipline in enumerate(disciplines):
				button = types.InlineKeyboardButton(discipline, callback_data=str(i))
				markup.row(button)
			bot.send_message(message.chat.id, "Выбери предмет!", reply_markup=markup)
			#bot.register_next_step_handler(message, semester_form)
		except KeyError:
			bot.send_message(message.chat.id, "Упс, кажется твоей группы нет в списках!")
			bot.send_message(message.chat.id, "Проверь корректность группы через /edit или обратись за помощью /help ")


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
					if (x >= 1) and (x <= 10):
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


# _____________________________________INFO, HELP, EDIT___________________________________________

@bot.message_handler(commands=['info'])
def info(message):
	bot.send_message(message.chat.id,
'''Привет! Я Бот обратной связи *Факультета БМТ*!
Моя задача (удивительно) собирать *обратную связь* студентов!
Свою задачу я решаю двумя способами: семестровые формы и обращения
*Семестровая форма* - анкета с вопросами по конкретной дисциплине, которую лучше всего заполнять в конце семетра.
*Обращение* - возможность для Вас в свободной форме высказаться на любую тему.
Все ответы хранятся используются в *обезличенном виде*, так как я сторонник анонимности!
Cтарайтесь писать мне чаще по вопросам, которые Вас беспокоят, чтобы вы вместе делали наш *Факультет БМТ* лучше!
Используйте /start для начала общения со мной.''',
				parse_mode='markdown')


@bot.message_handler(commands=['help'])
def help(message):
	markup = types.InlineKeyboardMarkup()
	button1 = types.InlineKeyboardButton('Матвей Могилев', url="https://t.me/Avowed721")
	markup.row(button1)
	bot.send_message(message.chat.id, "Если что-то не работает, пишите!", reply_markup=markup)


@bot.message_handler(commands=['edit'])
def edit(message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	button1 = types.KeyboardButton('Да')
	button2 = types.KeyboardButton('Нет')
	button3 = types.KeyboardButton('А какая у меня группа? 👉👈')
	markup.row(button1, button2)
	markup.row(button3)
	bot.send_message(message.chat.id, f"Вы хотите изменить свою группу?", reply_markup=markup)
	bot.register_next_step_handler(message, group_edit)



# ___________________________________ИЗМЕНЕНИЕ ГРУППЫ_______________________________________
def group_edit(message):
	if message.text == 'Нет':
		bot.send_message(message.chat.id, "Хорошо!")
	elif message.text == 'А какая у меня группа? 👉👈':
		bot.send_message(message.chat.id, "Так так так...")
		user_group = get_group_by_id(name='semester_forms', tg_id=message.from_user.id)
		bot.send_message(message.chat.id, f"Ваша группа: {user_group.strip().upper()}")
	elif message.text == 'Да':
		bot.send_message(message.chat.id, "Введите новую группу:")
		bot.register_next_step_handler(message, group_edit_2)


def group_edit_2(message):
	group = message.text.strip().upper()
	if is_group_correct(group):
		update_group(name='semester_forms', tg_id=message.from_user.id, group=group )
		bot.send_message(message.chat.id, f"Готово! \nТеперь Ваша группа: {group}")
	else:
		bot.send_message(message.chat.id, f"Обрати внимание на формат!\nФормат: БМТX-XX(Б|М) ")
		bot.register_next_step_handler(message, group_edit_2)


@bot.message_handler(content_types=['text'])
def other(message):
	bot.send_message(message.chat.id,
f''' /start - начать
/info - полезная информация
/help - помощь
/edit - изменить группу''',
				parse_mode='markdown')




bot.infinity_polling()