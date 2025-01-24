from flask import Flask, render_template, request
import sqlite3 as sq
from config import database
from datetime import datetime

connect = sq.connect(database, check_same_thread=False)
cursor = connect.cursor()

if __name__ == "__main__":
    app = Flask(__name__)
    connect = sq.connect(database, check_same_thread=False)
    cursor = connect.cursor()

def user_select_to_dict(tuple_info):
    dict = {}
    dict['user_id'] = tuple_info[0][0]
    dict['role_id'] = tuple_info[0][1]
    dict['registration_time'] = tuple_info[0][2]
    dict['first_name'] = tuple_info[0][3]
    dict['second_name'] = tuple_info[0][4]
    dict['third_name'] = tuple_info[0][5]
    dict['login'] = tuple_info[0][6]
    dict['password'] = tuple_info[0][7]
    dict['email'] = tuple_info[0][8]
    dict['birth_date'] = tuple_info[0][9]
    dict['school_id'] = tuple_info[0][10]
    dict['city_id'] = tuple_info[0][11]
    dict['class'] = tuple_info[0][12]
    if tuple_info[0][13] != -1:
        dict['photo_directory'] = '/img/profile-pictures/profile_' + str(tuple_info[0][13]) + '_avatar.jpg'
    else:
        dict['photo_directory'] = '/img/profile-pictures/profile_default_avatar.jpg'

    return dict

def insert_problem(problem_type, problem_class, problem_source, problem_statement, problem_answer, problem_difficulty):
    amount = cursor.execute("SELECT COUNT (*) FROM problems").fetchall()[0][0]
    text = ""
    prev = 0
    last = 0
    i = 0
    while i < len(problem_statement):
        if problem_statement[i] == '\n':
            last = i
            while problem_statement[i] == '\n':
                i += 1
            text += problem_statement[prev:last]
            text += '<br>'
            prev = i
        i += 1

    text += problem_statement[prev:len(problem_statement)]

    sql_req = f"""
    INSERT INTO problems
    VALUES ({amount}, {problem_type}, {problem_class}, "{problem_source}", "{text}", "{problem_answer}", {problem_difficulty})
    """

    print(sql_req)
    cursor.execute(sql_req) #|safe
    connect.commit()

def insert_problem_file(problem_type, problem_class, problem_source, filename, problem_answer, problem_difficulty):
    file = open(filename, "r", encoding="UTF-8")
    file_text = file.read()
    insert_problem(problem_type, problem_source, problem_class, file_text, problem_answer, problem_difficulty)

def insert_user(info):
    print(info)
    current_id = int(cursor.execute("""
            SELECT COUNT(*) FROM users
            """).fetchall()[0][0])
    does_exist = len(cursor.execute(f"""SELECT * FROM users WHERE login = "{info['login']}" """).fetchall())

    if does_exist:
        return 1
    else:
        photo = request.files['file']
        has_photo = not (request.files['file'].filename == '')
        photo_id = -1
        if has_photo:
            photo_id = current_id
            path = "static/img/profile-pictures/profile_" + str(photo_id) + "_avatar.jpg"
            photo.save(path)

        role_id = cursor.execute(f"""SELECT role_id FROM roles WHERE role_name = '{info['role']}' """).fetchall()[0][0]
        school_id = cursor.execute(f"""SELECT school_id FROM schools WHERE school_name = '{info['school']}' """).fetchall()[0][0]
        city_id = cursor.execute(f"""SELECT city_id FROM cities WHERE city_name = '{info['city']}' """).fetchall()[0][0]
        print(role_id, school_id, city_id)
        registration_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        sql_req = f"""
                            INSERT INTO users 
                            VALUES ({current_id}, {role_id}, "{registration_time}", "{info['first_name']}", "{info['second_name']}", "{info['third_name']}", "{info['login']}", 
                            "{info['password']}", "{info['email']}", "{info['url']}", "{info['tel']}", {info['love_range']}, 
                            "{info['birth_date']}", {school_id}, {city_id}, "{info['class']}", {photo_id})
                            """
        cursor.execute(sql_req)
        connect.commit()

        return 0

def insert_answers_to_variant_from_user(answers, variant_id, user_id, assignment_id):
    completion_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
    sql_req_1 = f"""
    INSERT INTO user_variant
    VALUES ({user_id}, {variant_id}, "{completion_time}", {assignment_id})
    """
    problems = sql_execute(f"""SELECT problem_id FROM variant_problem WHERE variant_id = {variant_id}""").fetchall()
    print(answers)
    print(problems)
    for i in range(len(problems)):
        sql_req_2 = f"""
            INSERT INTO user_problem 
            VALUES ({user_id}, {problems[i][0]}, "{answers[str(problems[i][0])]}", "{completion_time}", {variant_id}, {assignment_id},
                    {(answers[str(problems[i][0])] == sql_execute(f"""SELECT problem_answer FROM problems 
                    WHERE problem_id = { problems[i][0] }""").fetchall()[0][0])})
            """
        print(sql_req_2)
        cursor.execute(sql_req_2)

    cursor.execute(sql_req_1)
    connect.commit()


def get_password_with_login(login):
    sql_req = f"""
    SELECT password FROM users
    WHERE users.login = "{login}"
    """
    return cursor.execute(sql_req).fetchall()

def get_user_id_with_login(login):
    sql_req = f"""
    SELECT user_id FROM users
    WHERE users.login = "{login}"
    """
    return cursor.execute(sql_req).fetchall()[0][0]

def get_user_info_with_user_id(id):
    sql_req = f"""
        SELECT * from users
        WHERE user_id = "{id}"
        """
    return cursor.execute(sql_req).fetchall()

def sql_execute(sql_request):
    return cursor.execute(sql_request)

if __name__ == "__main__":
    print("         ТИП   КЛАСС   ОТВЕТ   СЛОЖОСТЬ", "ВВЕДИТЕ: ", sep='\n', end="")
    problem_type, problem_class, problem_answer, problem_difficulty = map(int, input().split())
    insert_problem_file(problem_type, problem_class, "costil.txt", problem_answer, problem_difficulty)
