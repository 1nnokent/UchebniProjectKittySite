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
def authorization_page(failed=False, problem=None):
    if request.method == 'GET' and not failed:
        return render_template("user_account_pages/authorization.html")
    if request.method == 'POST' and failed:
        return render_template("user_account_pages/authorization_failed.html", problem=problem)
    if request.method == 'POST':
        info = request.form.to_dict()
        password_input = database_requests.get_password_with_login(info["login"])
        if not password_input:
            return authorization_page(failed=True, problem="Пользователя с данным логином не существует")
            #Отобразить "Неправильный логин или пароль" [неправильный логин]
        elif password_input[0][0] != info['Password']:
            return authorization_page(failed=True, problem="Введен неверный пароль")
            #Отобразить "Неправильный логин или пароль" [неправильный пароль]
        else:
            person_id = database_requests.get_user_id_with_login(info['login'])
            return redirect(url_for('personal_user_page', user_id=person_id))

@app.route("/users/<user_id>")
def personal_user_page(user_id):
    info = database_requests.get_user_info_with_user_id(user_id)
    if not info:
        return render_template("error_pages/authorization_user_not_found_error.html")
    else:
        kwargs = database_requests.user_select_to_dict(info)
        print('!!!!!!!')
        return render_template("templates/user_account_pages/user.html", **kwargs)

@app.route("/problems/add", methods=['POST', 'GET'])
def add_problem():
    if request.method == 'GET':
        return render_template("add_problem.html")
    if request.method == 'POST':
        info = request.form.to_dict()
        if not (1 <= int(info['problem_type']) <= 27):
            return render_template("error_incorrect_problem") #Такого номера задания нет в КИМ

        database_requests.insert_problem(int(info['problem_type']), info['problem_class'], info['problem_source'],
                                         info['problem_statement'], info['problem_answer'], int(info['problem_difficulty']))
        return render_template('problem_added.html')

@app.route("/test")
def test_page():
    problems = database_requests.sql_execute(f"""SELECT * FROM problems""").fetchall()
    return render_template("test.html", problems=problems, user=[0, "aowje"])

@app.route("/blank")
def blank_page():
    return render_template("blank.html")

@app.route("/variants/<variant_id>", methods=['GET', 'POST'])
def variant_page(variant_id):
    if request.method == 'GET':
        kwargs = database_requests.variant_page_default_kwargs(variant_id)
        return render_template("variant_page.html", **kwargs)
    elif request.method == 'POST':
        kwargs = database_requests.variant_page_feedback_kwargs(variant_id)
        database_requests.insert_variant_answers(request.form.to_dict(), variant_id, -1, -1)
        return render_template("variant_page.html", **kwargs)

@app.route("/problems/list")
def problems_page():
    problems = database_requests.sql_execute(f"""SELECT * FROM problems""").fetchall()
    return render_template("problem_list.html", problems=problems)

if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1")
