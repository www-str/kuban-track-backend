import os

from datetime import timedelta, datetime, timezone

from data import db_session
from data.users import User
from data.achievements import Achievements
from data.token_blocklist import TokenBlocklist

from APIs.TwoGis import TwoGis

from dotenv import load_dotenv

from flask import Flask, request, Response
from flask_cors import CORS
from flask_jwt_extended import create_access_token, current_user, jwt_required, JWTManager, get_jwt

ACCESS_EXPIRES = timedelta(hours=1)

load_dotenv()
app = Flask(__name__)
CORS(app)
jwt = JWTManager(app)

app.config['SECRET_KEY'] = os.getenv('KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
app.config["JWT_VERIFY_SUB"] = False

@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.before_request
def before_request():
    if request.method.lower() == 'options':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

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

def generate_error_response(message: str) -> Response:
    response = Response()
    response.status_code = 418
    response.data = {"error": message}
    return response

@jwt.expired_token_loader
@jwt.unauthorized_loader
def unauthorized(e):
    return generate_error_response("user not logged in")

@app.route('/api/register', methods=['GET', 'POST'])
def api_register_user():
    args = request.args

    login = args.get('login', None)
    if login is None:
        return generate_error_response("login should be specified")

    password = args.get('password', None)
    if password is None:
        return generate_error_response("password should be specified")

    db_sess = db_session.create_session()

    if db_sess.query(User).filter(User.login == login).first():
        db_sess.close()
        return generate_error_response("login already exists")

    user = User(login=login)
    user.set_password(password)
    db_sess.add(user)
    db_sess.commit()
    return {"ok": "registered"}

@app.route('/api/login', methods=['GET', 'POST'])
def api_login_user():
    args = request.args

    login = args.get('login', None)
    if login is None:
        return generate_error_response("login should be specified")

    password = args.get('password', None)
    if password is None:
        return generate_error_response("password should be specified")

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == login).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=user)
        return {"ok": {"token": access_token}}

    return generate_error_response("no user found or invalid password")

@app.route("/api/logout", methods=['GET', 'POST'])
@jwt_required()
def api_logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db_sess = db_session.create_session()
    db_sess.add(TokenBlocklist(jti=jti, created_at=now))
    db_sess.commit()
    return {"ok": "token revoked"}

@app.route('/api/profile', methods=['GET', 'POST'])
@jwt_required()
def api_user_profile():
    achievements = []
    current_user_object = current_user()
    for i in current_user_object.achievements:
        achievements.append({"id": i.id, "name": i.title, "points": i.points, "description": i.description})
    return {"ok": {"login": current_user_object.login, "points": current_user_object.points, "achievements": achievements}}

@app.route('/api/achievements', methods=['GET', 'POST'])
def api_achievements():
    achievements = []
    db_sess = db_session.create_session()
    for i in db_sess.query(Achievements):
        achievements.append({"id": i.id, "name": i.title, "points": i.points, "description": i.description})
    return {"ok": achievements}


@app.route('/api/earn_achievement', methods=['GET', 'POST'])
@jwt_required()
def api_eran_achievement():
    args = request.args

    achievement_id = args.get('id', None)
    if achievement_id is None:
        return generate_error_response("id should be specified")

    achievement_id = int(achievement_id)

    if achievement_id >= 2147483647:
        return generate_error_response("too big id")

    current_user_object = current_user()

    if current_user_object.achievements.filter(Achievements.id == achievement_id).first() is not None:
        return generate_error_response("user already earned it")

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user_object.id).first()
    achievement = db_sess.query(Achievements).filter(Achievements.id == achievement_id).first()

    if achievement is None:
        db_sess.close()
        return generate_error_response("achievement with requested id does not exist")

    user.achievements.append(achievement)
    user.points += achievement.points
    db_sess.commit()

    return {"ok": "earned"}


@app.route('/api/find_place', methods=['GET', 'POST'])
def api_find_place():
    args = request.args

    city = args.get('city', None)
    if city is None:
        return generate_error_response("city should be specified")

    q = args.get('q', None)
    if q is None:
        return generate_error_response("rubric should be specified")

    region = twoGis.find_region_id(city)
    if region == 0:
        return generate_error_response("Fail to find region")

    result = twoGis.find_places_in_region(q, None, region)

    if result.get("error", None) is not None:
        return generate_error_response(result["error"])

    return result

RUBRICS = ["Казино", "Ресторан", "Отель", "Иподром", "Бары", "Караоке"]

@app.route('/api/get_rubrics', methods=['GET', 'POST'])
def api_get_rubrics():
    return {"ok": RUBRICS}

def main():
    #db_session.global_init(f"sqlite:///db.db")
    db_session.global_init(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
    db_sess = db_session.create_session()
    db_sess.add(Achievements(id=1, title="How it big", points=10, description="Visit this"))
    db_sess.add(Achievements(id=2, title="How it cool", points=10, description="Visit that"))
    db_sess.add(Achievements(id=3, title="How it ok", points=10, description="Visit nor this nor that"))
    db_sess.commit()

if __name__ == '__main__':
    main()
    app.run(host='0.0.0.0', port=8090)

