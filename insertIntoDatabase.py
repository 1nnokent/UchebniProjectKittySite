from flask import Flask, render_template, request
import sqlite3 as sq

app = Flask(__name__)
connect = sq.connect('DataBase.sqlite', check_same_thread=False)

cursor = connect.cursor()

def insert_task(task_type, task_class, task_text, task_answer, task_difficulty):
    amount = cursor.execute("SELECT COUNT (*) FROM problems").fetchall()[0][0]
    text = ""
    prev = 0
    last = 0
    i = 0
    while i < len(task_text):
        if task_text[i] == '\n':
            last = i
            while task_text[i] == '\n':
                i += 1
            text += task_text[prev:last]
            text += '<br>'
            prev = i
        i += 1

    text += task_text[prev:len(task_text)]

    sql_req = f"""
    INSERT INTO problems
    VALUES ({amount}, {task_type}, {task_class}, "{text}", "{task_answer}", {task_difficulty})
    """

    print(sqlReq)
    cursor.execute(sqlReq) #|safe
    connect.commit()

def insert_task_file(task_type, task_class, filename, task_answer, task_difficulty):
    file = open(filename, "r", encoding="UTF-8")
    file_text = file.read()
    insert_task(task_type, task_class, file_text, task_answer, task_difficulty)


insert_task_file(8, 0, "costil.txt", 13000, 1)
