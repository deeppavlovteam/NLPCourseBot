from DialogClasses import *
from Sqlighter import SQLighter
import universal_reply
import config
import random
from quizzes.QuizClasses import Quiz

wait_usr_interaction = State(name='WAIT_USR_INTERACTION',
                             triggers_out={'MAIN_MENU': {'phrases': ['/start'], 'content_type': 'text'}})
# ----------------------------------------------------------------------------

main_menu = State(name='MAIN_MENU',
                  row_width=2,
                  triggers_out={'PASS_HW_NUM_SELECT': {'phrases': ['🐟 Сдать дз 🐠'], 'content_type': 'text'},
                                'ASK_QUESTION_START': {'phrases': ['🦉 Задать вопрос 🦉'], 'content_type': 'text'},
                                'GET_MARK': {'phrases': ['🐝 Ваши оценки за дз 🐝'], 'content_type': 'text'},
                                'GET_QUIZ_MARK': {'phrases': ['🐝 Ваши оценки за квизы 🐝'], 'content_type': 'text'},
                                'CHECK_HW_NUM_SELECT': {'phrases': ['🐌 Проверить дз 🐌'], 'content_type': 'text'},
                                'ADMIN_MENU': {'phrases': [universal_reply.ADMIN_KEY_PHRASE], 'content_type': 'text'},
                                'TAKE_QUIZ': {'phrases': [universal_reply.quiz_enter], 'content_type': 'text'},
                                'CHECK_QUIZ': {'phrases': [universal_reply.quiz_check], 'content_type': 'text'}},
                  hidden_states={'state_name': 'ADMIN_MENU', 'users_file': config.admins},
                  welcome_msg='Выберите доступное действие, пожалуйста')

# ----------------------------------------------------------------------------


quiz = Quiz(config.quiz_name, quiz_json_path=config.quiz_path,
            next_global_state_name='MAIN_MENU')

class QuizState(State):

    def make_reply_markup(self):
        pass

    def welcome_handler(self, bot, message, sqldb: SQLighter):
        quiz.run(bot, message, sqldb)

    def out_handler(self, bot, message, sqldb: SQLighter):
        if message.content_type != 'text':
            return None
        new_state = quiz.run(bot, message, sqldb)
        return new_state


take_quiz = QuizState(name='TAKE_QUIZ')

# ----------------------------------------------------------------------------

check_quiz = State(name='CHECK_QUIZ',
                   triggers_out={
                       'SEND_QQUESTION_TO_CHECK': {'phrases': config.quizzes_possible_to_check, 'content_type': 'text'},
                       'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'}},
                   welcome_msg='Пожалуйста, выберите номер квиза для проверки:')


# ----------------------------------------------------------------------------

def send_qquestion(bot, message, sqldb):
    if message.text not in config.quizzes_possible_to_check:
        quiz_name = sqldb.get_latest_quiz_name(message.chat.username)
    else:
        quiz_name = message.text
    if quiz_name is None:
        bot.send_message("SMTH WENT WRONG..")
        return
    arr = sqldb.get_quiz_question_to_check(quiz_name=quiz_name,
                                           user_id=message.chat.username)
    if len(arr) > 0:
        q_id, q_name, q_text, q_user_ans, _ = arr
        sqldb.make_fake_db_record_quiz(q_id, message.chat.username)
        bot.send_message(chat_id=message.chat.id, text=q_text + '\n' + 'USER_ANSWER:\n' + q_user_ans)
    else:
        # TODO: do smth with empty db;
        bot.send_message(text='К сожалению проверить пока нечего.',
                         chat_id=message.chat.id)


send_quiz_question_to_check = State(name='SEND_QQUESTION_TO_CHECK',
                                    row_width=3,
                                    triggers_out={'SAVE_MARK': {'phrases': ['Верю', 'Не верю']},
                                                  'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'}},
                                    handler_welcome=send_qquestion,
                                    welcome_msg='Правильно или нет ответил пользователь?\n'
                                                'Нажмите кнопку, чтобы оценить ответ.')


