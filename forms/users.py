from flask_login import UserMixin


class User(UserMixin):
    id = None
    login = None
    name = None
    surname = None
    type = None
    cart = None


def convert_user(response_user):
    user = response_user["user"]
    result_user = User()
    result_user.id = user["id"]
    result_user.login = user["login"]
    result_user.name = user["name"]
    result_user.surname = user["surname"]
    result_user.type = user["type"]
    result_user.cart = user["cart"]
    return result_user