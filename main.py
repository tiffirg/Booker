import configparser
import requests
import codecs
import os
import hashlib
from random import shuffle
from ast import literal_eval as eval
from flask import Flask, render_template, redirect, abort, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms.loginform import LoginForm
from forms.registerform import RegisterForm
from forms.cartlibrarianform import LibrarianForm
from forms.users import convert_user


config_file = configparser.ConfigParser()
config_file.read_file(codecs.open("settings.ini", "r", "utf8"))
URL_API = config_file["API"]["url_api"]
REGISTRATION = config_file["Registration"]
app = Flask(__name__)
app.config['SECRET_KEY'] = config_file["CSRF"]["secret_key"]
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    response = requests.get(URL_API + f"user/{user_id}").json()
    user = convert_user(response)
    return user


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/', methods=["GET", "POST"])
def index():
    all_books = []
    result_words = []
    params = {"random": int(config_file["Constant"]["amount_books_slider"])}
    response_books = requests.get(URL_API + "books", params=params)
    response_books_json = response_books.json()
    books = response_books_json['books']
    all_books.append(books)
    result_words.append({"header": "Книги", "link_words": "Все книги", "link": "/books/0"})
    response_genres = requests.get(URL_API + "book/genres")
    response_genres_json = response_genres.json()
    genres = [response_genre for response_genre in response_genres_json["genres"]]
    shuffle(genres)
    genres = genres[:int(config_file["Constant"]["amount_genres_index"])]
    for genre in genres:
        params["genre"] = genre["name"]
        response_genre = requests.get(URL_API + 'books', params=params)
        response_genre_json = response_genre.json()
        genre_books = response_genre_json["books"]
        all_books.append(genre_books)
        result_words.append({"header": genre["name"], "link_words": "Книги жанра", "link": f"genre/{genre['id']}/0"})
    return render_template("index.html", url="/book/", all_books=all_books, words=result_words)


@app.route("/books/<int:page>", methods=["GET", "POST"])
def books(page):
    amount_books = int(config_file["Constant"]["page_amount_books"])
    params = {"onlyAmount": True}
    amount_all_books = requests.get(URL_API + "books", params=params).json()["amount"]
    amount_pages = amount_all_books // amount_books + 1 if amount_all_books % amount_books != 0 else 0
    params = {"amount": amount_books, "start": amount_books * page}
    response = requests.get(URL_API + "books", params=params).json()
    books = response["books"]
    return render_template("books.html", url="/book/", books=books, amount_pages=amount_pages)


@app.route("/book/<int:id>", methods=["POST", "GET"])
def book(id):
    book_in_cart, it_is_librarian = False, False
    in_issuance = False
    response = requests.get(URL_API + "book/" + str(id)).json()
    book = response["book"]
    if not current_user.is_authenticated:
        return render_template("book.html", book=book)
    book_id = book["id"]
    response = requests.get(URL_API + f'user/{current_user.id}').json()
    user = response["user"]
    if user["type"] == "LIBRARIAN":
        it_is_librarian = True
        return render_template("book.html", book=book, book_in_cart=book_in_cart, it_is_librarian=it_is_librarian)
    if user["cart"] and str(book_id) in user["cart"].split(";"):
        book_in_cart = True
    issues = requests.get(URL_API + "issues", json={"user_id": current_user.id, "issue_status": "ISSUED"}).json()
    if issues.get("error", False):
        return render_template("book.html", book=book, book_in_cart=book_in_cart)
    for issue in issues:
        if issue["id"] == book_id:
            in_issuance = True
            break
    return render_template("book.html", book=book, book_in_cart=book_in_cart, it_is_librarian=it_is_librarian,
                           in_issuance=in_issuance)


@app.route('/genres', methods=["GET", "POST"])
def genres():
    params = {"letters": True}
    response = requests.get(URL_API + "book/genres", params=params).json()
    dict_genres = response["genres"]
    return render_template("genres.html", dict_genres=dict_genres, url="/genre/")


@app.route("/genre/<int:id>/<int:page>", methods=["GET", "POST"])
def genre(id, page):
    name = requests.get(URL_API + f"genre/{id}").json()["genre"]["name"]
    amount_books = int(config_file["Constant"]["page_amount_books"])
    params = {"onlyAmount": True, "genre": name}
    amount_all_books_genre = requests.get(URL_API + "books", params=params).json()["amount"]
    amount_pages = amount_all_books_genre // amount_books + 1 if amount_all_books_genre % amount_books != 0 else 0
    params = {"amount": amount_books, "start": amount_books * page, "genre": name}
    response = requests.get(URL_API + "books", params=params).json()
    books_genre = response["books"]
    return render_template("books.html", url="/book/", books=books_genre, amount_pages=amount_pages)