# ----------------------------------------------------------------------------

def save_mark_quiz(bot, message, sqldb):
    is_right = int(message.text == 'Верю')
    sqldb.save_mark_quiz(message.chat.username, is_right)
    bot.send_message(text='Оценка сохранена. Спасибо.', chat_id=message.chat.id)


save_mark_quiz = State(name='SAVE_MARK',
                       row_width=2,
                       triggers_out={'SEND_QQUESTION_TO_CHECK': {'phrases': ['Продолжить проверку']},
                                     'CHECK_QUIZ': {'phrases': ['Назад']}},
                       handler_welcome=save_mark_quiz,
                       welcome_msg='Желаете ли еще проверить ответы из того же квиза?')

# ----------------------------------------------------------------------------

ask_question_start = State(name='ASK_QUESTION_START',
                           triggers_out={'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'},
                                         'SAVE_QUESTION': {'phrases': [], 'content_type': 'text'}},
                           welcome_msg='Сформулируйте вопрос к семинаристу и отправьте его одним сообщением 🐠.')


# ----------------------------------------------------------------------------

def save_question_handler(bot, message, sqldb):
    sqldb.write_question(message.chat.username, message.text)


save_question = State(name='SAVE_QUESTION',
                      triggers_out={'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'},
                                    'SAVE_QUESTION': {'phrases': [], 'content_type': 'text'}},
                      handler_welcome=save_question_handler,
                      welcome_msg='Спасибо за вопрос. Хорошего дня 🐯 :)\n'
                                  'Если желаете задать еще вопрос, напишите его сразу следующим сообщением.'
                                  'Если у вас нет такого желания, воспользуйтесь кнопкой "Назад".')

# ----------------------------------------------------------------------------

welcome_to_pass_msg = 'Пожалуйста, выберите номер задания для сдачи.'
welcome_to_return_msg = 'Доступные для сдачи задания отсутствуют.'
pass_hw_num_selection = State(name='PASS_HW_NUM_SELECT',
                              row_width=2,
                              triggers_out={'PASS_HW_CHOSEN_NUM': {'phrases': config.hw_possible_to_pass,
                                                                   'content_type': 'text'},
                                            'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'}},
                              welcome_msg=welcome_to_pass_msg if len(config.hw_possible_to_pass) > 0
                              else welcome_to_return_msg)


# ----------------------------------------------------------------------------

def make_fake_db_record(bot, message, sqldb):
    sqldb.make_fake_db_record(message.chat.username, message.text)


pass_hw_chosen_num = State(name='PASS_HW_CHOSEN_NUM',
                           triggers_out={'PASS_HW_UPLOAD': {'phrases': [], 'content_type': 'document'},
                                         'PASS_HW_NUM_SELECT': {'phrases': ['Назад'], 'content_type': 'text'}},
                           handler_welcome=make_fake_db_record,
                           welcome_msg='Пришлите файл **(один архив или один Jupyter notebook)** весом не более 20 Мб.')


# ----------------------------------------------------------------------------

class HwUploadState(State):
    def welcome_handler(self, bot, message, sqldb: SQLighter):
        username = message.chat.username
        if not message.document.file_name.endswith(config.available_hw_resolutions):
            tmp_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            tmp_markup.add(types.KeyboardButton('Меню'))
            bot.send_message(message.chat.id, "🚫 {}, очень жаль но файлик не сдается в нашу систему...\n"
                                              "Возможны следующие расширения файлов: {}.\n"
                                              "Напоминаю, что дз сдается в виде одного файла архива или одного Jupyter ноутбука."
                             .format(username.title(), str(config.available_hw_resolutions)), reply_markup=tmp_markup)
        else:
            sqldb.upd_homework(user_id=username, file_id=message.document.file_id)
            bot.send_message(message.chat.id,
                             'Уважаемый *{}*, ваш файлик был заботливо сохранен 🐾\n'
                             .format(username.title()),
                             reply_markup=self.reply_markup, parse_mode='Markdown')

    def out_handler(self, bot, message, sqldb: SQLighter):
        for state_name, attribs in self.triggers_out.items():
            if message.content_type == 'document':
                return self.welcome_handler(bot, message, sqldb)

            elif (message.content_type == 'text') and (message.text in attribs['phrases']):
                return state_name
        return self.default_out_handler(bot, message)


