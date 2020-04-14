import configparser
import requests
from flask import Flask, render_template, request


config_file = configparser.ConfigParser()
config_file.read("settings.ini")
URL_API = config_file["API"]["url_api"]
app = Flask(__name__)
app.config['SECRET_KEY'] = config_file["CSRF"]["secret_key"]


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
    print(response_json)
    return response_json


@app.route('/genres')
def genres():
    pass


@app.route('/authors')
def authors():
    pass


@app.route('/login')
def login():
    pass


@app.route("/register")
def register():
    pass

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')