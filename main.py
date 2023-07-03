import telebot
from telebot import types
import json
import sqlite3
import datetime
from dataclasses import dataclass, field
from contextlib import closing
import pandas as pd

with open("token.txt", 'r') as file:
    token = file.readline()

with open("form.json", 'r', encoding="UTF-8") as file:
    form_data = json.load(file)

with open("disciplines.json", 'r', encoding="UTF-8") as file:
    disciplines_data = json.load(file)

bot = telebot.TeleBot(token)

admin_id = 465825972
database_name = 'feedback.sql'
teachers_data = 'teachers.xlsx'

groups = disciplines_data.keys()


@dataclass
class User:
    id: int = 0
    group: str = None

    degree: str = None
    department: str = None
    semester: str = None

    def registration(self, message):

        degree = message.text
        self.id = message.from_user.id

        if degree in ['Бакалавриат', 'Магистратура']:
            self.degree = degree
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

            if self.degree == 'Бакалавриат':
                markup.row(types.KeyboardButton('БМТ1'), types.KeyboardButton('БМТ2'))
            elif self.degree == 'Магистратура':
                markup.row(types.KeyboardButton('БМТ1'), types.KeyboardButton('БМТ2'))
                markup.row(types.KeyboardButton('БМТ3'), types.KeyboardButton('БМТ4'))
                markup.row(types.KeyboardButton('БМТ5'))

            bot.send_message(message.chat.id, "Выберите кафедру", reply_markup=markup)
            bot.register_next_step_handler(message, self.choose_department)

        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
            bot.register_next_step_handler(message, self.registration)

    def choose_department(self, message):
        department = message.text
        if department in ['БМТ1', 'БМТ2', 'БМТ3', 'БМТ4', 'БМТ5']:
            self.department = department
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

            n = 9 if self.degree[0] == 'Б' else 5
            for i in range(1, n, 2):
                markup.row(types.KeyboardButton(f'Семестр {i}'), types.KeyboardButton(f'Семестр {i + 1}'))

            bot.send_message(message.chat.id, "Выберите семестр", reply_markup=markup)
            bot.register_next_step_handler(message, self.choose_semester)
        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
            bot.register_next_step_handler(message, self.choose_department)

    def choose_semester(self, message):
        semester = message.text
        if semester in ['Семестр 1', 'Семестр 2', 'Семестр 3', 'Семестр 4',
                        'Семестр 5', 'Семестр 6', 'Семестр 7', 'Семестр 8']:
            self.semester = semester
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

            local_groups = [group for group in groups if
                            (group[-1] == self.degree[0]) and
                            (group[3] == self.department[-1]) and
                            (group[5] == self.semester[-1])]

            for group in local_groups:
                markup.row(types.KeyboardButton(group))
            bot.send_message(message.chat.id, "Выберите группу", reply_markup=markup)
            bot.register_next_step_handler(message, self.choose_group)

        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
            bot.register_next_step_handler(message, self.choose_semester)

    def choose_group(self, message):
        group = message.text
        if group in groups:
            self.group = group
            if message.from_user.id in database.get_ids():
                self.update_group()
                bot.send_message(message.chat.id, f"Готово! \nТеперь Ваша группа: {group}")
            else:
                self.insert_group()
                bot.send_message(message.chat.id, f"Приятно познакомиться! 👋\nНажмите /start, чтобы начать ")
        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
            bot.register_next_step_handler(message, self.choose_group)

    def insert_group(self):
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:

            sql_script = "INSERT INTO users (id, group_name) VALUES(?, ?)"

            data_tuple = (self.id, self.group)
            cursor.execute(sql_script, data_tuple)
            connection.commit()
        connection.close()

    def update_group(self):
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:

            sql_script = "UPDATE users SET group_name = ? WHERE id = ?"

            data_tuple = (self.group, self.id)
            cursor.execute(sql_script, data_tuple)
            connection.commit()
        connection.close()

    def group_edit(self, message):
        if message.text == 'Нет':
            bot.send_message(message.chat.id, "Хорошо!")
        elif message.text == 'А какая у меня группа? 👉👈':
            bot.send_message(message.chat.id, "Так так так...")
            bot.send_message(message.chat.id, f"Ваша группа: {database.get_group_by_id()}")
        elif message.text == 'Да':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button1 = types.KeyboardButton("Бакалавриат")
            button2 = types.KeyboardButton("Магистратура")
            markup.row(button1)
            markup.row(button2)
            bot.send_message(message.chat.id, "Где Вы обучаетесь?", reply_markup=markup)
            bot.register_next_step_handler(message, self.registration)
        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️")
            bot.register_next_step_handler(message, self.group_edit)