pass_hw_upload = HwUploadState(name='PASS_HW_UPLOAD',
                               triggers_out={
                                   'PASS_HW_NUM_SELECT': {'phrases': ['Сдать еще одно дз'], 'content_type': 'text'},
                                   'MAIN_MENU': {'phrases': ['Меню'], 'content_type': 'text'}})


# ----------------------------------------------------------------------------

def show_marks_table(bot, message, sqldb):
    num_checked = sqldb.get_num_checked(message.chat.username)
    if len(num_checked) == 0:
        bot.send_message(message.chat.id, 'Уважаемый *{}*, '
                                          'вам нужно проверить как минимум 3 работы'
                                          ' из каждого сданного вами задания, '
                                          'чтобы узнать свою оценку по данному заданию. '
                                          'На текущий момент вы не проверили ни одно задание :(.'.format(
            message.chat.username.title()),
                         parse_mode='Markdown')
    else:
        may_be_shown = []
        for num, count in num_checked:
            if count < 3:
                bot.send_message(message.chat.id, '👻 Для того чтобы узнать оценку по заданию {}'
                                                  ' вам нужно проверить еще вот столько [{}]'
                                                  ' заданий этого семинара.'.format(num, 3 - count))
            else:
                may_be_shown.append(num)

        if len(may_be_shown) == 0:
            return

        marks = sqldb.get_marks(message.chat.username)
        if len(marks) < 1:
            bot.send_message(message.chat.id, 'Уважаемый *{}*, '
                                              'ваши работы еще не были проверены ни одним разумным существом.\n'
                                              'Остается надеяться и верить в лучшее 🐸'.format(
                message.chat.username.title()),
                             parse_mode='Markdown')
        else:
            count_what_show = 0
            ans = '_Ваши оценки следующие_\n'
            for hw_num, date, mark in marks:
                if hw_num in may_be_shown:
                    count_what_show += 1
                    ans += '🐛 Для работы *' + hw_num + '*, загруженной *' + date + '* оценка: *' + str(
                        round(mark, 2)) + '*\n'
            if count_what_show > 0:
                bot.send_message(message.chat.id, ans, parse_mode='Markdown')
                bot.send_message(message.chat.id, 'Если какой-то работы нет в списке, значит ее еще не проверяли.')
            else:
                bot.send_message(message.chat.id, 'Уважаемый *{}*, '
                                                  'ваши работы по проверенным вами заданиям еще не были проверены'
                                                  ' ни одним разумным существом.\n'
                                                  'Остается надеяться и верить в лучшее 🐸 '
                                                  '(_или написать оргам и заставить их проверить_)'.format(
                    message.chat.username.title()),
                                 parse_mode='Markdown')


get_mark = State(name='GET_MARK',
                 triggers_out={'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'}},
                 handler_welcome=show_marks_table,
                 welcome_msg='Такие дела)')


# ----------------------------------------------------------------------------
def get_marks_table_quiz(bot, message, sqldb):
    bot.send_message(text="Пока никто не проверил ваши квизы. Возвращайтесь позже.",
                     chat_id=message.chat.id)
    # table = sqldb.get_marks_quiz(user_id=message.chat.username)

get_quiz_mark = State(name='GET_QUIZ_MARK',
                      triggers_out={'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'}},
                      handler_welcome=get_marks_table_quiz,
                      welcome_msg='Такие дела..')

# ----------------------------------------------------------------------------

welcome_check_hw = 'Выберите номер задания для проверки' if len(config.hw_possible_to_check) > 0 \
    else 'Нет доступных для проверки заданий. Выпейте чаю, отдохните.'
