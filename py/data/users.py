import datetime
import sqlalchemy
from sqlalchemy import Sequence
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from typing import List
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship


from .achievements import Achievements

userAchievements = sqlalchemy.Table(
    "userAchievements",
    SqlAlchemyBase.metadata,
    sqlalchemy.Column("users", sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("achievements", sqlalchemy.ForeignKey("achievements.id")),
)

class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, Sequence("users_seq"), primary_key=True)

    login = sqlalchemy.Column(sqlalchemy.String(length=100), index=True, unique=True, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String(length=2000), nullable=False)

    points = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=0)

    achievements: Mapped[List[Achievements]] = relationship(secondary=userAchievements, lazy='dynamic')

    def __repr__(self):
        return f'Имя пользователя: {self.login}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
