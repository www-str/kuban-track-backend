import os
from TwoGis import TwoGis
from YaJS import YaJS
from YaStatic import YaStatic
from dotenv import load_dotenv
from flask import Flask

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('KEY')

twoGis = TwoGis(os.getenv('2GIS_API_KEY'))
YaJS = YaJS(os.getenv('YA_MAPS_JS_API_KEY'))
YaStatic = YaStatic(os.getenv('YA_MAPS_STATIC_API_KEY'))

@app.route('/')
def home():
    return {"home": "not exists"}


@app.route('/api/time')
def get_current_time():
    return {'time': "not a problem"}
