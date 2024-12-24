from flask import Flask, render_template, request, redirect, url_for
import sqlite3 as sq
from config import database
import database_requests

app = Flask(__name__, template_folder="templates")

@app.route('/')
def first_page():
    return render_template("index.html")

@app.route("/registration", methods=["POST", "GET"])
def registration_page():
    if request.method == "GET":
        return render_template("/user_account_pages/registration.html")
    elif request.method == "POST":
        code = database_requests.insert_user(request.form.to_dict())
        if code == 0:
            return render_template("/user_account_pages/registration_end.html")
        elif code == 1:
            return render_template("/error_pages/error_registration_user_exists.html") #если пользователь уже есть
        else:
            pass

@app.route("/authorization", methods=["POST", "GET"])
def authorization_page(failed=False):
    if request.method == 'GET' and not failed:
        return render_template("user_account_pages/authorization.html")
    if request.method == 'POST' and failed:
        return render_template("user_account_pages/authorization_failed.html")
    if request.method == 'POST':
        info = request.form.to_dict()
        password_input = database_requests.get_password_with_login(info["login"])
        print(info)
        print(password_input)
        if not password_input:
            return authorization_page(failed=True)
            pass #Отобразить "Неправильный логин или пароль" [неправильный логин]
        elif password_input[0][0] != info['Password']:
            return authorization_page(failed=True)
            pass #Отобразить "Неправильный логин или пароль" [неправильный пароль]
        else:
            person_id = database_requests.get_user_id_with_login(info['login'])
            return redirect(url_for('personal_user_page', id=person_id))

@app.route("/users/<id>")
def personal_user_page(id):
    info = database_requests.get_user_info_with_user_id(id)
    print(info)
    if not info:
        return render_template("error_pages/authorization_user_not_found_error.html")
    else:
        kwargs = database_requests.user_select_to_dict(info)
        print(kwargs)
        return render_template("user_account_pages/user.html", **kwargs)

@app.route("/problems/add", methods=['POST', 'GET'])
def add_problem():
    if request.method == 'GET':
        return render_template("add_problem.html")
    if request.method == 'POST':
        info = request.form.to_dict()
        print(info)
        if not (1 <= int(info['problem_type']) <= 27):
            return render_template("error_incorrect_problem") #Такого номера задания нет в КИМ

        database_requests.insert_problem(int(info['problem_type']), info['problem_class'], info['problem_source'],
                                         info['problem_statement'], info['problem_answer'], int(info['problem_difficulty']))
        return render_template('problem_added.html')

@app.route("/test")
def test_page():
    problems = database_requests.sql_execute(f"""SELECT * FROM problems""").fetchall()
    print(problems)
    return render_template("test.html", problems=problems)

@app.route("/variants/<variant_id>", methods=['GET', 'POST'])
def variant_page(variant_id):
    sql_req = f"""SELECT * FROM
                  problems INNER JOIN variant_problem
                  ON variant_problem.problem_id = problems.problem_id
                  WHERE variant_problem.variant_id = {variant_id}"""
    problems = database_requests.sql_execute(sql_req).fetchall()
    answers_default = (-1,) * len(problems)
    print(problems)
    kwargs = dict()
    if request.method == 'GET':
        kwargs['problems'] = problems
        kwargs['answers'] = answers_default
        kwargs['show_answers'] = False
        kwargs['amount_right'] = -1
        return render_template("variant_demo.html", **kwargs)
    elif request.method == 'POST':
        given_answers = []
        tmp = request.form.to_dict()
        if not (tmp.__contains__('show_answers')):
            tmp['show_answers'] = False
        else:
            tmp['show_answers'] = True
        for key in tmp:
            given_answers.append(tmp[key])
        answers = []
        for i in range(len(problems)):
            if (given_answers[i] == ''):
                answers.append(-1)
            else:
                answers.append(int(given_answers[i] == database_requests.sql_execute(f"""SELECT problem_answer FROM problems 
                WHERE problem_id = { problems[i][0] }""").fetchall()[0][0]))
        database_requests.insert_answers_to_variant_from_user(tmp, variant_id, -1, -1)
        answers = tuple(answers)
        kwargs['problems'] = problems
        kwargs['answers'] = answers
        kwargs['show_answers'] = tmp['show_answers']
        kwargs['amount_right'] = 0
        for elem in answers:
            if elem == 1:
                kwargs['amount_right'] += 1
        return render_template("variant_demo.html", **kwargs)


@app.route("/problems/list")
def problems_page():
    problems = database_requests.sql_execute(f"""SELECT * FROM problems""").fetchall()
    print(problems)
    return render_template("problem_list.html", problems=problems)


if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1")
