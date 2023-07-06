import random
import string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from domains import domains as domainlist
import random
import validators
import os
from dotenv import load_dotenv
from googletrans import Translator
from weather import keys as weatherkeys
from captcha.image import ImageCaptcha
from flask import (
    Flask,
    request,
    jsonify,
    redirect,
    render_template,
    send_from_directory,
    Response,
)
import requests


pastebin = os.getenv('pastebin')

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=os.getenv('mongodb'),
    strategy="fixed-window",  # or "moving-window"
)

@app.route('/', methods=["GET"])
def home():
    return jsonify('Hello World!')

@app.route("/email", methods=["GET"])
@limiter.limit("100 per minute")
def check():
    email = request.args.get("email")
    if not email:
        return jsonify({"Error": "Please provide an email."}), 400
    elif email:
        if "@" in email:
            result = False
            data = email.split("@")
            if data[1] in domainlist:
                result = True
            return jsonify({"result": result})
        else:
            return jsonify({"Error": "Please provide a valid email."}), 400


@app.route("/genpass", methods=["GET"])
@limiter.limit("100 per minute")
def genpassword():
    len = request.args.get("length")
    if not len:
        return jsonify({"Error": "Please provide length like 8 or 9."}), 400
    elif len:
        try:
            len = int(len)
            characters = string.ascii_letters + string.digits + string.punctuation
            password = "".join(random.choice(characters) for _ in range(len))
            return jsonify({"Password": password})
        except:
            return jsonify({"Error": "Please provide valid length"}), 400


@app.route("/pastebin", methods=["POST"])
@limiter.limit("10 per minute")
def paste():
    body = request.form.get('content')
    name = request.headers.get("name") or None
    data = {
        "api_option": "paste",
        "api_dev_key": pastebin,
        "api_paste_code": body,
        "api_paste_name": name,
        "api_paste_private": 1,
    }
    response = requests.post("https://pastebin.com/api/api_post.php", data=data)
    if response.status_code == 200:
        return jsonify({"Link": response.text})
    else:
        return jsonify({"Error": "Something went wrong please try again later."}), 408


@app.route("/weather", methods=["GET"])
@limiter.limit("3 per minute")
def weather():
    city = request.args.get("city")
    key = os.getenv('weather')
    if not city:
        return jsonify({"error": "City parameter is missing."}), 400
    url = f"http://api.openweathermap.org/data/2.5/weather?appid={key}&units=metric&q={city}"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        weather_data = {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
        }
        return jsonify(weather_data)
    else:
        return jsonify({"error": "Unable to fetch weather data."}), 500


@app.route("/captcha", methods=["GET"])
@limiter.limit("10 per minute")
def captcha():
    captchacode = request.args.get("captcha")
    if not captchacode:
        return jsonify({"error": "Provide captcha code like: 66Ahd."}), 400
    elif captchacode:
        try:
            captchatext = captchacode
            captcha = ImageCaptcha()
            data = captcha.generate(captchatext)
            image = data.getvalue()
            return Response(image, mimetype="image/png")
        except:
            return jsonify({"Error": "Please provide valid length"}), 400


@app.route("/qrcode", methods=["GET"])
@limiter.limit("100 per minute")
def qrcode():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Provide url"}), 400
    elif url:
        if validators.url(url):
            data = requests.get(
                f"https://chart.googleapis.com/chart?cht=qr&chs=300x300&chl={url}"
            )
            return Response(data.content, mimetype="image/png")
        else:
            return jsonify({"error": "Provide a valid url."}), 400

@app.route("/translate", methods=["POST"])
@limiter.limit("100 per minute")
def translate_text():
    text = request.form['text']
    target_lang = request.form['target_lang']
    translator = Translator()
    translation = translator.translate(text=text, src="auto", dest=target_lang)
    return jsonify({'translation': translation.text})


@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"error": 'page not found'}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="10000")
