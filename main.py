import configparser
import requests
import codecs
import hashlib
from ast import literal_eval as eval
from flask import Flask, render_template, redirect, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms.loginform import LoginForm
from forms.registerform import RegisterForm


config_file = configparser.ConfigParser()
config_file.read_file(codecs.open("settings.ini", "r", "utf8"))
URL_API = config_file["API"]["url_api"]
REGISTRATION = config_file["Registration"]
app = Flask(__name__)
app.config['SECRET_KEY'] = config_file["CSRF"]["secret_key"]
# session.permanent = True
# login_manager = LoginManager()
# login_manager.init_app(app)


# @login_manager.user_loader
# def load_user(user_id):
#     response = requests.get(URL_API + f"user\\{user_id}").json()
#     return response


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect("/")

@app.route('/session_test/')
def session_test():
    if 'visits_count' in session:
        session['visits_count'] = session.get('visits_count') + 1
    else:
        session['visits_count'] = 1
    # дальше - код для вывода страницы


@app.route('/')
def main():
    params = {"random": 15}
    response = requests.get(URL_API + "books", params=params)
    response_json = response.json()
    books = response_json['books']
    return render_template("main.html", books=books)


@app.route("/books", methods=["GET", "POST"])
def books():
    params = {}
    response = requests.get(URL_API + "books", params=params)
    response_json = response.json()
    return response_json


@app.route('/genres')
def genres():
    response = requests.get(URL_API + "book\\genres", json={})
    print(response.json())
    return


@app.route('/authors')
def authors():
    pass


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_request = eval(config_file["Login"]["login_request_structure"])
        login_statuses = eval(config_file["Login"]["login_statuses"])
        user = login_request["user"]
        user["login"] = form.username.data
        user["password_hash"] = hashlib.md5(bytes(form.password.data, encoding='utf-8')).hexdigest()
        response = requests.get(URL_API + "login", json=login_request).json()
        status = response["authentication_status"]
        if status == "SUCCESS":
            login_user(response["user"], remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', form=form, message=login_statuses[status])
    return render_template('login.html', form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    types = [type(field).__name__ for field in form]
    if form.validate_on_submit():
        registration_statuses = eval(REGISTRATION["registration_statuses"])
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form, types=types,
                                   message=registration_statuses["PASSWORD_MISMATCH"])

        registration_request = eval(REGISTRATION["registration_request_structure"])
        user = registration_request["user"]
        user["login"] = form.username.data
        user["name"] = form.name.data
        user["surname"] = form.surname.data
        user["email"] = form.email.data
        user["address"]["city"] = form.city.data
        user["address"]["address_line"] = form.address.data
        user["password_hash"] = hashlib.md5(bytes(form.password.data, encoding = 'utf-8')).hexdigest()
        print(user["password_hash"])
        response = requests.post(URL_API + "registration", json=registration_request).json()
        status = response["authentication_status"]
        if status == "SUCCESS":
            return redirect('/login')
        return render_template("register.html", form=form, types=types, message=registration_statuses[status])
    return render_template("register.html", form=form, types=types)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')