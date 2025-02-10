from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3 as sq
from config import database
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import database_requests as dr

app = Flask(__name__, template_folder="templates")
app.secret_key = 'super_secret_key'

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'authorization_page'

class User(UserMixin):
    def __init__(self, user_id, role):
        self.id = user_id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    user_info = dr.get_user_info_with_user_id(user_id)
    if user_info:
        return User(user_id=user_info[0], role=user_info[5])
    return None


# Общие страницы

# Главная страница
@app.route('/')
def first_page():
    amount = dr.sql_execute("SELECT count(*) FROM variants").fetchall()[0][0]
    return render_template("yandex.html", amount=amount)

# Тестовая страница
@app.route("/test")
def test_page():
    problems = dr.sql_execute("SELECT * FROM problems").fetchall()
    return render_template("test.html", user=[0, "aowje"])

# Пустая страница
@app.route("/blank")
def blank_page():
    return render_template("blank.html")

# Страница ошибки
@app.route("/error/")
def error_page():
    return render_template("error_pages/error_page.html")


# Личные страницы пользователя

# Регистрация пользователя
@app.route("/registration", methods=["POST", "GET"])
def registration_page():
    if request.method == "GET":
        return render_template("user_account_pages/registration.html")
    elif request.method == "POST":
        user_data = request.form.to_dict()
        code = dr.insert_user(user_data)
        if code == 0:
            return render_template("user_account_pages/registration_end.html")
        elif code == 1:
            return render_template("error_pages/error_registration_user_exists.html")
        else:
            pass

# Авторизация пользователя
@app.route("/authorization", methods=["POST", "GET"])
def authorization_page(failed=False, problem=None):
    if request.method == "GET":
        return render_template("user_account_pages/authorization.html")
    elif request.method == "POST":
        if failed:
            return render_template("user_account_pages/authorization_failed.html", problem=problem)
        info = request.form.to_dict()
        password_input = dr.get_password_with_login(info["login"])
        if not password_input:
            return authorization_page(failed=True, problem="Пользователя с данным логином не существует")
        elif password_input[0][0] != info["Password"]:
            return authorization_page(failed=True, problem="Введен неверный пароль")
        person_id = dr.get_user_id_with_login(info["login"])
        user = User(user_id=person_id, role=dr.get_user_info_with_user_id(person_id)[5])
        login_user(user)
        return redirect(url_for("personal_user_page"))
    
# Аккаунт пользователя
@app.route("/user/profile")
@login_required
def personal_user_page():
    info = dr.get_user_info_with_user_id(current_user.id)
    if not info:
        return render_template("error_pages/authorization_user_not_found_error.html")
    kwargs = dr.user_select_to_dict(info)
    name = dr.get_user_name(current_user.id)
    print(name)
    return render_template("user_account_pages/user.html", **kwargs, user=name)


# Форум

# Список тем
@app.route('/forum/topics/all', methods=["POST", "GET"])
@login_required
def forum_main_page():
    if request.method == "GET":
        discussions = dr.get_discussions()
        name = dr.get_user_name(current_user.id)
        return render_template("forum/forum_main_page.html", discussions=discussions, user=name)
    elif request.method == "POST":
        info = request.form.to_dict()
        topic_id = dr.insert_new_topic(info)
        return redirect(url_for("forum_topic_page", topic_id=topic_id))

# Конкретная тема
@app.route('/forum/topics/<topic_id>', methods=["POST", "GET"])
@login_required
def forum_topic_page(topic_id):
    if request.method == "GET":
        name = dr.get_user_name(current_user.id)
        topic_name = dr.get_topic_name(topic_id)
        messages = dr.get_topic_messages(topic_id)
        return render_template("forum/forum_topic_page.html", topic_name=topic_name, messages=messages, user=name)
    elif request.method == "POST":
        info = request.form.to_dict()
        dr.insert_topic_message(topic_id, info)
        return redirect(url_for("forum_topic_page", topic_id=topic_id))


# Группы

# Главная страница групп
@app.route('/groups/all', methods=["POST", "GET"])
@login_required
def group_main_page():
    groups = dr.get_groups(current_user.id)
    name = dr.get_user_name(current_user.id)
    return render_template("groups/group_main.html", groups=groups, user=name)

