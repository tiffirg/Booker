import configparser
from flask import Flask


config_file = configparser.ConfigParser()  # создаём объекта парсера
config_file.read("settings.ini")
app = Flask(__name__)
print(config_file["CSRF"]["secret_key"])
app.config['SECRET_KEY'] = config_file["CSRF"]["secret_key"]


if __name__ == '__main__':
    app.run()