import telebot
from telebot import types
import sqlite3
import random
import os
import config

API = config.api
bot = telebot.TeleBot(API)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"""Привет, @{message.from_user.username}!
Я создан, чтобы ты с успехом сдал теорию ПДД в Грузии.""")
    add_to_users(int(message.from_user.id), message.from_user.username)
    send_reply_menu(message.chat.id)


@bot.message_handler(content_types=['text'])
def text_handler(message):
    tg_user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    btn_info = ['📚 Начать экзамен', '📋 Начать марафон', '📝 Работа над ошибками',
                '📊 Статистика', '❌ Прервать тренировку']
    if text not in btn_info:
        bot.send_message(message.chat.id, f'Для работы с ботом используйте, пожалуйста, меню.')
        add_to_users(int(message.from_user.id), message.from_user.username)
        send_reply_menu(chat_id)
    else:
        if text == '📚 Начать экзамен':
            set_round_info(tg_user_id, 'exam')
            choose_category(message)
        elif text == '📋 Начать марафон':
            set_round_info(tg_user_id, 'marathon')
            choose_category(message)
        elif text == '📝 Работа над ошибками':
            if check_data_from_mistake_questions_by_tg_user_id(tg_user_id):
                set_round_info(tg_user_id, 'work on mistakes')
                stat_id = fetch_current_round_id_from_users_by_tg_user_id(tg_user_id)
                list_of_question_ids = get_list_of_mistake_question_ids(tg_user_id)
                print(list_of_question_ids)
                set_list_of_question_id_to_stats_by_stat_id(stat_id, list_of_question_ids)
                send_reply_end_game(chat_id)
                round_step(message, tg_user_id)
            else:
                bot.send_message(chat_id, f'У вас нет вопросов, требующих исправления!')
        elif text == '📊 Статистика':
            send_stats(chat_id, tg_user_id)
        elif text == '❌ Прервать тренировку':
            stat_id = fetch_current_round_id_from_users_by_tg_user_id(tg_user_id)
            if stat_id is not None:
                end_of_the_game(chat_id, stat_id)
                update_current_round_id_after_end_of_the_game_in_users_by_tg_user_id(tg_user_id)
                send_reply_menu(chat_id)
            else:
                bot.send_message(message.chat.id, f'У вас нет активных сеансов тренировки.')


def send_reply_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton('📚 Начать экзамен')
    btn2 = types.KeyboardButton('📋 Начать марафон')
    btn3 = types.KeyboardButton('📝 Работа над ошибками')
    btn4 = types.KeyboardButton('📊 Статистика')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(chat_id, 'Доступные действия:', reply_markup=markup)


