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
    dict['user_id'] = tuple_info[0]
    dict['role'] = sql_execute(f"""SELECT role_name FROM roles WHERE role_id = {tuple_info[1]}""").fetchall()[0][0]
    dict['registration_time'] = tuple_info[2]
    dict['first_name'] = tuple_info[3]
    dict['second_name'] = tuple_info[4]
    dict['surname'] = tuple_info[5]
    dict['login'] = tuple_info[6]
    dict['password'] = tuple_info[7]
    dict['email'] = tuple_info[8]
    dict['tel'] = tuple_info[9]
    dict['birth_date'] = tuple_info[10]
    dict['school'] = sql_execute(f"""SELECT school_name FROM schools WHERE school_id = {tuple_info[11]}""").fetchall()[0][0]
    dict['city'] = sql_execute(f"""SELECT city_name FROM cities WHERE city_id = {tuple_info[12]}""").fetchall()[0][0]
    dict['class'] = tuple_info[13]
    dict['number_of_attempts'] = {}
    dict['number_of_right_attempts'] = {}
    dict['ratio'] = {}
    for task in range(1, 28):
        dict['number_of_attempts'][task] = random.randint(1, 25)
        dict['number_of_right_attempts'][task] = random.randint(1, dict['number_of_attempts'][task])
        dict['ratio'][task] = dict['number_of_right_attempts'][task] / dict['number_of_attempts'][task]
    if tuple_info[14] != -1:
        dict['photo_directory'] = '/img/profile-pictures/profile_' + str(tuple_info[14]) + '.jpg'
    else:
        dict['photo_directory'] = '/img/profile-pictures/profile_default_avatar.jpg'

    return dict

def get_problems():
    problems = sql_execute("SELECT * FROM problems").fetchall()
    ret = []
    for elem in problems:
        tmp = []
        for i in elem:
            tmp.append(i)

        pictures = sql_execute(f"""SELECT picture_id FROM problem_picture WHERE problem_id = { elem[0] }""")
        k = []
        for i in pictures:
            k.append(f"""problem_{i[0]}.jpg""")
        tmp.append(k)

        tables = sql_execute(f"""SELECT table_id FROM problem_table WHERE problem_id = { elem[0] }""")
        k = []
        for i in tables:
            k.append(f"""{i[0]}.xlsx""")
        tmp.append(k)

        texts = sql_execute(f"""SELECT text_file_id FROM problem_text_file WHERE problem_id = { elem[0] }""")
        k = []
        for i in texts:
            k.append(f"""{i[0]}.txt""")
        tmp.append(k)

        ret.append(tmp)

    return ret

