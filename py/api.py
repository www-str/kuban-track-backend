import os

from datetime import timedelta, datetime, timezone

from data import db_session
from data.users import User
from data.achievements import Achievements
from data.token_blocklist import TokenBlocklist

from APIs.TwoGis import TwoGis

from dotenv import load_dotenv

from flask import Flask, request
from flask_jwt_extended import create_access_token, current_user, jwt_required, JWTManager, get_jwt
from flask_cors import CORS

ACCESS_EXPIRES = timedelta(hours=1)

load_dotenv()
app = Flask(__name__)


app.config['SECRET_KEY'] = os.getenv('KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES

jwt = JWTManager(app)

cors = CORS(app)

twoGis = TwoGis(os.getenv('2GIS_API_KEY'))

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    db_sess = db_session.create_session()
    return db_sess.query(User).filter_by(id=identity).one_or_none

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    db_sess = db_session.create_session()
    token = db_sess.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None

@jwt.unauthorized_loader
def unauthorized(e):
    return {"error": "user not logged in"}

@jwt.expired_token_loader
def unauthorized(e):
    return {"error": "user not logged in"}

@app.route('/')
def home():
    return {"home": "not exists"}

@app.route('/api/register')
def api_register_user():
    args = request.args

    login = args.get('login', None)
    if login is None:
        return {"error": "login should be specified"}

    password = args.get('password', None)
    if password is None:
        return {"error": "password should be specified"}

    db_sess = db_session.create_session()

    if db_sess.query(User).filter(User.login == login).first():
        db_sess.close()
        return {"error": "login already exists"}

    user = User(login=login)
    user.set_password(password)
    db_sess.add(user)
    db_sess.commit()
    return {"ok": "registered"}


@app.route('/api/login')
def api_login_user():
    args = request.args

    login = args.get('login', None)
    if login is None:
        return {"error": "login should be specified"}

    password = args.get('password', None)
    if password is None:
        return {"error": "password should be specified"}

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == login).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=user)
        return {"ok": {"token": access_token}}

    return {"error": "no user found or invalid password"}

@app.route("/api/logout")
@jwt_required()
def api_logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db_sess = db_session.create_session()
    db_sess.add(TokenBlocklist(jti=jti, created_at=now))
    db_sess.commit()
    return {"ok": "token revoked"}

@app.route('/api/profile')
@jwt_required()
def api_user_profile():
    achievements = []

    for i in current_user.achievements:
        achievements.append({"id": i.id, "name": i.title, "points": i.points, "description": i.description})
    return {"ok": {"login": current_user.login, "points": current_user.points, "achievements": achievements}}

@app.route('/api/achievements')
def api_achievements():
    achievements = []
    db_sess = db_session.create_session()
    for i in db_sess.query(Achievements):
        achievements.append({"id": i.id, "name": i.title, "points": i.points, "description": i.description})
    return {"ok": achievements}


@app.route('/api/eran_achievement')
@jwt_required()
def api_eran_achievement():
    args = request.args

    achievement_id = args.get('id', None)
    if achievement_id is None:
        return {"error": "id should be specified"}

    if current_user.achievements.filter(Achievements.id == achievement_id).first() is not None:
        return {"error": "user already earned it"}

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    achievement = db_sess.query(Achievements).filter(Achievements.id == achievement_id).first()

    if achievement is None:
        db_sess.close()
        return {"error": "achievement with requested id does not exist"}

    user.achievements.append(achievement)
    user.points += achievement.points
    db_sess.commit()

    return {"ok": "earned"}


@app.route('/api/find_place')
def api_find_place():
    args = request.args

    city = args.get('city', None)
    if city is None:
        return {"error": "city should be specified"}

    q = args.get('q', None)
    if q is None:
        return {"error": "rubric should be specified"}

    region = twoGis.find_region_id(city)
    if region == 0:
        return {"error": "Fail to find region"}

    return twoGis.find_places_in_region(q, None, region)

RUBRICS = ["Казино", "Ресторан", "Отель", "Иподром", "Бары", "Караоке"]

@app.route('/api/get_rubrics')
def api_get_rubrics():
    return {"ok": RUBRICS}

def main():
    db_session.global_init("sqlite:///db.db")

main()