@dataclass
class Database:
    id: int = 0

    @staticmethod
    def create():
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

            teachers = pd.read_excel(teachers_data)
            teachers.to_sql('teachers', connection, index=False, if_exists="replace")

            cursor.execute(users)
            cursor.execute(forms)
            cursor.execute(feedback)
            connection.commit()
        connection.close()

    @staticmethod
    def get_ids():
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT id FROM users")
            users_ids = cursor.fetchall()
            users_ids = [i[0] for i in users_ids]
        connection.close()
        return users_ids

    def get_group_by_id(self):
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:

            sql_script = "SELECT group_name FROM users WHERE id = ?"

            data_tuple = (self.id, )
            cursor.execute(sql_script, data_tuple)
            group = cursor.fetchone()[0]
        connection.close()
        return group


@dataclass
class Feedback:
    id: int = 0
    datetime: str = None
    feedback: str = None

    def add_feedback(self):
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:

            sql_script = "INSERT INTO feedback (id, datetime, feedback) VALUES(?, ?, ?)"

            data_tuple = (self.id, self.datetime, self.feedback)
            cursor.execute(sql_script, data_tuple)
            connection.commit()
        connection.close()

    @staticmethod
    def read_feedback(message):
        if message.content_type == 'text':
            feedback.datetime = datetime.datetime.fromtimestamp(message.date).strftime('%Y-%m-%d %H:%M:%S')
            feedback.feedback = message.text
            feedback.add_feedback()

            bot.send_message(465825972, f"💬 *New Feedback*: {message.text}", parse_mode='markdown')
            bot.send_message(message.chat.id, "Спасибо за обратную связь! 🙏")
            bot.send_message(message.chat.id, "/start, если хотите написать что-нибудь еще")
        else:
            bot.send_message(message.chat.id, "Словами, пожалуйста 🙃")
            bot.send_message(message.chat.id, "Ваши замечания/предложения: ")
            bot.register_next_step_handler(message, feedback.read_feedback)