# Страница группы
@app.route("/groups/<group_id>", methods=["GET", "POST"])
@login_required
def group_page(group_id):
    if request.method == "GET":
        members = dr.get_group_members(group_id)
        courses = dr.get_group_courses(group_id)
        assignments = dr.get_group_assignments(group_id)
        name = dr.get_user_name(current_user.id)
        return render_template("groups/group_page.html", members=members, courses=courses, assignments=assignments, user=name)
    elif request.method == "POST":
        pass


# Курсы

# Список курсов
@app.route("/courses/all")
def course_main_page():
    courses = dr.get_courses()
    return render_template("courses/courses_page.html", courses=courses)

# Страница курса
@app.route("/courses/<course_id>")
def course_page(course_id):
    materials = dr.get_course_materials(course_id)
    variant = dr.get_course_variant(course_id)
    return render_template("courses/course_page.html", materials=materials, course_id=course_id, variant_id=variant[0][0])

# Добавление курса
@app.route("/courses/add", methods=["GET", "POST"])
def add_course():
    if request.method == "GET":
        return render_template("courses/add_course.html")
    elif request.method == "POST":
        info = request.form.to_dict()
        course_id = dr.sql_execute("SELECT count(*) FROM courses").fetchall()[0][0] + 1
        dr.insert_course(course_id, info["course_name"], info["course_description"])
        return redirect(url_for("edit_course", course_id=course_id))

