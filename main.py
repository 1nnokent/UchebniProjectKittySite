from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3 as sq
from config import database
import database_requests as dr

app = Flask(__name__, template_folder="templates")

@app.route('/')
def first_page():
    amount = dr.sql_execute("SELECT count(*) FROM variants").fetchall()[0][0]
    return render_template("yandex.html", amount=amount)

@app.route("/registration", methods=["POST", "GET"])
def registration_page():
    if request.method == "GET":
        return render_template("/user_account_pages/registration.html")
    if request.method == "POST":
        code = dr.insert_user(request.form.to_dict())
        if code == 0:
            return render_template("/user_account_pages/registration_end.html")
        if code == 1:
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
        password_input = dr.get_password_with_login(info["login"])
        if not password_input:
            return authorization_page(failed=True, problem="Пользователя с данным логином не существует")
            #Отобразить "Неправильный логин или пароль" [неправильный логин]
        elif password_input[0][0] != info['Password']:
            return authorization_page(failed=True, problem="Введен неверный пароль")
            #Отобразить "Неправильный логин или пароль" [неправильный пароль]
        else:
            person_id = dr.get_user_id_with_login(info['login'])
            return redirect(url_for('personal_user_page', user_id=person_id))

@app.route("/users/<user_id>")
def personal_user_page(user_id):
    info = dr.get_user_info_with_user_id(user_id)
    if not info:
        return render_template("error_pages/authorization_user_not_found_error.html")
    else:
        kwargs = dr.user_select_to_dict(info)
        return render_template("user_account_pages/user.html", **kwargs)

@app.route("/test")
def test_page():
    problems = dr.sql_execute(f"""SELECT * FROM problems""").fetchall()
    return render_template("test.html", user=[0, "aowje"])

@app.route("/learning-materials/all")
def learning_materials_page():
    materials = dr.get_learning_materials()
    return render_template('learning_materials.html', materials=materials)

@app.route("/learning-materials/<material_id>")
def learning_material_page(material_id):
    material = dr.get_learning_material(material_id)
    print(material)
    if material[1] == 0:
        return render_template('learning_video.html', material=material)
    if material[1] == 1:
        return render_template('learning_presentation.html', material=material)
    if material[1] == 2:
        return render_template('learning_conspect.html', material=material)


@app.route("/blank")
def blank_page():
    return render_template("blank.html")

@app.route("/variants/add", methods=['GET', 'POST'])
def add_variant():
    if request.method == 'GET':
        return render_template('add_variant.html')
    if request.method == 'POST':
        info = request.form.to_dict()
        variant_id = dr.sql_execute("SELECT count(*) FROM variants").fetchall()[0][0] + 1
        dr.insert_variant(variant_id, info['variant_name'], info['variant_description'], 0)
        return redirect(url_for('modify_variant', variant_id=variant_id))

@app.route("/variants/<variant_id>/modify", methods=['GET', 'POST'])
def modify_variant(variant_id):
    if request.method == 'GET':
        problems = dr.get_problems_by_variant(variant_id)
        return render_template('modify_variant.html', problems=problems)
    if request.method == 'POST':
        problem_id = request.form.to_dict()['problem_id']

        if problem_id == '' or int(problem_id) >= dr.sql_execute("SELECT count(*) FROM problems").fetchall()[0][0]:
            return redirect(url_for('error_page'))

        dr.insert_problem_to_variant(variant_id, int(problem_id))
        return redirect(url_for('modify_variant', variant_id=variant_id))

@app.route("/variants/<variant_id>", methods=['GET', 'POST'])
def variant_page(variant_id):
    if request.method == 'GET':
        kwargs = dr.variant_page_default_kwargs(variant_id)
        return render_template("variant_page.html", **kwargs)
    if request.method == 'POST':
        kwargs = dr.variant_page_feedback_kwargs(variant_id)
        dr.insert_variant_answers(request.form.to_dict(), variant_id, -1, -1)
        return render_template("variant_page.html", **kwargs)

@app.route('/forum/topics/all', methods=['POST', 'GET'])
def forum_main_page():
    if request.method == 'GET':
        discussions = dr.get_discussions()
        print(discussions)
        return render_template("forum_main_page.html", discussions=discussions)
    if request.method == 'POST':
        info = request.form.to_dict()
        topic_id = dr.insert_new_topic(info)
        return redirect(url_for('forum_topic_page', topic_id=topic_id))

@app.route('/forum/topics/<topic_id>', methods=['POST', 'GET'])
def forum_topic_page(topic_id):
    if request.method == 'GET':
        topic_name = dr.get_topic_name(topic_id)
        messages = dr.get_topic_messages(topic_id)
        return render_template('forum_topic_page.html', topic_name=topic_name, messages=messages)
    if request.method == 'POST':
        info = request.form.to_dict()
        dr.insert_topic_message(topic_id, info)
        topic_name = dr.get_topic_name(topic_id)
        messages = dr.get_topic_messages(topic_id)
        return redirect(url_for('forum_topic_page', topic_id=topic_id))

@app.route("/problems/all")
def problems_page():
    problems = dr.sql_execute(f"""SELECT * FROM problems""").fetchall()
    return render_template("problem_list.html", problems=problems)

@app.route("/problems/add", methods=['POST', 'GET'])
def add_problem():
    if request.method == 'GET':
        return render_template("add_problem.html")
    if request.method == 'POST':
        info = request.form.to_dict()
        if not (1 <= int(info['problem_type']) <= 27):
            return redirect(url_for('error_page')) #Такого номера задания нет в КИМ

        dr.insert_problem(int(info['problem_type']), info['problem_source'],
                                         info['problem_statement'], info['problem_answer'], int(info['problem_difficulty']))
        return redirect(url_for('add_problem'))

@app.route("/courses/all")
def courses_page():
    courses = dr.get_courses()
    return render_template("courses_page.html", courses=courses)

@app.route("/courses/<course_id>")
def course_page(course_id):
    materials = dr.get_course_materials(course_id)
    return render_template("course_page.html", materials=materials)

@app.route("/error/")
def error_page():
    return render_template('error.html')

if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1")