check_hw_num_selection = State(name='CHECK_HW_NUM_SELECT',
                               triggers_out={'CHECK_HW_SEND': {'phrases': config.hw_possible_to_check,
                                                               'content_type': 'text'},
                                             'MAIN_MENU': {'phrases': ['Назад'], 'content_type': 'text'}},
                               welcome_msg=welcome_check_hw,
                               row_width=2)


# ----------------------------------------------------------------------------

def choose_file_and_send(bot, message, sqldb):
    # TODO: do smth to fix work with empty hw set;
    # TODO: OH MY GOD! people should check only work that they have done!!!!

    file_ids = sqldb.get_file_ids(hw_num=message.text, number_of_files=3, user_id=message.chat.username)
    if len(file_ids) > 0:
        chosen_file = random.choice(file_ids)[0]
        sqldb.write_check_hw_ids(message.chat.username, chosen_file)
        bot.send_document(message.chat.id, chosen_file)
    else:
        print("ERROR! empty sequence")
        pass


check_hw_send = State(name='CHECK_HW_SEND',
                      triggers_out={'CHECK_HW_SAVE_MARK': {'phrases': config.marks,
                                                           'content_type': 'text'}},
                      handler_welcome=choose_file_and_send,
                      row_width=3,
                      welcome_msg="Пожалуйста, оцените работу.")


# ----------------------------------------------------------------------------

def save_mark(bot, message, sqldb):
    sqldb.save_mark(message.chat.username, message.text)


check_hw_save_mark = State(name='CHECK_HW_SAVE_MARK',
                           triggers_out={'CHECK_HW_NUM_SELECT': {'phrases': ['Проверить еще одну работу'],
                                                                 'content_type': 'text'},
                                         'MAIN_MENU': {'phrases': ['Меню'],
                                                       'content_type': 'text'}},
                           welcome_msg='Спасибо за проверенную работу:)',
                           handler_welcome=save_mark)

# ----------------------------------------------------------------------------

admin_menu = State(name='ADMIN_MENU',
                   triggers_out={
                       'KNOW_NEW_QUESTIONS': {'phrases': ['Узнать вопросы к семинару'], 'content_type': 'text'},
                       'SEE_HW_STAT': {'phrases': ['Узнать статистику сдачи домашек'], 'content_type': 'text'},
                       'MAIN_MENU': {'phrases': ['Главное меню'], 'content_type': 'text'}},
                   welcome_msg='Добро пожаловать, о Великий Одмен!')


# ----------------------------------------------------------------------------

def get_questions(bot, message, sqldb):
    questions = sqldb.get_questions_last_week()
    if len(questions) > 0:
        res = '*Questions for the last week*\n'
        for user_id, question, date in questions:
            res += '👽 User: *' + user_id + '* asked at *' + date + '*:\n' + question + '\n\n'
        bot.send_message(message.chat.id, res, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, '_Нет ничего новенького за последние 7 дней, к сожалению_:(',
                         parse_mode='Markdown')


know_new_questions = State(name='KNOW_NEW_QUESTIONS',
                           triggers_out={'ADMIN_MENU': {'phrases': ['Назад в админку'], 'content_type': 'text'}},
                           handler_welcome=get_questions,
                           welcome_msg='Это все 👽')


# ----------------------------------------------------------------------------

def get_hw_stat(bot, message, sqldb):
    hw_stat = sqldb.get_checked_works_stat()
    if len(hw_stat) == 0:
        bot.send_message(message.chat.id, "Нет проверенных домашек совсем:( Грусть печаль.")
    else:
        ans = '_Количество проверенных работ на каждое задание_\n'
        for sem, count in hw_stat:
            ans += sem + '\t' + str(count) + '\n'
        bot.send_message(message.chat.id, ans, parse_mode='Markdown')


see_hw_stat = State(name='SEE_HW_STAT',
                    triggers_out={'ADMIN_MENU': {'phrases': ['Назад в админку'], 'content_type': 'text'}},
                    handler_welcome=get_hw_stat,
                    welcome_msg='Это все что есть проверенного.\nЕсли какого номера тут нет, значит его не проверили.')

# ----------------------------------------------------------------------------