def insert_problem(problem_type, problem_source, problem_statement, problem_answer, problem_difficulty, problem_id=None):
    if problem_id is None:
        problem_id = sql_execute("SELECT COUNT (*) FROM problems").fetchall()[0][0]
    
    pictures = request.files.getlist('photos')
    for elem in pictures:
        if elem.filename == '':
            continue
        picture_id = sql_execute("SELECT count(*) FROM problem_picture").fetchall()[0][0]
        path = f"""static/img/problem-pictures/problem_{picture_id}.jpg"""
        elem.save(path)
        sql_execute(f"""
            INSERT 
                INTO problem_picture
            VALUES
                ({problem_id}, {picture_id}) 
        """)

    tables = request.files.getlist('tables')
    for elem in tables:
        if elem.filename == '':
            continue
        table_id = sql_execute("SELECT count(*) FROM problem_table").fetchall()[0][0]
        path = f"""static/excel-tables/{table_id}.xlsx"""
        elem.save(path)
        sql_execute(f"""
            INSERT
                INTO problem_table
            VALUES
                ({problem_id}, {table_id})
        """)

    texts = request.files.getlist('texts')
    for elem in texts:
        if elem.filename == '':
            continue
        text_id = sql_execute("SELECT count(*) FROM problem_text_file").fetchall()[0][0]
        path = f"""static/text-files/{text_id}.txt"""
        elem.save(path)
        sql_execute(f"""
            INSERT
                INTO problem_text_file
            VALUES
                ({problem_id}, {text_id})
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
    VALUES ({problem_id}, {problem_type}, "{problem_source}", "{text}", "{problem_answer}", {problem_difficulty})
    """

    sql_execute(sql_req) #|safe
    connect.commit()


def insert_problem_file(problem_type, problem_class, problem_source, filename, problem_answer, problem_difficulty):
    file = open(filename, "r", encoding="UTF-8")
    file_text = file.read()
    insert_problem(problem_type, problem_source, problem_class, file_text, problem_answer, problem_difficulty)

def insert_user(info):
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
            path = "static/img/profile-pictures/profile_" + str(photo_id) + ".jpg"
            photo.save(path)

        role_id = sql_execute(f"""SELECT role_id FROM roles WHERE role_name = '{info['role']}' """).fetchall()[0][0]
        school_id = sql_execute(f"""SELECT school_id FROM schools WHERE school_name = '{info['school']}' """).fetchall()[0][0]
        city_id = sql_execute(f"""SELECT city_id FROM cities WHERE city_name = '{info['city']}' """).fetchall()[0][0]
        registration_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        sql_req = f"""
                            INSERT INTO users 
                            VALUES ({current_id}, {role_id}, "{registration_time}", "{info['first_name']}", 
                            "{info['second_name']}", "{info['surname']}", "{info['login']}", 
                            "{info['password']}", "{info['email']}", "{info['tel']}", 
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
    return sql_execute(sql_req).fetchall()[0]

def get_problems_by_variant(variant_id):
    sql_req = f"""
            SELECT 
                problems.problem_id, problem_type_id, problem_source, problem_statement, problem_answer, problem_difficulty
            FROM
                problems 
            INNER JOIN
                variant_problem
            ON
                problems.problem_id = variant_problem.problem_id
            WHERE
                variant_problem.variant_id = {variant_id}
    """
    return sql_execute(sql_req).fetchall()

def get_learning_materials_by_course(course_id):
    sql_req = f"""
            SELECT 
                learning_materials.material_id, material_type, material_name, material_description, material_statement, material_ege_type
            FROM
                learning_materials
            INNER JOIN
                course_material
            ON
                learning_materials.material_id = course_material.material_id
            WHERE
                course_material.course_id = {course_id}
    """
    return sql_execute(sql_req).fetchall()

def get_variant_by_course(course_id):
    sql_req = f"""
            SELECT 
                course_variant.variant_id
            FROM
                course_variant
            WHERE
                course_variant.course_id = {course_id}
    """
    return sql_execute(sql_req).fetchall()

def variant_page_default_kwargs(variant_id):
    ret = []
    problems = get_problems_by_variant(variant_id)
    for elem in problems:
        tmp = []
        for i in elem:
            tmp.append(i)
        pictures = sql_execute(f"""SELECT picture_id FROM problem_picture WHERE problem_id = {elem[0]}""")
        k = []
        for i in pictures:
            k.append(f"""problem_{i[0]}.jpg""")
        tmp.append(k)

        tables = sql_execute(f"""SELECT table_id FROM problem_table WHERE problem_id = {elem[0]}""")
        k = []
        for i in tables:
            k.append(f"""{i[0]}.xlsx""")
        tmp.append(k)

        texts = sql_execute(f"""SELECT text_file_id FROM problem_text_file WHERE problem_id = {elem[0]}""")
        k = []
        for i in texts:
            k.append(f"""{i[0]}.txt""")
        tmp.append(k)

        ret.append(tmp)

    answers_default = ((-1, -2)) * len(problems)
    display_mode = sql_execute(f"""SELECT display_mode FROM variants WHERE variant_id = {variant_id}""").fetchall()[0][0]
    kwargs = dict()
    kwargs['problems'] = ret
    kwargs['answers'] = answers_default
    kwargs['show_answers'] = False
    kwargs['amount_right'] = -1
    kwargs['display_mode'] = display_mode

    return kwargs

def variant_page_feedback_kwargs(variant_id):
    problems = get_problems_by_variant(variant_id)
    ret = []
    for elem in problems:
        tmp = []
        for i in elem:
            tmp.append(i)
        pictures = sql_execute(f"""SELECT picture_id FROM problem_picture WHERE problem_id = {elem[0]}""")
        k = []
        for i in pictures:
            k.append(f"""problem_{i[0]}.jpg""")
        tmp.append(k)

        tables = sql_execute(f"""SELECT table_id FROM problem_table WHERE problem_id = {elem[0]}""")
        k = []
        for i in tables:
            k.append(f"""{i[0]}.xlsx""")
        tmp.append(k)

        texts = sql_execute(f"""SELECT text_file_id FROM problem_text_file WHERE problem_id = {elem[0]}""")
        k = []
        for i in texts:
            k.append(f"""{i[0]}.txt""")
        tmp.append(k)

        ret.append(tmp)

    kwargs = dict()
    given_answers = []
    tmp = request.form.to_dict()

    if not ('show_answers' in tmp):
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
    display_mode = sql_execute(f"""SELECT display_mode FROM variants WHERE variant_id = {variant_id}""").fetchall()[0][0]

    kwargs['problems'] = ret
    kwargs['answers'] = answers
    kwargs['show_answers'] = tmp['show_answers']
    kwargs['amount_right'] = 0
    kwargs['display_mode'] = display_mode
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
    for problem in problems:
        sql_req_2 = f"""
            INSERT INTO user_problem 
            VALUES ({user_id}, {problem[0]}, "{answers[str(problem[0])]}", "{completion_time}", {variant_id}, {assignment_id},
                    {(answers[str(problem[0])] == sql_execute(f'''SELECT problem_answer FROM problems 
                    WHERE problem_id = { problem[0] }''').fetchall()[0][0])})
            """
        sql_execute(sql_req_2)

    sql_execute(sql_req_1)
    connect.commit()


def change_variant_display_mode(variant_id, mode):
    sql_req = f"""UPDATE variants SET display_mode = {mode} WHERE variant_id = {variant_id}"""
    sql_execute(sql_req)
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
                users.surname, 
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

def get_course_variant(course_id):
    sql_req = f"""
            SELECT
                course_variant.variant_id
            FROM
                course_variant
            WHERE
                course_variant.course_id = {course_id}
    """
    return sql_execute(sql_req).fetchall()

def insert_variant(variant_id, variant_name, variant_description, author_id):
    sql_req = f"""
            INSERT INTO
                variants
            VALUES
                ({variant_id}, "{variant_name}", "{variant_description}", {author_id}, 3)
    """
    sql_execute(sql_req)
    connect.commit()

def insert_course(course_id, course_name, course_description):
    sql_req = f"""
            INSERT INTO
                courses
            VALUES
                ({course_id}, "{course_name}", "{course_description}")
    """
    sql_execute(sql_req)
    connect.commit()

def insert_problem_to_variant(variant_id, problem_id):
    sql_req = f"""
            INSERT INTO
                variant_problem
            VALUES
                ({variant_id}, {problem_id})
    """
    sql_execute(sql_req)
    connect.commit()

def insert_learning_material_to_course(course_id, learning_material_id):
    sql_req = f"""
            INSERT INTO
                course_material
            VALUES
                ({course_id}, {learning_material_id})
    """
    sql_execute(sql_req)
    connect.commit()

def remove_problem_from_variant(variant_id, problem_id):
    sql_req = f"""
            DELETE 
                FROM variant_problem
            WHERE
                variant_id = {variant_id}
            AND
                problem_id = {problem_id}
    """
    sql_execute(sql_req)
    connect.commit()

def remove_learning_material_from_course(course_id, learning_material_id):
    sql_req = f"""
            DELETE 
                FROM course_material
            WHERE
                course_id = {course_id}
            AND
                material_id = {learning_material_id}
    """
    sql_execute(sql_req)
    connect.commit()

def get_groups(user_id):
    group_list = sql_execute(f"""SELECT group_id FROM user_group WHERE user_id = {user_id}""").fetchall()
    group_list_string = "("
    for elem in group_list:
        group_list_string = group_list_string + str(elem[0]) + ', '
    group_list_string = group_list_string[:-2:] + ')'
    groups = sql_execute(f"""SELECT * FROM groups WHERE group_id IN {group_list_string}""").fetchall()
    return groups

def get_group_members(group_id):
    sql_req = f"""
            SELECT
                first_name, second_name, surname, role_name
            FROM
                users
            INNER JOIN
                roles ON users.role_id = roles.role_id
            INNER JOIN
                user_group ON user_group.user_id = users.user_id
            WHERE
                user_group.group_id = {group_id}
    """
    members = sql_execute(sql_req).fetchall()
    return members

def get_group_courses(group_id):
    sql_req = f"""
            SELECT
                *
            FROM
                courses
                INNER JOIN
                group_course ON group_course.course_id = courses.course_id
            WHERE
                group_course.group_id = {group_id}
    """
    courses = sql_execute(sql_req).fetchall()
    return courses

def get_group_assignments(group_id):
    sql_req = f"""
            SELECT
                assignments.assignment_id, variants.variant_id, variants.variant_name, variants.variant_description
            FROM
                    assignment_group
                INNER JOIN
                    assignments
                ON
                    assignment_group.assignment_id = assignments.assignment_id
                INNER JOIN
                    variants
                ON
                    assignments.variant_id = variants.variant_id
                WHERE
                    assignment_group.group_id = {group_id}
    """
    variants = sql_execute(sql_req).fetchall()
    return variants

def change_variant(course_id, variant_id):
    sql_req = f"""
        UPDATE course_variant
        SET variant_id = {variant_id}
        WHERE course_id = {course_id}
    """
    sql_execute(sql_req)
    connect.commit()
    
def encode_group_code(group_id):
    code = ''
    alph = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    leng = 0
    while group_id or leng < 5:
        code += alph[group_id % 26]
        group_id //= 26
        leng += 1
    return code[::-1]

def decode_group_code(encoded_id):
    ret = 0
    alph = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(5):
        ret += alph.find(encoded_id[i]) * 26 ** (4 - i)
    return ret
