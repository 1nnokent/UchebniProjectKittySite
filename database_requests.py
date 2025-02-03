import random

from flask import Flask, render_template, request
import sqlite3 as sq
from config import database
from datetime import datetime

connect = sq.connect(database, check_same_thread=False)
cursor = connect.cursor()

def sql_execute(sql_request):
    ret = cursor.execute(sql_request)
    return ret

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
    dict['number_of_attempts'] = {}
    dict['number_of_right_attempts'] = {}
    dict['ratio'] = {}
    for task in range(1, 28):
        dict['number_of_attempts'][task] = random.randint(1, 25)
        dict['number_of_right_attempts'][task] = random.randint(1, dict['number_of_attempts'][task])
        dict['ratio'][task] = dict['number_of_right_attempts'][task] / dict['number_of_attempts'][task]
    if tuple_info[0][13] != -1:
        dict['photo_directory'] = '/img/profile-pictures/profile_' + str(tuple_info[0][13]) + '_avatar.jpg'
    else:
        dict['photo_directory'] = '/img/profile-pictures/profile_default_avatar.jpg'

    return dict

def insert_problem(problem_type, problem_source, problem_statement, problem_answer, problem_difficulty):
    amount = sql_execute("SELECT COUNT (*) FROM problems").fetchall()[0][0]
    pictures = request.files.getlist('files')
    for elem in pictures:
        picture_id = sql_execute("SELECT count(*) FROM problem_picture").fetchall()[0][0]
        path = "static/img/problem-pictures/problem_" + str(picture_id) + ".jpg"
        elem.seek(0)
        elem.save(path)
        sql_execute(f"""
            INSERT 
                INTO problem_picture
            VALUES
                ({amount}, {picture_id}) 
        """)
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
    VALUES ({amount}, {problem_type}, "{problem_source}", "{text}", "{problem_answer}", {problem_difficulty})
    """

    print(sql_req)
    sql_execute(sql_req) #|safe
    connect.commit()

def insert_problem_file(problem_type, problem_class, problem_source, filename, problem_answer, problem_difficulty):
    file = open(filename, "r", encoding="UTF-8")
    file_text = file.read()
    insert_problem(problem_type, problem_source, problem_class, file_text, problem_answer, problem_difficulty)

def insert_user(info):
    print(info)
    current_id = int(sql_execute("""
            SELECT COUNT(*) FROM users
            """).fetchall()[0][0])
    does_exist = len(sql_execute(f"""SELECT * FROM users WHERE login = "{info['login']}" """).fetchall())

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

        role_id = sql_execute(f"""SELECT role_id FROM roles WHERE role_name = '{info['role']}' """).fetchall()[0][0]
        school_id = sql_execute(f"""SELECT school_id FROM schools WHERE school_name = '{info['school']}' """).fetchall()[0][0]
        city_id = sql_execute(f"""SELECT city_id FROM cities WHERE city_name = '{info['city']}' """).fetchall()[0][0]
        print(role_id, school_id, city_id)
        registration_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        sql_req = f"""
                            INSERT INTO users 
                            VALUES ({current_id}, {role_id}, "{registration_time}", "{info['first_name']}", "{info['second_name']}", "{info['third_name']}", "{info['login']}", 
                            "{info['password']}", "{info['email']}", "{info['url']}", "{info['tel']}", {info['love_range']}, 
                            "{info['birth_date']}", {school_id}, {city_id}, "{info['class']}", {photo_id})
                            """
        sql_execute(sql_req)
        connect.commit()
        return 0

def get_password_with_login(login):
    sql_req = f"""
    SELECT password FROM users
    WHERE users.login = "{login}"
    """
    return sql_execute(sql_req).fetchall()

def get_user_id_with_login(login):
    sql_req = f"""
    SELECT user_id FROM users
    WHERE users.login = "{login}"
    """
    return sql_execute(sql_req).fetchall()[0][0]

def get_user_info_with_user_id(id):
    sql_req = f"""
        SELECT * from users
        WHERE user_id = "{id}"
        """
    return sql_execute(sql_req).fetchall()

def variant_page_default_kwargs(variant_id):
    sql_req = f"""SELECT * FROM
                      problems INNER JOIN variant_problem
                      ON variant_problem.problem_id = problems.problem_id
                      WHERE variant_problem.variant_id = {variant_id}"""
    problems = sql_execute(sql_req).fetchall()
    answers_default = ((-1, -2)) * len(problems)
    kwargs = dict()
    kwargs['problems'] = problems
    kwargs['answers'] = answers_default
    kwargs['show_answers'] = False
    kwargs['amount_right'] = -1
    return kwargs

def variant_page_feedback_kwargs(variant_id):
    sql_req = f"""SELECT * FROM
                      problems INNER JOIN variant_problem
                      ON variant_problem.problem_id = problems.problem_id
                      WHERE variant_problem.variant_id = {variant_id}"""
    problems = sql_execute(sql_req).fetchall()
    kwargs = dict()
    given_answers = []
    tmp = request.form.to_dict()

    if not (tmp.__contains__('show_answers')):
        tmp['show_answers'] = False

    for key in tmp:
        given_answers.append(tmp[key])

    answers = []
    for i in range(len(problems)):
        if given_answers[i] == '':
            answers.append((-1, -1))
        else:
            answers.append((given_answers[i], int(given_answers[i] == sql_execute(f"""SELECT problem_answer FROM problems 
                WHERE problem_id = {problems[i][0]}""").fetchall()[0][0])))
    answers = tuple(answers)
    kwargs['problems'] = problems
    kwargs['answers'] = answers
    kwargs['show_answers'] = tmp['show_answers']
    kwargs['amount_right'] = 0
    for elem in answers:
        if elem[1] == 1:
            kwargs['amount_right'] += 1
    return kwargs

def insert_variant_answers(answers, variant_id, user_id, assignment_id):
    completion_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
    sql_req_1 = f"""
    INSERT INTO user_variant
    VALUES ({user_id}, {variant_id}, "{completion_time}", {assignment_id})
    """
    problems = sql_execute(f"""SELECT problem_id FROM variant_problem WHERE variant_id = {variant_id}""").fetchall()
    print(answers)
    print(problems)
    for problem in problems:
        sql_req_2 = f"""
            INSERT INTO user_problem 
            VALUES ({user_id}, {problem[0]}, "{answers[str(problem[0])]}", "{completion_time}", {variant_id}, {assignment_id},
                    {(answers[str(problem[0])] == sql_execute(f'''SELECT problem_answer FROM problems 
                    WHERE problem_id = { problem[0] }''').fetchall()[0][0])})
            """
        print(sql_req_2)
        sql_execute(sql_req_2)

    sql_execute(sql_req_1)
    connect.commit()

def get_discussions():
    sql_req = f"""
        SELECT * FROM forum_discussions
    """
    return sql_execute(sql_req).fetchall()

def get_topic_name(topic_id):
    sql_req = f"""
        SELECT discussion_name FROM forum_discussions WHERE discussion_id = { topic_id }
    """
    return sql_execute(sql_req).fetchall()[0][0]

def get_topic_messages(topic_id):
    sql_req = f"""
        SELECT 
                users.first_name, 
                users.second_name, 
                forum_messages.message_text,
                forum_messages.message_send_time
            FROM 
                users 
            INNER JOIN 
                forum_messages ON users.user_id = forum_messages.message_author_id 
            INNER JOIN 
                forum_discussion_message ON forum_messages.message_id = forum_discussion_message.message_id 
            WHERE 
                forum_discussion_message.discussion_id = { topic_id }
            ORDER BY 
                forum_messages.message_send_time ASC;
    """
    return sql_execute(sql_req).fetchall()

def insert_new_topic(info):
    message_id = sql_execute("SELECT count(*) FROM forum_messages").fetchall()[0][0]
    discussion_id = sql_execute("SELECT count(*) FROM forum_discussions").fetchall()[0][0]
    author_id = 0
    messages_count = 1
    message_name = info['topicTitle']
    message_text = info['topicDescription']
    message_send_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
    sql_req1 = f"""
        INSERT INTO forum_discussions 
        VALUES ({discussion_id}, "{message_name}", {author_id}, {messages_count}, "{message_send_time}")
    """
    sql_req2 = f"""
        INSERT INTO forum_discussion_message
        VALUES ({discussion_id}, {message_id})
    """
    sql_req3 = f"""
        INSERT INTO forum_messages
        VALUES ({message_id}, "{message_name}", "{message_text}", "{message_send_time}", {author_id})
    """
    sql_execute(sql_req1)
    sql_execute(sql_req2)
    sql_execute(sql_req3)
    connect.commit()
    return discussion_id

def insert_topic_message(topic_id, info):
    message_text = info['reply_text']
    message_id = sql_execute("SELECT count(*) FROM forum_messages").fetchall()[0][0]
    send_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
    author_id = 0
    sql_req1 = f"""
        INSERT INTO
                forum_messages
            VALUES
                ({message_id}, NULL, "{message_text}", "{send_time}", {author_id}) 
    """
    sql_req2 = f"""
        INSERT INTO
                forum_discussion_message
            VALUES
                ({topic_id}, {message_id})
    """
    cur_num = sql_execute(f"""SELECT messages_count FROM forum_discussions WHERE discussion_id = {topic_id}""").fetchall()[0][0]
    sql_req3 = f"""
        UPDATE
            forum_discussions
        SET
            messages_count = {cur_num + 1}
        WHERE
            discussion_id = {topic_id}
    """
    sql_execute(sql_req1)
    sql_execute(sql_req2)
    sql_execute(sql_req3)
    connect.commit()

def get_learning_materials():
    sql_req = f"""SELECT * FROM learning_materials"""
    return sql_execute(sql_req).fetchall()

def get_learning_material(material_id):
    sql_req = f"""SELECT * FROM learning_materials WHERE material_id = {material_id}"""
    return sql_execute(sql_req).fetchall()[0]

def get_courses():
    sql_req = f"""SELECT * FROM courses"""
    return sql_execute(sql_req).fetchall()

def get_course_materials(course_id):
    sql_req = f"""
            SELECT
                learning_materials.material_id, material_type, material_name, material_description, material_statement, material_ege_type
            FROM
                course_material INNER JOIN learning_materials
            ON
                course_material.material_id = learning_materials.material_id
            WHERE
                course_material.course_id = {course_id}
    """
    return sql_execute(sql_req).fetchall()

if __name__ == "__main__":
    print("         ТИП   КЛАСС   ОТВЕТ   СЛОЖОСТЬ", "ВВЕДИТЕ: ", sep='\n', end="")
    problem_type, problem_class, problem_answer, problem_difficulty = map(int, input().split())
    insert_problem_file(problem_type, problem_class, "costil.txt", problem_answer, problem_difficulty)
