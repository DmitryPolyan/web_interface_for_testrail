from app import db, login
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True)
    password = db.Column(db.String(20))
    role = db.Column(db.String(10))

    def __repr__(self):
        return f'User {self.username}'

    # да, мы специально не хэшируем пароли и храним их в БД в открытом виде
    def check_password(self, password):
        if self.password == password:
            return True


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