def send_reply_end_game(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton('❌ Прервать тренировку')
    markup.add(btn1)
    bot.send_message(chat_id, 'Вы можете прервать тренировку, нажав на кнопку', reply_markup=markup)


def send_stats(chat_id, tg_user_id):
    data = fetch_data_from_stats_by_tg_user_id(tg_user_id)
    bot.send_message(chat_id, f"""Ваши результаты:
✅ Показатель верных ответов: <b>{data[0]}%</b>
❌ Показатель ошибок: <b>{data[1]}%</b>""", parse_mode='HTML')


def send_question(chat_id, question_info, question_id):
    if image_exists(question_id):
        with open(f'images/{question_id}.jpg', 'rb') as photo:
            bot.send_photo(chat_id, photo)
    bot.send_message(chat_id, question_info[0], parse_mode='HTML')  # question_text
    bot.send_message(chat_id, question_info[1], reply_markup=question_info[2])  # message_with_answers, markup


def end_of_the_game(chat_id, stat_id):
    correct_cnt, mistakes = fetch_correct_and_mistake_from_stats_by_stat_id(stat_id)
    bot.send_message(chat_id, f"""Тренировка завершена! Ваш результат:
✅ Верные ответы - <b>{correct_cnt}</b>
❌ Ошибки - <b>{mistakes}</b>""", parse_mode='HTML')


def add_to_users(tg_user_id, username):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM users WHERE tg_user_id = ?", (tg_user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute(f"""
                    INSERT INTO users (tg_user_id, username) 
                    VALUES (?, ?)
                """, (tg_user_id, username,))
        db.commit()
    db.close()


def add_current_question_to_mistakes_by_tg_user_id_and_question_id(tg_user_id, question_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"""
            INSERT INTO mistake_questions (tg_user_id, question_id) 
            VALUES (?, ?)
        """, (tg_user_id, question_id))
    db.commit()
    db.close()


def choose_category(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(f'Категория А', callback_data='A')
    btn2 = types.InlineKeyboardButton(f'Категория Б', callback_data='B')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f'Выбери категорию прав:', reply_markup=markup)


def round_step(message, tg_user_id):
    stat_id = fetch_current_round_id_from_users_by_tg_user_id(tg_user_id)
    list_of_question_ids = fetch_list_of_question_ids_from_stats_by_stat_id(stat_id)
    if len(list_of_question_ids) == 0:
        end_of_the_game(message.chat.id, stat_id)
        update_current_round_id_after_end_of_the_game_in_users_by_tg_user_id(tg_user_id)
        send_reply_menu(message.chat.id)
    else:
        question_id = get_question_id_from_list_of_question_ids(list_of_question_ids)
        print(question_id)
        question_info = construct_question_info(stat_id, question_id)
        send_question(message.chat.id, question_info, question_id)


def set_new_round_to_stats(tg_user_id, round_type):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"""
        INSERT INTO stats (tg_user_id, round_type, round_num, correct_cnt, mistakes_cnt) 
        VALUES (?, ?, ?, ?, ?)
    """, (tg_user_id, round_type, 1, 0, 0))
    db.commit()
    db.close()


def set_current_round_id_to_users_by_tg_user_id(tg_user_id, current_round_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE users SET current_round_id = ? WHERE tg_user_id = ?',
                (current_round_id, tg_user_id))
    db.commit()
    db.close()


def set_category_to_stats_by_stat_id(stat_id, category):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE stats SET category = ? WHERE stat_id = ?',
                (category, stat_id))
    db.commit()
    db.close()


def set_list_of_question_id_to_stats_by_stat_id(stat_id, list_of_question_ids):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE stats SET list_of_question_ids = ? WHERE stat_id = ?',
                (list_of_question_ids, stat_id))
    db.commit()
    db.close()


def fetch_stat_id_by_tg_user_id(tg_user_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM stats WHERE tg_user_id = ? ORDER BY stat_id DESC",
                (tg_user_id,))
    data = cur.fetchone()
    db.close()

    return data[0]


def fetch_current_round_id_from_users_by_tg_user_id(tg_user_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM users WHERE tg_user_id = ?",
                (tg_user_id,))
    data = cur.fetchone()
    db.close()
    if data:
        return data[3]
    return None


def fetch_list_of_question_ids_from_stats_by_stat_id(stat_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM stats WHERE stat_id = ?", (stat_id,))
    data = cur.fetchone()
    db.close()

    return data[7]


def fetch_round_num_from_stats_by_stat_id(stat_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM stats WHERE stat_id = ?", (stat_id,))
    data = cur.fetchone()
    db.close()

    return data[4]


def fetch_text_from_questions_by_question_id(question_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM questions WHERE question_id = ?", (question_id,))
    data = cur.fetchone()
    db.close()

    return data[2]


def fetch_answer_ids_from_answers_by_question_id(question_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM answers WHERE question_id = ?", (question_id,))
    data = cur.fetchall()
    db.close()

    list_of_answer_ids = [row[0] for row in data]
    random.shuffle(list_of_answer_ids)

    return list_of_answer_ids


def fetch_answer_texts_from_answers_by_list_of_answer_ids(list_of_answer_ids):
    text = ''
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    for i, id in enumerate(list_of_answer_ids):
        cur.execute(f"SELECT * FROM answers WHERE answer_id = ?", (id,))
        data = cur.fetchone()
        if i != 0:
            text += '\n'
        text += f'{i + 1} - {data[2]}'
    db.close()

    return text


def fetch_round_type_from_stats_by_stat_id(stat_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM stats WHERE stat_id = ?", (stat_id,))
    data = cur.fetchone()
    db.close()

    return data[2]


def fetch_correct_and_mistake_from_stats_by_stat_id(stat_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM stats WHERE stat_id = ?", (stat_id,))
    data = cur.fetchone()
    db.close()

    return (data[5], data[6])


def fetch_data_from_stats_by_tg_user_id(tg_user_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM stats WHERE tg_user_id = ?", (tg_user_id,))
    data = cur.fetchall()
    if data:
        correct_answers = [row[5] for row in data]
        mistakes = [row[6] for row in data]
        all_actions = sum(correct_answers)
        all_actions += sum(mistakes)
        percentage_correct = round((sum(correct_answers) / all_actions * 100), 2)
        percentage_mistakes = round((sum(mistakes) / all_actions * 100), 2)
        return (percentage_correct, percentage_mistakes)
    else:
        return (0, 0)


def fetch_description_from_questions_by_question_id(question_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM questions WHERE question_id = ?", (question_id,))
    data = cur.fetchone()
    db.close()

    return data[3]


def fetch_right_answer_from_answers_by_question_id(question_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM answers WHERE question_id = ? AND is_right = ?",
                (question_id, 1))
    data = cur.fetchone()
    db.close()

    return data[2]


def check_data_from_mistake_questions_by_tg_user_id(tg_user_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM mistake_questions WHERE tg_user_id = ?", (tg_user_id,))
    data = cur.fetchall()
    if data:
        return True
    else:
        return False


def get_list_of_question_ids(category, round_type):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute("SELECT * FROM questions WHERE category = ?", (category,))
    data = cur.fetchall()
    db.close()

    all_question_ids = [row[0] for row in data]
    question_ids = []
    if round_type == 'exam':
        question_ids = random.sample(all_question_ids, min(30, len(all_question_ids)))
    else:
        random.shuffle(all_question_ids)
        question_ids = all_question_ids

    list_of_question_ids = ','.join(map(str, question_ids))

    return list_of_question_ids


def get_list_of_mistake_question_ids(tg_user_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute("SELECT * FROM mistake_questions WHERE tg_user_id = ?", (tg_user_id,))
    data = cur.fetchall()
    db.close()

    question_ids = [row[2] for row in data]
    random.shuffle(question_ids)

    list_of_question_ids = ','.join(map(str, question_ids))

    return list_of_question_ids


def get_question_id_from_list_of_question_ids(list_of_question_ids):
    pos = list_of_question_ids.find(',')
    if pos != -1:
        question_id = list_of_question_ids[:pos]
        return int(question_id)
    return int(list_of_question_ids)


def construct_buttons_for_answers_by_list_of_answer_ids(list_of_answer_ids):
    buttons = []
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    for i, id in enumerate(list_of_answer_ids):
        cur.execute(f"SELECT * FROM answers WHERE answer_id = ?", (id,))
        data = cur.fetchone()
        is_right = 'false'
        if data[3] == 1:
            is_right = 'true'
        btn = types.InlineKeyboardButton(f'{i + 1}', callback_data=f'{is_right}')
        buttons.append(btn)
    db.close()

    return buttons


def construct_question_info(stat_id, question_id):
    question_num = fetch_round_num_from_stats_by_stat_id(stat_id)
    question_text = f"""<b>Вопрос {str(question_num)}</b>
{fetch_text_from_questions_by_question_id(question_id)}"""
    list_of_answer_ids = fetch_answer_ids_from_answers_by_question_id(question_id)
    message_with_answers = fetch_answer_texts_from_answers_by_list_of_answer_ids(list_of_answer_ids)
    buttons = construct_buttons_for_answers_by_list_of_answer_ids(list_of_answer_ids)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i + 2])

    return (question_text, message_with_answers, markup)


def delete_row_from_mistakes_by_tg_user_id_and_question_id(tg_user_id, mistakes_question_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute("DELETE FROM mistake_questions WHERE tg_user_id = ? AND mistakes_question_id = ?",
                (tg_user_id, mistakes_question_id))
    db.commit()
    db.close()


def remove_current_question_from_list_of_question_ids(list_of_question_ids):
    pos = list_of_question_ids.find(',')
    if pos != -1:
        return list_of_question_ids[pos + 1:]
    else:
        return ''


def update_correct_cnt_from_stats_with_stat_id(stat_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE stats SET correct_cnt = correct_cnt + 1 WHERE stat_id = ?', (stat_id,))
    db.commit()

    db.close()


def update_mistakes_cnt_from_stats_with_stat_id(stat_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE stats SET mistakes_cnt = mistakes_cnt + 1 WHERE stat_id = ?', (stat_id,))
    db.commit()
    db.close()


def update_round_num_from_stats_with_stat_id(stat_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE stats SET round_num = round_num + 1 WHERE stat_id = ?', (stat_id,))
    db.commit()
    db.close()


def update_list_of_question_ids_from_stats_with_stat_id(stat_id, list_of_question_ids):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE stats SET list_of_question_ids = ? WHERE stat_id = ?',
                (list_of_question_ids, stat_id))
    db.commit()
    db.close()


def update_current_round_id_after_end_of_the_game_in_users_by_tg_user_id(tg_user_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute(f'UPDATE users SET current_round_id = NULL WHERE tg_user_id = ?',
                (tg_user_id,))
    db.commit()
    db.close()


def is_current_question_in_mistakes_by_tg_user_id_and_question_id(tg_user_id, question_id):
    db = sqlite3.connect('teoria.db')
    cur = db.cursor()
    cur.execute("SELECT * FROM mistake_questions WHERE tg_user_id = ? AND question_id = ?",
                (tg_user_id, question_id))
    data = cur.fetchone()
    db.close()

    if data is None:
        return False
    else:
        return True


def image_exists(question_id):
    image_path = f'images/{question_id}.jpg'
    return os.path.isfile(image_path)


def set_round_info(tg_user_id, data):
    set_new_round_to_stats(tg_user_id, data)
    stat_id = fetch_stat_id_by_tg_user_id(tg_user_id)
    set_current_round_id_to_users_by_tg_user_id(tg_user_id, stat_id)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    tg_user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

    if data == 'A' or data == 'B':
        category = data
        stat_id = fetch_current_round_id_from_users_by_tg_user_id(tg_user_id)
        set_category_to_stats_by_stat_id(stat_id, category)
        round_type = fetch_round_type_from_stats_by_stat_id(stat_id)
        list_of_question_ids = get_list_of_question_ids(category, round_type)
        set_list_of_question_id_to_stats_by_stat_id(stat_id, list_of_question_ids)
        send_reply_end_game(chat_id)
        round_step(call.message, tg_user_id)

    elif data == 'true' or data == 'false':
        stat_id = fetch_current_round_id_from_users_by_tg_user_id(tg_user_id)
        round_type = fetch_round_type_from_stats_by_stat_id(stat_id)
        list_of_question_ids = fetch_list_of_question_ids_from_stats_by_stat_id(stat_id)
        current_question_id = get_question_id_from_list_of_question_ids(list_of_question_ids)
        if round_type == 'work on mistakes':
            if data == 'true':
                update_correct_cnt_from_stats_with_stat_id(stat_id)
                delete_row_from_mistakes_by_tg_user_id_and_question_id(tg_user_id, current_question_id)
                bot.send_message(chat_id, f'✅ <b>Верно!</b>', parse_mode='HTML')
            else:
                update_mistakes_cnt_from_stats_with_stat_id(stat_id)
                description = fetch_description_from_questions_by_question_id(current_question_id)
                right_answer = fetch_right_answer_from_answers_by_question_id(current_question_id)
                bot.send_message(chat_id, f"""❌ <b>Неверно!</b>

<b>Верный ответ:</b> {right_answer}

<b>Пояснение:</b>
{description}""", parse_mode='HTML')
        else:
            if data == 'true':
                update_correct_cnt_from_stats_with_stat_id(stat_id)
                bot.send_message(chat_id, f'✅ <b>Верно!</b>', parse_mode='HTML')
            else:
                update_mistakes_cnt_from_stats_with_stat_id(stat_id)
                if not is_current_question_in_mistakes_by_tg_user_id_and_question_id(tg_user_id, current_question_id):
                    add_current_question_to_mistakes_by_tg_user_id_and_question_id(tg_user_id, current_question_id)
                description = fetch_description_from_questions_by_question_id(current_question_id)
                right_answer = fetch_right_answer_from_answers_by_question_id(current_question_id)
                bot.send_message(chat_id, f"""❌ <b>Неверно!</b>

<b>Верный ответ:</b> {right_answer}

<b>Пояснение:</b>
{description}""", parse_mode='HTML')

        update_round_num_from_stats_with_stat_id(stat_id)
        list_of_question_ids = remove_current_question_from_list_of_question_ids(list_of_question_ids)
        update_list_of_question_ids_from_stats_with_stat_id(stat_id, list_of_question_ids)

        round_step(call.message, tg_user_id)


bot.polling(none_stop=True)
