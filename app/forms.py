from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, SelectMultipleField, StringField, PasswordField, widgets, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User
import db_handler


# Реализация чекбокса во FlaskForm
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# Форма для автоизации
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired('Введите имя')])
    password = PasswordField('Пароль', validators=[DataRequired('Введите пароль')])
    remember_me = BooleanField('Запомнить ')
    submit = SubmitField('Войти')


# Форма регистрации новых пользователей
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired('Введите имя')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Пароль', validators=[DataRequired('Введите пароль')])
    password2 = StringField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=['user', 'admin', 'guest'])
    select_user = SelectField('Выберите профиль для редактирования', choices=[1])
    submit = SubmitField('Сохранить')

    def validate_username(self, username):
        """
        Ф-я проверки возможнности исп-я данного имени пользователя
        :param username: Введенное пользователем имя для регистрации
        :return:
        """
        user = User.query.filter_by(username=username.data.lower()).first()
        if user is not None:
            raise ValidationError('Такое имя уже используется')


# Форма глвной страницы
class StartPageForm(FlaskForm):
    # Напрямую из тетреил
    # list_p = testrail_handler.return_projects_dict()
    # Из БД
    list_p = db_handler.get_data(-1)
    list_of_projects = SelectField('Выберите проект', choices=list_p)

    list_s = []
    list_of_suites = SelectField('Выберите набор тестов', choices=list_s)

    choices = []
    list_of_sections = MultiCheckboxField('Выберите группы тестов', choices=choices)
    additional_list_of_section = MultiCheckboxField('', choices=choices)



