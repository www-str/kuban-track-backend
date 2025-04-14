import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm, Sequence
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Achievements(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'achievements'

    id = sqlalchemy.Column(sqlalchemy.Integer, Sequence("achievements_seq"), rimary_key=True)

    title = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=True)
    points = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)



