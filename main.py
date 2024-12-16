from flask import Flask, render_template, request, redirect, url_for
import sqlite3 as sq

app = Flask(__name__, template_folder="templates")
connect = sq.connect('DataBase.sqlite', check_same_thread=False)

cursor = connect.cursor()

def toKwargsUser(tuple):
    dict = {}
    dict['UserID'] = tuple[0][0]
    dict['Login'] = tuple[0][1]
    dict['Password'] = tuple[0][2]
    dict['FirstName'] = tuple[0][3]
    dict['SecondName'] = tuple[0][4]
    dict['EmailAddress'] = tuple[0][5]
    dict['PhoneNumber'] = tuple[0][6]
    dict['SiteAddress'] = tuple[0][7]
    dict['BirthdayDate'] = tuple[0][8]
    dict['CatType'] = tuple[0][9]
    dict['About'] = tuple[0][10]
    if tuple[0][11] == -1:
        dict['PhotoID'] = "/img/profile-pictures/profile_default.jpg"
    else:
        dict['PhotoID'] = ("/img/profile-pictures/profile_") + str(tuple[0][0]) + ".jpg"
    dict['CertifiedKitty'] = tuple[0][12]
    return dict

@app.route('/')
def first_page():
    return render_template("index.html")

@app.route("/registration", methods=["POST", "GET"])
def registration_page():
    if request.method == "GET":
        return render_template("registration.html")
    elif request.method == "POST":
        info = request.form.to_dict()
        print(info)

        currentId = int(cursor.execute("""
        SELECT COUNT(*) FROM Users
        """).fetchall()[0][0])
        certifiedKitty = False
        if info.get('CertifiedKitty') == 'on':
            certifiedKitty = True
        does_exist = cursor.execute(f"""SELECT * FROM Users WHERE Login = "{info["Login"]}" """).fetchall()

        if len(does_exist):
            return render_template("error_pages/registration_user_exists_error.html")
            pass #если пользователь уже есть
        else:
            photo = request.files['file']
            hasPhoto = not (request.files['file'].filename == '')
            photoId = -1
            if hasPhoto:
                photoId = currentId
            sqlReq = f"""
                        INSERT INTO Users 
                        VALUES ({currentId}, "{info['Login']}", "{info['Password']}", "{info['FirstName']}", "{info['SecondName']}", "{info['EmailAddress']}", "{info['PhoneNumber']}", 
                        "{info['SiteAddress']}", "{info['BirthdayDate']}", "{info['CatType']}", "{info['About']}", {photoId}, {certifiedKitty})
                        """
            path = "static/img/profile-pictures/profile_" + str(currentId) + ".jpg"
            photo.save(path)
            cursor.execute(sqlReq)
            connect.commit()

            return render_template("registration_end.html")


@app.route("/authorization", methods=["POST", "GET"])
def authorization_page(Failed=False):
    if request.method == 'GET' and not Failed:
        return render_template("user_account_pages/authorization.html")
    if request.method == 'POST' and Failed:
        return render_template("user_account_pages/authorization_failed.html")
    if request.method == 'POST':
        info = request.form.to_dict()
        sqlReq = f"""
        SELECT Password FROM Users
        WHERE Users.Login = "{info["Login"]}"
        """
        password_input = cursor.execute(sqlReq).fetchall()
        print(info)
        print(password_input)
        if password_input == []:
            return authorization_page(Failed=True)
            pass #Отобразить "Неправильный логин или пароль" [неправильный логин]
        elif password_input[0][0] != info['Password']:
            return authorization_page(Failed=True)
            pass #Отобразить "Неправильный логин или пароль" [неправильный пароль]
        else:
            sqlReq = f"""
            SELECT UserID FROM Users
            WHERE Users.Login = "{info["Login"]}"
            """
            person_id = cursor.execute(sqlReq).fetchall()[0][0]
            return redirect(url_for('personal_user_page', id=person_id))


@app.route("/users/<id>")
def personal_user_page(id):
    sqlReq = f"""
    SELECT * from Users
    WHERE UserID = "{ id }"
    """
    info = cursor.execute(sqlReq).fetchall()
    print(info)
    if info == []:
        return render_template("error_pages/authorization_user_not_found_error.html")
    else:
        kwargs = toKwargsUser(cursor.execute(sqlReq).fetchall())
        print(kwargs)
        return render_template("user_account_pages/user.html", **kwargs)


@app.route("/test")
def test_page():
    sqlReq =\
        f"""
        SELECT * FROM Tasks
        """
    Tasks = cursor.execute(sqlReq).fetchall()
    print(Tasks)
    return render_template("error_pages/error_404_not_found.html", Tasks=Tasks)

@app.route("/tasks")
def tasks_page():
    sqlReq =\
        f"""
            SELECT * FROM Tasks
        """
    Tasks = cursor.execute(sqlReq).fetchall()
    print(Tasks)
    return render_template("tasks.html", Tasks=Tasks)


if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1")