# Редактирование курса
@app.route("/courses/<course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):
    if request.method == "GET":
        learning_materials = dr.get_learning_materials_by_course(course_id)
        return render_template("courses/edit_course.html", learning_materials=learning_materials, course_id=course_id)
    elif request.method == "POST":
        info = request.form.to_dict()
        operation = "learning_material_id_add" in info
        learning_material_id = info[list(info.keys())[0]]
        mmax = dr.sql_execute("SELECT count(*) FROM learning_materials").fetchall()[0][0]
        if learning_material_id == "" or int(learning_material_id) - 1 >= mmax:
            return redirect(url_for("error_page"))
        if operation:
            dr.insert_learning_material_to_course(course_id, int(learning_material_id) - 1)
        else:
            dr.remove_learning_material_from_course(course_id, int(learning_material_id))
        return redirect(url_for("edit_course", course_id=course_id))

# Редактирование варианта задания на курсе
@app.route("/courses/<course_id>/edit_variant", methods=["GET", "POST"])
def edit_course_variant(course_id):
    if request.method == "GET":
        variant = dr.get_variant_by_course(course_id)
        return render_template("courses/edit_course_variant.html", variant=variant[0][0], course_id=course_id)
    elif request.method == "POST":
        info = request.form.to_dict()
        dr.change_variant(course_id, int(info["num_var"]))
        return redirect(url_for("edit_course_variant", course_id=course_id))

# Страница варианта задания для курса
@app.route("/variants_fc/<course_id>/<variant_id>", methods=["GET", "POST"])
def variant_page_fc(course_id, variant_id):
    if request.method == "GET":
        kwargs = dr.variant_page_default_kwargs(variant_id)
        return render_template("courses/variant_page_fc.html", **kwargs, course_id=course_id, variant_id=variant_id)
    elif request.method == "POST":
        kwargs = dr.variant_page_feedback_kwargs(variant_id)
        dr.insert_variant_answers(request.form.to_dict(), variant_id, -1, -1)
        return render_template("courses/variant_page_fc.html", **kwargs, course_id=course_id, variant_id=variant_id)


# Учебные материалы

# Список учебных материалов
@app.route("/learning-materials/all")
def learning_materials_page():
    materials = dr.get_learning_materials()
    return render_template("materials/learning_materials.html", materials=materials)

# Страница учебного материала
@app.route("/learning-materials/<material_id>")
def learning_material_page(material_id):
    material = dr.get_learning_material(material_id)
    if material[1] == 0:
        return render_template("materials/learning_video.html", material=material)
    elif material[1] == 1:
        print(material[4])
        return render_template("materials/learning_presentation.html", material=material)
    elif material[1] == 2:
        return render_template("materials/learning_conspect.html", material=material)


# Варианты

# Добавление варианта
@app.route("/variants/add", methods=["GET", "POST"])
@login_required
def add_variant():
    if request.method == "GET":
        name = dr.get_user_name(current_user.id)
        return render_template("variants/add_variant.html", user=name)
    elif request.method == "POST":
        info = request.form.to_dict()
        variant_id = dr.sql_execute("SELECT count(*) FROM variants").fetchall()[0][0] + 1
        dr.insert_variant(variant_id, info["variant_name"], info["variant_description"], 0)
        return redirect(url_for("edit_variant", variant_id=variant_id))

# Редактирование варианта
@app.route("/variants/<variant_id>/edit", methods=["GET", "POST"])
@login_required
def edit_variant(variant_id):
    if request.method == "GET":
        kwargs = dr.variant_page_default_kwargs(variant_id)
        name = dr.get_user_name(current_user.id)
        return render_template("variants/edit_variant.html", **kwargs, user=name)
    elif request.method == "POST":
        info = request.form.to_dict()
        display_mode = request.form["feedbackOption"]
        dr.change_variant_display_mode(variant_id, display_mode)
        problem_id = info[list(info.keys())[0]]
        mmax = dr.sql_execute("SELECT count(*) FROM problems").fetchall()[0][0]
        if problem_id == "" or int(problem_id) - 1 >= mmax:
            return redirect(url_for("error_page"))
        if "problem_id_add" in info:
            dr.insert_problem_to_variant(variant_id, int(problem_id) - 1)
        elif "problem_id_delete" in info:
            dr.remove_problem_from_variant(variant_id, int(problem_id))
        return redirect(url_for("edit_variant", variant_id=variant_id))

# Страница варианта
@app.route("/variants/<variant_id>", methods=["GET", "POST"])
def variant_page(variant_id):
    if request.method == "GET":
        kwargs = dr.variant_page_default_kwargs(variant_id)
        return render_template("variants/variant_page.html", **kwargs)
    elif request.method == "POST":
        kwargs = dr.variant_page_feedback_kwargs(variant_id)
        dr.insert_variant_answers(request.form.to_dict(), variant_id, -1, -1)
        return render_template("variants/variant_page.html", **kwargs)


#Задачи

# Список задач
@app.route("/problems/all")
def problems_page():
    problems = dr.get_problems()
    name = dr.get_user_name(current_user.id)
    return render_template("problems/problem_list.html", problems=problems, user=name)

# Редактирование задачи
@app.route("/problems/<problem_id>/edit", methods=["GET", "POST"])
@login_required
def edit_problem(problem_id):
    if request.method == "GET":
        problem = dr.sql_execute(f"SELECT * FROM problems WHERE problem_id = {problem_id}").fetchall()[0]
        name = dr.get_user_name(current_user.id)
        return render_template("problems/edit_problem.html", problem=problem, user=name)
    elif request.method == "POST":
        info = request.form.to_dict()
        if info["problem_type"] == "" or not (1 <= int(info["problem_type"]) <= 27):
            return redirect(url_for("error_page"))
        dr.sql_execute(f"DELETE FROM problems WHERE problem_id = {problem_id}")
        dr.insert_problem(
            int(info["problem_type"]),
            info["problem_source"],
            info["problem_statement"],
            info["problem_answer"],
            int(info["problem_difficulty"]),
            problem_id=problem_id
        )
        return redirect(url_for("problems_page"))

# Добавление задачи
@app.route("/problems/add", methods=["GET", "POST"])
@login_required
def add_problem():
    if request.method == "GET":
        name = dr.get_user_name(current_user.id)
        return render_template("problems/add_problem.html", user=name)
    elif request.method == "POST":
        info = request.form.to_dict()
        if info["problem_type"] == "" or not (1 <= int(info["problem_type"]) <= 27):
            return redirect(url_for("error_page"))
        dr.insert_problem(
            int(info["problem_type"]),
            info["problem_source"],
            info["problem_statement"],
            info["problem_answer"],
            int(info["problem_difficulty"])
        )
        return redirect(url_for("add_problem"))


if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1")
