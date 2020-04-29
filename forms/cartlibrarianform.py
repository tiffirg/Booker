from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed, FileRequired


class LibrarianForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    author = StringField('Автор', validators=[DataRequired()])
    genre = StringField('Жанр', validators=[DataRequired()])
    barcode = StringField('Штрих-код', validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired()])
    image = FileField()
    submit = SubmitField('Добавить книгу')