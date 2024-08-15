import sqlite3
import requests
from bs4 import BeautifulSoup
import lxml
import re
import translators as ts
import config
import respository


USER_AGENT = config.user_agent


def add_question_info(db, table, question_text, category, description):
    cur = db.cursor()
    cur.execute(f"""
                INSERT INTO {table} (text, category, description) 
                VALUES (?, ?, ?)
            """, (question_text, category, description))
    db.commit()


def get_question_id(db, table):
    cur = db.cursor()
    cur.execute(f"SELECT MAX(question_id) FROM {table}")
    question_id = cur.fetchone()
    return question_id[0]


def add_answers(db, table, question_id, answers, index_right_answer):
    cur = db.cursor()
    for i, answer in enumerate(answers):
        is_right = 0
        if i == index_right_answer:
            is_right = 1
        cur.execute(f"""
                        INSERT INTO {table} (question_id, text, is_right) 
                        VALUES (?, ?, ?)
                    """, (question_id, answer, is_right))
    db.commit()


def parse(db, url, category, pages):
    user_agent = {
        'User-Agent': USER_AGENT}
    cookies = {
        'exam-settings': '%7B%22category%22%3A1%2C%22locale%22%3A%22ru%22%2C%22skin%22%3A%22dark%22%2C%22user%22%3A0%2C%22created%22%3A1716899742%2C%22questions%22%3A30%2C%22challenge%22%3Atrue%2C%22all_questions%22%3Afalse%2C%22topics%22%3A%5B%221%22%2C%222%22%2C%223%22%2C%224%22%2C%225%22%2C%226%22%2C%227%22%2C%228%22%2C%229%22%2C%2210%22%2C%2211%22%2C%2212%22%2C%2213%22%2C%2214%22%2C%2215%22%2C%2216%22%2C%2217%22%2C%2218%22%2C%2219%22%2C%2220%22%2C%2221%22%2C%2222%22%2C%2223%22%2C%2224%22%2C%2225%22%2C%2226%22%2C%2227%22%2C%2228%22%2C%2229%22%2C%2230%22%2C%2231%22%2C%2232%22%5D%2C%22autoShowCorrect%22%3Atrue%2C%22autoNextStep%22%3Afalse%7D'
    }
    for i in range(1, pages):
        response = requests.get(f'{url + str(i)}', headers=user_agent, cookies=cookies)
        if response.status_code == 200:
            print(f'Successfull connect to page {i}')
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')
            items = soup.find_all('div', class_='item')
            for item in items:
                # get all info about question and add it to table question
                question_text = item.find('div', class_='t-question').find('p').find('span').text
                description = item.find('div', class_='desc-box-inner').find('p', class_=lambda x: x != 'sorry').text
                description = ts.translate_text(ts.translate_text(description, translator='yandex'),
                                                translator='yandex', to_language='ru')

                add_question_info(db, 'questions', question_text, category, description)

                # get all info about answers and add it to table answers
                question_id = get_question_id(db, 'questions')
                t_cover_divs = item.find_all('div', class_=re.compile(r't-cover'))
                answers = []
                for t_cover_div in t_cover_divs:
                    text_wrap_spans = t_cover_div.find_all('span', class_='text-wrap')
                    for span in text_wrap_spans:
                        answers.append(span.text)
                index_right_answer = int(
                    item.find('p', attrs={'data-is-correct-list': 'true'}).find('span', class_='t-a-num').text) - 1
                add_answers(db, 'answers', question_id, answers, index_right_answer)
                # get image if exists
                if item.find('img'):
                    img_link = item.find('img')['src']
                    img_response = requests.get(img_link, stream=True)
                    if img_response.status_code == 200:
                        img_path = f'images/{question_id}.jpg'
                        with open(img_path, 'wb') as img_file:
                            for chunk in img_response.iter_content(1024):
                                img_file.write(chunk)
                        print(f'Image saved as {img_path}')
                    else:
                        print('Failed to download image')

            print(f'Success parsing of page {i}')
        else:
            print(f'Request failed with status code: {response.status_code}')


db = respository.connection()
parse(db, 'https://teoria.on.ge/tickets/1?page=', 'A', 45)
parse(db, 'https://teoria.on.ge/tickets/2?page=', 'B', 56)


