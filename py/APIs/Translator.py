import requests

class Translator(object):
    def translate(self, q, s, t):
        response = requests.post(f"https://translate.flossboxin.org.in/translate?q={q}&source={s}&target={t}&format=text&alternatives=0")

        json = response.json()
        status_code = response.status_code
        if status_code == 200:
            return json["translatedText"]
        else:
            return "error"