@app.route('/authors', methods=["GET", "POST"])
def authors():
    params = {"letters": True}
    response = requests.get(URL_API + "book/authors", params=params).json()
    dict_authors = response["authors"]
    return render_template("authors.html", dict_authors=dict_authors, url="/author/")


@app.route('/author/<int:id>/<int:page>', methods=["GET", "POST"])
def author(id, page):
    name = requests.get(URL_API + f"author/{id}").json()["author"]["name"]
    amount_books = int(config_file["Constant"]["page_amount_books"])
    params = {"onlyAmount": True, "author": name}
    amount_all_books_author = requests.get(URL_API + "books", params=params).json()["amount"]
    amount_pages = amount_all_books_author // amount_books + 1 if amount_all_books_author % amount_books != 0 else 0
    params = {"amount": amount_books, "start": amount_books * page, "author": name}
    response = requests.get(URL_API + "books", params=params).json()
    books_genre = response["books"]
    return render_template("books.html", url="/book/", books=books_genre, amount_pages=amount_pages)


@app.route('/cart', methods=["GET", "POST"])
@login_required
def cart():
    it_is_librarian = False
    response = requests.get(URL_API + f'user/{current_user.id}').json()
    user = response["user"]
    if user["type"] == "LIBRARIAN":
        form = LibrarianForm()
        it_is_librarian = True
        if form.validate_on_submit():
            adding_book_request = eval(config_file["Adding"]["adding_book_request_structure"])
            adding_book_statuses = eval(config_file["Adding"]["adding_book_statuses"])
            adding_book = adding_book_request["book"]
            adding_book["name"] = form.name.data
            adding_book["author"] = form.author.data
            adding_book["genre"] = form.genre.data
            adding_book["barcode"] = form.barcode.data
            adding_book["description"] = form.description.data
            adding_book["image_url"] = form.image_url.data
            adding_book["icon_url"] = form.icon_url.data
            response = requests.post(URL_API + "/book", json=adding_book_request).json()
            status = response["add_status"]
            message = adding_book_statuses[status]
            if status == "SUCCESS":
                trash = ["csrf_token", "submit"]
                for field in form:
                    if field.name not in trash:
                        field.data = ""
            return render_template("cart.html", form=form, it_is_librarian=it_is_librarian, message=message)
        return render_template("cart.html", form=form, it_is_librarian=it_is_librarian)
    if not user["cart"]:
        return render_template("cart.html", it_is_librarian=it_is_librarian)
    ids = [int(el) for el in user["cart"].split(";")]
    cart = [requests.get(URL_API + f'book/{book_id}').json()["book"] for book_id in ids]
    return render_template("cart.html", it_is_librarian=it_is_librarian, cart=cart, url="/book/")


@app.route('/forward/', methods=["GET", "POST"])
def forward():
    not_search = False
    search = request.form["search"]
    response = requests.get(URL_API + "books", params={"search": search}).json()
    books = response["books"]
    amount = response["amount"]
    if amount == 1:
        book_id = books[0]["id"]
        return redirect(f"/book/{book_id}")
    if amount == 0:
        not_search = True
        params = {"random": int(config_file["Constant"]["amount_books_slider"])}
        response_books = requests.get(URL_API + "books", params=params)
        response_books_json = response_books.json()
        books = response_books_json['books']
        return render_template("books.html", url="/book/", books=books, amount_pages=1, not_search=not_search)
    return render_template("books.html", url="/book/", books=books, amount_pages=1)


@app.route('/add_book_card/<int:book_id>', methods=["GET", "POST"])
def add_book_card(book_id):
    json = {"user_id": current_user.id, "book_id": book_id}
    requests.post(URL_API + "cart", json=json).json()
    return redirect(f"/book/{book_id}")


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
            login_user(convert_user(response), remember=form.remember_me.data)
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
        user["password_hash"] = hashlib.md5(bytes(form.password.data, encoding='utf-8')).hexdigest()
        response = requests.post(URL_API + "registration", json=registration_request).json()
        status = response["authentication_status"]
        if status == "SUCCESS":
            return redirect('/login')
        return render_template("register.html", form=form, types=types, message=registration_statuses[status])
    return render_template("register.html", form=form, types=types)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run()