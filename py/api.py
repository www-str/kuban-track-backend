import os
import re

from data import db_session
from data.users import User

from APIs.TwoGis import TwoGis
from APIs.YaJS import YaJS
from APIs.YaStatic import YaStatic

from dotenv import load_dotenv
from flask import Flask, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('KEY')

login_manager = LoginManager()
login_manager.init_app(app)

twoGis = TwoGis(os.getenv('2GIS_API_KEY'))
YaJS = YaJS(os.getenv('YA_MAPS_JS_API_KEY'))
YaStatic = YaStatic(os.getenv('YA_MAPS_STATIC_API_KEY'))

@app.route('/')
def home():
    return {"home": "not exists"}

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return {"error": "user not logged in"}

@app.route('/api/register')
def api_register_user():

    args = request.args
    login = args.get('login')
    password = args.get('password')
    db_sess = db_session.create_session()

    if db_sess.query(User).filter(User.login == login).first():
        return {"error": "login already exists"}

    user = User(login=login)
    user.set_password(password)
    db_sess.add(user)
    db_sess.commit()
    return {"ok": "registered"}


@app.route('/api/login')
def api_login_user():
    args = request.args
    login = args.get('login')
    remember = True if args.get('remember') == 'true' else False
    password = args.get('password')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == login).first()

    if user and user.check_password(password):
        login_user(user, remember=remember)
        return {"ok": "logged in"}

    return {"error": "no user found or invalid password"}

@app.route("/api/logout")
@login_required
def api_logout():
    logout_user()
    return {"ok": "user logged out"}

@app.route('/api/profile')
@login_required
def api_user_profile():
    return {"ok": {"login": current_user.login, "points": current_user.points, "achievements": [{"name": "Palceholder", "points": 0, "description": "Palceholder"}]}}


def main():
    db_session.global_init("sqlite:///db.db")

main()