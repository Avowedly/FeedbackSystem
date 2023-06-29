import telebot
from telebot import types
import json
import sqlite3
import datetime
from contextlib import closing

with open("token.txt", 'r') as file:
    token = file.readline()

with open("form.json", 'r', encoding="UTF-8") as file:
    form_data = json.load(file)

with open("disciplines.json", 'r', encoding="UTF-8") as file:
    disciplines_data = json.load(file)

bot = telebot.TeleBot(token)

admin_id = 465825972
database_name = 'feedback.sql'
groups = disciplines_data.keys()
degree = ''

# ___________________________________БАЗА ДАННЫХ_________________________________________
def create_database():
    """
    Создает базу данных, если она еще не была создана
    Поля: id, группа
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:

        users = '''CREATE TABLE IF NOT EXISTS users 
        (
            id int primary key, 
            group_name varchar(10)
        )'''

        feedback = '''CREATE TABLE IF NOT EXISTS feedback 
        (
            id int, 
            datetime varchar(25) primary key, 
            feedback varchar(500)
        )
        '''

        forms = '''CREATE TABLE IF NOT EXISTS forms 
        (
            id int, datetime varchar(25) primary key, 
            discipline varchar(25), 
            lec int, 
            lecm int, 
            sem int, 
            semm int, 
            lab int, 
            labm int, 
            proj int,
            projm int,
            comments varchar(500)
        )
        '''

        cursor.execute(users)
        cursor.execute(forms)
        cursor.execute(feedback)
        connection.commit()
    connection.close()

def insert_field(table, args):
    """
    Добавление нового поля в таблицу
    """
    connection = sqlite3.connect(database_name)
    with closing(connection.cursor()) as cursor:

        users = '''INSERT INTO users 
        (
            id, 
            group_name
        ) 
        VALUES('%s', '%s')
        '''

        feedback = '''INSERT INTO feedback 
        (
            id, 
            datetime, 
            feedback
        ) 
        VALUES('%s', '%s', '%s')
        '''

        forms = '''INSERT INTO forms 
        (
            id, 
            datetime, 
            discipline, 
            lec, 
            lecm, 
            sem, 
            semm, 
            lab, 
            labm, 
            proj, 
            projm, 
            comments
        ) 
        VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s','%s','%s','%s')
        '''

        if table == 'users':
            cursor.execute(users % args)
        elif table == 'forms':
            cursor.execute(forms % args)
        elif table == 'feedback':
            cursor.execute(feedback % args)
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

def user_registration(message):
    """
    Регистрация пользователя по группе и id в телеграме
    """
    global degree
    degree = message.text

    if degree in ['Бакалавриат', 'Магистратура']:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

        if degree == 'Бакалавриат':
            for i in range(1, 3):
                markup.row(types.KeyboardButton(f'БМТ{i}'))
        elif degree == 'Магистратура':
            for i in range(1, 6):
                markup.row(types.KeyboardButton(f'БМТ{i}'))

        bot.send_message(message.chat.id, "Выберите кафедру", reply_markup=markup)
        bot.register_next_step_handler(message, choose_department)

    else:
        bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
        bot.register_next_step_handler(message, user_registration)

def choose_department(message):
    if message.text in ['БМТ1', 'БМТ2', 'БМТ3', 'БМТ4', 'БМТ5']:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        global department
        global degree
        N = 9 if degree[0] == 'Б' else 5
        department = message.text
        for i in range(1, N, 2):
            markup.row(types.KeyboardButton(f'Семестр {i}'), types.KeyboardButton(f'Семестр {i + 1}'))

        bot.send_message(message.chat.id, "Выберите семестр", reply_markup=markup)
        bot.register_next_step_handler(message, choose_semester)

    else:
        bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
        bot.register_next_step_handler(message, choose_department)


def choose_semester(message):
    semester = message.text
    if semester in ['Семестр 1', 'Семестр 2', 'Семестр 3', 'Семестр 4', 'Семестр 5', 'Семестр 6', 'Семестр 7', 'Семестр 8']:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        global groups
        global degree
        global department
        local_groups = [group for group in groups if (group[-1] == degree[0]) and (group[3] == department[-1]) and (group[5] == semester[-1])]
        for group in local_groups:
            markup.row(types.KeyboardButton(group))
        bot.send_message(message.chat.id, "Выберите группу", reply_markup=markup)
        bot.register_next_step_handler(message, choose_group)

    else:
        bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
        bot.register_next_step_handler(message, choose_semester)

def choose_group(message):
    group = message.text
    if group in groups:
        if message.from_user.id in get_ids():    #Проверка, зарегистрирован ли пользователь на данным момент (отличает регистрацию от изменения группы)
            update_group(tg_id=message.from_user.id, group=group)
            bot.send_message(message.chat.id, f"Готово! \nТеперь Ваша группа: {group}")
        else:
            insert_field(table='users', args=(message.from_user.id, group))
            bot.send_message(message.chat.id, f"Приятно познакомиться! 👋\nНажмите /start, чтобы начать ")
    else:
        bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
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
        if message.from_user.id == admin_id :
            button3 = types.KeyboardButton('💽 База данных')
            markup.row(button3)
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
                    markup.row(types.KeyboardButton(discipline))
                bot.send_message(message.chat.id, "Выберите предмет!", reply_markup=markup)
                bot.register_next_step_handler(message, semester_form)
        except KeyError:
            bot.send_message(message.chat.id, "Упс, кажется Вашей группы нет в списках! ☹️")
            bot.send_message(message.chat.id, "Проверьте корректность группы через /edit или обратитесь за помощью /help")


    def semester_form(message):
        """
        Последовательный вывод вопросов из вопросника и прием ответов
        """

        if message.text == '/return':
            bot.send_message(message.chat.id, "Опрос отменен 🔚", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, back_to_info)

        elif message.text in disciplines:

            current_discipline = message.text
            user_id = message.from_user.id
            date = datetime.datetime.fromtimestamp(message.date).strftime('%Y-%m-%d %H:%M:%S')
            answers = [user_id, date, current_discipline]

            questions = (q for q in form_data.values())
            question = next(questions)
            quest_type = question['type']
            def ask(message):
                """
                Функция для вывода вопроса в чат
                """
                nonlocal quest_type
                quest_type = question['type']
                quest_text = question['text']
                if quest_type == 'scale':
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    for i in range(1, 11, 2):
                        markup.row(types.KeyboardButton(str(i)), types.KeyboardButton(str(i+1)))
                    markup.row('Такого вида занятий не было')
                    bot.send_message(message.chat.id, quest_text, reply_markup=markup)
                if quest_type == 'text':
                    bot.send_message(message.chat.id, quest_text, reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, read_answer)

            def read_answer(message):
                """
                Функция для чтения ответа пользователя
                Проверяет корректность ввода в зависимости от требований в переменной requirement
                Если ответ корректен по форме, то переходит к следующему вопросу,
                если нет - задает вопрос, пока не будет получен корректный ответ
                """
                if message.text == '/return':
                    bot.send_message(message.chat.id, "Данные не были сохранены ⚠️", reply_markup=types.ReplyKeyboardRemove())
                    bot.register_next_step_handler(message, back_to_info)
                elif message.content_type == 'text' and (quest_type == 'text' or
                                                         quest_type == 'scale' and
                                                         (message.text in [str(i) for i in range(1, 11)] or
                                                          message.text == 'Такого вида занятий не было')):
                    try:
                        nonlocal question
                        if message.text == 'Такого вида занятий не было':
                            question = next(questions)
                            answers.extend([None, None])
                        else:
                            answers.append(message.text)
                        question = next(questions)
                        ask(message)
                    except StopIteration:
                        insert_field(table='forms', args=tuple(answers))
                        bot.send_message(message.chat.id, "Спасибо за ответы! 🙏")
                        bot.send_message(465825972,
                                         f"💬 *New Completed Form* for group: {get_group_by_id(tg_id=message.from_user.id)}",
                                         parse_mode='markdown')
                        bot.send_message(message.chat.id, "Продолжим? /return для отмены")
                        choose_semester_form(message)
                else:
                    bot.send_message(message.chat.id, "Используйте кнопки/текст 🙃️")
                    bot.register_next_step_handler(message, read_answer)

            ask(message)                                        # Запуск анкетирования

        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️ \n/return для отмены опроса")
            bot.register_next_step_handler(message, semester_form)

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

    elif message.text == '💽 База данных' and message.from_user.id == admin_id:
        with open('feedback.sql', 'rb') as doc:
            bot.send_document(admin_id, doc)

    elif message.text == '/help':
        help(message)

    elif message.text == '/start':
        send_welcome(message)

    elif message.text == '/info':
        info(message)

    elif message.text == '/edit':
        edit(message)

    else:
        bot.send_message(message.chat.id, "Используйте кнопки или команды 🙃️")
        bot.register_next_step_handler(message, start)


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
        button1 = types.KeyboardButton("Бакалавриат")
        button2 = types.KeyboardButton("Магистратура")
        markup.row(button1)
        markup.row(button2)
        bot.send_message(message.chat.id, "Где Вы обучаетесь?", reply_markup=markup)
        bot.register_next_step_handler(message, user_registration)
    else:
        bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
        bot.register_next_step_handler(message, group_edit)


# ___________________________________МЕНЮ С КОМАНДАМИ_______________________________________

@bot.message_handler(content_types=['text'])
def commands(message):
    bot.send_message(message.chat.id,
                     f''' /start - начать
/edit - изменить группу
/return - выйти из опроса
/info - полезная информация
/help - помощь 
''',
                     parse_mode='markdown', reply_markup=types.ReplyKeyboardRemove())



bot.infinity_polling()