@dataclass
class SemesterForm:
    id: int = 0
    datetime: str = None
    discipline: str = None

    question: dict = field(default_factory=dict)
    questions: iter = field(default_factory=list)

    rates: list = field(default_factory=list)
    empty_disciplines: list = field(default_factory=list)

    def add_filled_form(self):
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:
            sql_script = """INSERT INTO forms 
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
            data_tuple = (self.id, self.datetime, self.discipline) + tuple(self.rates)
            cursor.execute(sql_script, data_tuple)
            connection.commit()
        connection.close()

    def get_filled_disciplines(self):
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:

            sql_script = "SELECT discipline FROM forms WHERE id = ?"

            data_tuple = (self.id, )
            cursor.execute(sql_script, data_tuple)
            data = cursor.fetchall()
            filled_disciplines = [i[0] for i in data]
        connection.close()
        return set(filled_disciplines)

    def list_of_teachers(self, semester):
        connection = sqlite3.connect(database_name)
        with closing(connection.cursor()) as cursor:
            sql_script = "SELECT * FROM teachers WHERE Предмет = ? AND Семестр = ?"
            data_tuple = (self.discipline, semester)
            cursor.execute(sql_script, data_tuple)
            teachers = cursor.fetchone()
        connection.close()

        if teachers is None:
            return None
        else:
            doubled_teachers = [[t, t] for t in teachers[2:]]      # Удвоение полученных типо занятий (т.к. 2 оценки на каждый тип)
            flat_teachers = [item for sublist in doubled_teachers for item in sublist] # Развертка в один список
            flat_teachers.append("Комментарии")                                       # Дополнительное поле для комментариев
            return flat_teachers

    def end_of_form(self, message):
        self.add_filled_form()
        self.rates = []
        bot.send_message(message.chat.id, "Спасибо за ответы! 🙏 \nПродолжим? /return для отмены")
        bot.send_message(465825972,
                         f"💬 *New Completed Form* for group: {database.get_group_by_id()}",
                         parse_mode='markdown')
        self.choose_semester_form(message)

    @staticmethod
    def pairwise(iterable):
        "s -> (s0, s1), (s2, s3), (s4, s5), ..."
        a = iter(iterable)
        return zip(a, a)

    def choose_semester_form(self, message):
        group = database.get_group_by_id()
        try:
            disciplines = set(disciplines_data[group])
            filled_disciplines = self.get_filled_disciplines()
            self.empty_disciplines = list(disciplines.difference(filled_disciplines))
            num_of_empty_disciplines = len(self.empty_disciplines)

            if num_of_empty_disciplines == 0:
                bot.send_message(message.chat.id,
                                 "Похоже Вы заполнили обратную связь по всем предметам! 🎉\nБольшое спасибо за уделенное время 🙏")
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for d1, d2 in self.pairwise(self.empty_disciplines):
                    markup.row(types.KeyboardButton(d1), types.KeyboardButton(d2))
                if num_of_empty_disciplines%2 == 1:
                    markup.row(types.KeyboardButton(self.empty_disciplines[-1]))

                bot.send_message(message.chat.id, "Выберите предмет!", reply_markup=markup)
                bot.register_next_step_handler(message, self.semester_form)
        except KeyError:
            bot.send_message(message.chat.id, "Ooops, кажется Вашей группы нет в списках! ☹️")
            bot.send_message(message.chat.id,
                             "Проверьте корректность группы через /edit или обратитесь за помощью /help")

    def semester_form(self, message):
        if message.text == '/return':
            bot.send_message(message.chat.id, "Опрос отменен 🔚", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, back_to_commands)

        elif message.text in self.empty_disciplines:

            self.datetime = datetime.datetime.fromtimestamp(message.date).strftime('%Y-%m-%d %H:%M:%S')
            self.discipline = message.text

            group = database.get_group_by_id()
            teachers = self.list_of_teachers(semester=group[5])   # Получение списка преподавателей по семестру и дисциплине
            print(teachers)

            if teachers is None:
                bot.send_message(message.chat.id, "Ooops, кажется данного предмета нет в базе! ☹️ \nУже сообщил о проблеме, скоро добавим \nВыберите другой предмет")
                bot.send_message(465825972,
                                 f"❗ Отсутствует дисциплина *{message.text}* у группы *{group}*",
                                 parse_mode='markdown')
                bot.register_next_step_handler(message, self.semester_form)

            else:
                for i, q in enumerate(form_data.keys()):
                    form_data[q]['teacher'] = teachers[i]

                self.questions = iter(form_data.values())
                self.question = next(self.questions)
                self.ask(message)

        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️ \n/return для отмены опроса")
            bot.register_next_step_handler(message, self.semester_form)

    def ask(self, message):

        if self.question['teacher'] is not None:
            if self.question['type'] == 'scale':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                for i in range(1, 11, 2):
                    markup.row(types.KeyboardButton(str(i)), types.KeyboardButton(str(i+1)))
                bot.send_message(message.chat.id, self.question['text'] + f'\nПреподаватель: {self.question["teacher"]}', reply_markup=markup)

            elif self.question['type'] == 'text':
                bot.send_message(message.chat.id, self.question['text'], reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, self.read_answer)
        else:
            try:
                form.rates.extend([None, None])
                next(self.questions)
                self.question = next(self.questions)
                self.ask(message)
            except StopIteration:
                self.end_of_form(message)


    def read_answer(self, message):
        if message.text == '/return':
            bot.send_message(message.chat.id,
                             "Данные не были сохранены ⚠️",
                             reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, back_to_commands)
        elif message.content_type == 'text' and (self.question['type'] == 'text' or
                                                 self.question['type'] == 'scale' and
                                                 message.text in [str(i) for i in range(1, 11)]):
            try:
                form.rates.append(message.text)
                self.question = next(self.questions)
                self.ask(message)
            except StopIteration:
                self.end_of_form(message)

        else:
            bot.send_message(message.chat.id, "Используйте кнопки 🙃️ \n/return для отмены опроса")
            bot.register_next_step_handler(message, self.read_answer)


user = User()
database = Database()
feedback = Feedback()
form = SemesterForm()

# _________________________________ПРИВЕТСТВЕННЫЙ ЭКРАН________________________________________

@bot.message_handler(commands=['start'])
def send_welcome(message):
    database.create()
    users_ids = database.get_ids()

    user_id = message.from_user.id

    user.id = user_id
    database.id = user_id
    feedback.id = user_id
    form.id = user_id

    if user_id in users_ids:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton('📑 Семестровый опрос')
        button2 = types.KeyboardButton('✍️ Обратная связь')
        markup.row(button1)
        markup.row(button2)
        if user_id == admin_id:
            markup.row(types.KeyboardButton('💽 База данных'))
        bot.send_message(message.chat.id, f"Привет! Чем могу помочь? 💁🏻", reply_markup=markup)
        bot.register_next_step_handler(message, start)

    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton("Бакалавриат")
        button2 = types.KeyboardButton("Магистратура")
        markup.row(button1, button2)
        bot.send_message(message.chat.id,
                         "Привет! Кажется мы еще не знакомы. \nГде Вы обучаетесь?",
                         reply_markup=markup)
        bot.register_next_step_handler(message, user.registration)


def start(message):

    if message.text == '📑 Семестровый опрос':
        form.choose_semester_form(message)

    elif message.text == '✍️ Обратная связь':
        bot.send_message(message.chat.id, "Ваши замечания/предложения: ️")
        bot.register_next_step_handler(message, feedback.read_feedback)

    elif message.text == '💽 База данных' and user.id == admin_id:
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

    elif message.text == '/return':
        back_to_commands(message)

    else:
        bot.send_message(message.chat.id, "Используйте кнопки или команды 🙃️")
        bot.register_next_step_handler(message, start)


# _____________________________________COMMANDS___________________________________________

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
                     '''Привет! Я Бот обратной связи *Факультета БМТ* 🧬
Я использую семестровые формы и обращения, чтобы накапливать обратную связь студентов.
*Семестровая форма* - анкета с вопросами по одной из дисциплин текущего семестра.
*Обращение* - возможность высказаться в свободной форме на любую тему.
Все ответы хранятся в *обезличенном виде*.
Используйте /start для начала общения со мной.''',
                     parse_mode='markdown', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['help'])
def help(message):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('🙋‍♂️ Матвей Могилев', url="https://t.me/Avowed721")
    markup.row(button1)
    bot.send_message(message.chat.id, "Если что-то не работает, пишите! 👇", reply_markup=markup)


@bot.message_handler(commands=['return'])
def back_to_commands(message):
    commands(message)


@bot.message_handler(commands=['edit'])
def edit(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Да')
    button2 = types.KeyboardButton('Нет')
    button3 = types.KeyboardButton('А какая у меня группа? 👉👈')
    markup.row(button1, button2)
    markup.row(button3)
    bot.send_message(message.chat.id, f"Вы хотите изменить свою группу?", reply_markup=markup)
    bot.register_next_step_handler(message, user.group_edit)


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
