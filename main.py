import telebot
from telebot import types
import json
import sqlite3
from re import match
import datetime
from contextlib import closing

with open("token.txt", 'r') as file:
    token = file.readline()

with open("form.json", 'r', encoding="UTF-8") as file:
    form_data = json.load(file)

with open("disciplines.json", 'r', encoding="UTF-8") as file:
    disciplines_data = json.load(file)

bot = telebot.TeleBot(token)
database_name = 'feedback.sql'

# ___________________________________БАЗА ДАННЫХ_________________________________________
def create_database():
    """
    Создает базу данных, если она еще не была создана
    Поля: id, группа
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id int primary key, group_name varchar(10))')
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS feedback (id int, datetime varchar(25) primary key, feedback varchar(500))')
        cursor.execute('CREATE TABLE IF NOT EXISTS forms (id int, datetime varchar(25) primary key, discipline varchar(25), \
                                                      lection int, lector int, seminar int, seminarist int, comments varchar(500))')
        connection.commit()
    connection.close()

def insert_field(table, args):
    """
    Добавление нового поля в таблицу
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:
        if table == 'users':
            cursor.execute("INSERT INTO users (id, group_name) VALUES('%s', '%s')" % args)
        elif table == 'forms':
            cursor.execute("INSERT INTO forms (id, datetime, discipline, lector, lection, seminar, seminarist, comments) \
                                            VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % args)
        elif table == 'feedback':
            cursor.execute("INSERT INTO feedback (id, datetime, feedback) VALUES('%s', '%s', '%s')" % args)
        connection.commit()
    connection.close()


def get_ids():
    """
    Получение id всех пользователей
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:
        cursor.execute("SELECT id FROM users")
        users_ids = cursor.fetchall()
        users_ids = [i[0] for i in users_ids]
    connection.close()
    return users_ids


def get_group_by_id(tg_id):
    """
    Получение группы по id пользователя
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:
        cursor.execute("SELECT group_name FROM users WHERE id = '%s'" % tg_id)
        group = cursor.fetchone()[0]
    connection.close()
    return group


def get_filled_disciplines(tg_id):
    """
    Получение спика дисциплин, которые уже были заполнены пользователем
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:
        cursor.execute("SELECT discipline FROM forms WHERE id = '%s'" % tg_id)
        data = cursor.fetchall()
        filled_disciplines = [i[0] for i in data]
    connection.close()
    return set(filled_disciplines)


def update_group(tg_id, group):
    """
    Обновление группы пользователя
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:
        cursor.execute("UPDATE users SET group_name = '%s' WHERE id = '%s'" % (group, tg_id))
        connection.commit()
    connection.close()

# ______________________________Регистрация пользователя по группе__________________________

# def is_group_correct(group):
#     """
#     Проверка корректности ввода группы
#     """
#     s = group.strip().upper()
#     res = match(r'БМТ[1-5]-[1-8][1-3][Б, М]$', s)
#     if res is None:
#         return False
#     else:
#         return True

def user_registration(message):
    """
    Регистрация пользователя по группе и id в телеграме
    """
    level = message.text
    local_groups = []

    if level in ['Бакалавриат', 'Магистратура']:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        groups = disciplines_data.keys()
        if level == 'Бакалавриат':
            local_groups = [group for group in groups if group.endswith('Б')]
        elif level == 'Магистратура':
            local_groups = [group for group in groups if group.endswith('М')]

        for group1, group2 in grouped(local_groups, 2):
            markup.row(types.KeyboardButton(group1), types.KeyboardButton(group2))
        bot.send_message(message.chat.id, "Пожалуйста, выберите свою группу", reply_markup=markup)
        bot.register_next_step_handler(message, choose_group)

    else:
        bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки 🙃️")
        bot.register_next_step_handler(message, user_registration)

def choose_group(message):

    group = message.text
    if group in disciplines_data.keys():
        insert_field(table='users', args=(message.from_user.id, group))
        bot.send_message(message.chat.id, f"Приятно познакомиться! 👋\nНажмите /start, чтобы начать ")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки 🙃️")
        bot.register_next_step_handler(message, choose_group)

# _________________________________ПРИВЕТСТВЕННЫЙ ЭКРАН________________________________________


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Приветственный экран
    """
    create_database()
    users_ids = get_ids()

    if message.from_user.id in users_ids:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton('📑 Семестровый опрос')
        button2 = types.KeyboardButton('✍️ Обратная связь')
        markup.row(button1)
        markup.row(button2)
        bot.send_message(message.chat.id, f"Привет! Чем могу помочь? 💁🏻", reply_markup=markup)
        bot.register_next_step_handler(message, start)

    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton("Бакалавриат")
        button2 = types.KeyboardButton("Магистратура")
        markup.row(button1)
        markup.row(button2)
        bot.send_message(message.chat.id,
                         "Привет! Кажется мы еще не знакомы. \nГде Вы обучаетесь?",
                         reply_markup=markup)
        bot.register_next_step_handler(message, user_registration)


def start(message):
    """
    Обработка выбранной на стартовом экране опции
    Семестровый опрос - пользователь отвечает на последовательность вопросов
    Обратная связь - пользователь пишет обращение в свободной форме
    """

    # _______________________________СЕМЕСТРОВЫЕ ФОРМЫ_____________________________________
    disciplines = ''

    def semester_form(message):
        """
        Последовательный вывод вопросов из вопросника и прием ответов
        """
        if message.text == '/return':
            bot.send_message(message.chat.id, "Опрос отменен 🔚", reply_markup=types.ReplyKeyboardRemove())
            back_to_info(message)
            return 0

        nonlocal disciplines

        if message.text not in disciplines:
            bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки 🙃️")
            choose_semester_form(message)
            return 0

        requirement = ''
        current_user_discipline = message.text
        user_id = message.from_user.id
        date = datetime.datetime.fromtimestamp(message.date).strftime('%Y-%m-%d %H:%M:%S')
        arguments = [user_id, date, current_user_discipline]

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
            if answer.text == '/return':
                bot.send_message(message.chat.id, "Данные не были сохранены ⚠️")
                back_to_info(answer)
                return 0

            nonlocal quest
            try:
                if is_correct(answer, requirement):
                    quest = next(questions)
                    arguments.append(answer.text)
                    ask(answer)
                else:
                    wrong_input(answer, requirement)
                    ask(answer)
            except StopIteration:
                arguments.append(answer.text)
                insert_field(table='forms', args=tuple(arguments))
                bot.send_message(message.chat.id, "Спасибо за ответы! 🙏")
                bot.send_message(465825972,
                                 f"💬 *New Completed Form* for group: {get_group_by_id(tg_id=message.from_user.id)}",
                                 parse_mode='markdown')
                bot.send_message(message.chat.id, "Продолжим? /return для отмены")
                choose_semester_form(message)

        questions = (q for q in form_data.values())
        quest = next(questions)
        ask(message)

    def choose_semester_form(message):
        '''
        Выводит кнопки с дисциплинами в зависимости от группы пользователя
        Далее перенаправляет в semester_form(), если группа есть в базе
        '''
        nonlocal disciplines
        group = get_group_by_id(tg_id=message.from_user.id)
        try:
            disciplines = set(disciplines_data[group])
            filled_disciplines = get_filled_disciplines(tg_id=message.from_user.id)  # Определение списка уже заполненных предметов
            disciplines = list(
                disciplines.difference(filled_disciplines))  # Определение списка еще не заполненных предметов

            if len(disciplines) == 0:
                bot.send_message(message.chat.id,
                                 "Похоже Вы заполнили обратную связь по всем предметам! 🎉\nБольшое спасибо за уделенное время 🙏")
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for discipline in disciplines:
                    button = types.KeyboardButton(discipline)
                    markup.row(button)
                bot.send_message(message.chat.id, "Выберите предмет!", reply_markup=markup)
                bot.register_next_step_handler(message, semester_form)
        except KeyError:
            bot.send_message(message.chat.id, "Упс, кажется Вашей группы нет в списках! ☹️")
            bot.send_message(message.chat.id, "Проверьте корректность группы через /edit или обратитесь за помощью /help")

    # _____________________________________FEEDBACK_____________________________________

    def read_feedback(message):
        """
        Функция для чтения обращение пользователя
        Принимает только текст
        """

        if message.content_type == 'text':
            date = datetime.datetime.fromtimestamp(message.date).strftime('%Y-%m-%d %H:%M:%S')
            insert_field(table='feedback', args=(message.from_user.id, date, message.text))
            bot.send_message(465825972, f"💬 *New Feedback*: {message.text}", parse_mode='markdown')
            bot.send_message(message.chat.id, "Спасибо за обратную связь! 🙏")
            bot.send_message(message.chat.id, "/start, если хотите написать что-нибудь еще")
        else:
            bot.send_message(message.chat.id, "Словами, пожалуйста 🙃")
            bot.send_message(message.chat.id, "Ваши замечания/предложения: ")
            bot.register_next_step_handler(message, read_feedback)

    # ______________________Обработка нажатий на стартовом экране___________________________

    if message.text == '📑 Семестровый опрос':
        choose_semester_form(message)

    elif message.text == '✍️ Обратная связь':
        bot.send_message(message.chat.id, "Ваши замечания/предложения: ️")
        bot.register_next_step_handler(message, read_feedback)


    elif message.text == '/help':
        help(message)

    elif message.text == '/info':
        info(message)

    elif message.text == '/edit':
        edit(message)

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
                bot.send_message(message.chat.id, 'Введите целое число от 1 до 10 🔢')
            if requirement == 'string':
                bot.send_message(message.chat.id, 'Используйте буквы и числа! 🔡')
        else:
            bot.send_message(message.chat.id, 'Используйте буквы и числа! 🔡')


# _____________________________________INFO, HELP, EDIT, RETURN___________________________________________

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
                     '''Привет! Я Бот обратной связи *Факультета БМТ* 🧬
Я использую семестровые формы и обращения, чтобы накапливать обратную связь студентов.
*Семестровая форма* - анкета с вопросами по одной из дисциплин текущего семестра.
*Обращение* - возможность высказаться в свободной форме на любую тему.
Все ответы хранятся в *обезличенном виде*. Я сторонник анонимности!
Используйте /start для начала общения со мной.''',
                     parse_mode='markdown', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['help'])
def help(message):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('🙋‍♂️ Матвей Могилев', url="https://t.me/Avowed721")
    markup.row(button1)
    bot.send_message(message.chat.id, "Если что-то не работает, пишите! 👇", reply_markup=markup)


@bot.message_handler(commands=['return'])
def back_to_info(message):
    commands(message)


# ___________________________________ИЗМЕНЕНИЕ ГРУППЫ_______________________________________

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


def group_edit(message):
    if message.text == 'Нет':
        bot.send_message(message.chat.id, "Хорошо!")
    elif message.text == 'А какая у меня группа? 👉👈':
        bot.send_message(message.chat.id, "Так так так...")
        user_group = get_group_by_id(tg_id=message.from_user.id)
        bot.send_message(message.chat.id, f"Ваша группа: {user_group}")
    elif message.text == 'Да':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        groups = disciplines_data.keys()
        for group1, group2 in grouped(groups, 2):
            markup.row(types.KeyboardButton(group1), types.KeyboardButton(group2))
        bot.send_message(message.chat.id, "Выберите новую группу", reply_markup=markup)
        bot.register_next_step_handler(message, group_update)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки 🙃️")
        edit(message)


def group_update(message):

    group = message.text
    if group in disciplines_data.keys():
        update_group(tg_id=message.from_user.id, group=group)
        bot.send_message(message.chat.id, f"Готово! \nТеперь Ваша группа: {group}")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки 🙃️")
        bot.register_next_step_handler(message, group_update)


# ___________________________________МЕНЮ С КОМАНДАМИ_______________________________________

@bot.message_handler(content_types=['text'])
def commands(message):
    bot.send_message(message.chat.id,
                     f''' /start - начать
/info - полезная информация
/return - выйти из опроса
/help - помощь 
/edit - изменить группу''',
                     parse_mode='markdown', reply_markup=types.ReplyKeyboardRemove())

def grouped(iterable, n):
    return zip(*[iter(iterable)]*n)


bot.infinity_polling()
