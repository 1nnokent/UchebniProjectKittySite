from flask import Flask, render_template, request
import sqlite3 as sq

app = Flask(__name__)
connect = sq.connect('DataBase.sqlite', check_same_thread=False)

cursor = connect.cursor()

Amount = cursor.execute("SELECT COUNT (*) FROM Tasks").fetchall()[0][0]
#No = int(input())
#Type = int(input())
No = 5
Type = -1
file = open("costil.txt", "r", encoding="UTF-8")
FileText = file.read()
Text = ""
prev = 0
last = 0
i = 0
while i < len(FileText):
    if FileText[i] == '\n':
        last = i
        while FileText[i] == '\n':
            i += 1
        Text += FileText[prev:last]
        Text += '<br>'
        prev = i
    i += 1

Text += FileText[prev:len(FileText)]

Answer = int(input())

sqlReq = f"""
INSERT INTO Tasks
VALUES ({Amount}, {No}, {Type}, "{Text}", {Answer})
"""

print(sqlReq)
cursor.execute(sqlReq) #|safe
connect.commit()
