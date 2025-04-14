import sqlalchemy

from .db_session import SqlAlchemyBase

class TokenBlocklist(SqlAlchemyBase):
    __tablename__ = 'tokenBlocklist'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    jti = sqlalchemy.Column(sqlalchemy.String(36), nullable=False, index=True)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
