from flask import Flask, request, render_template, Response, redirect, jsonify, make_response, g, send_file
from functools import wraps
import requests
import os
import jwt
import json
from urllib.parse import urlparse
from flask_mysqldb import MySQL
from utils.ebayApi import ebay_research
from utils.db import do_login, do_register
from utils.job_scheduler import create_cronjob
from utils.schema_validation import validate_json
from pathlib import Path

search_engines = {
    "api.ebay.com":ebay_research
    # TODO: add more online shops, someday, somehow...
    }

mysql = MySQL()
def init_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config['SECRET_KEY'] = os.environ.get('SECRET', os.urandom(32))
    app.config['MYSQL_HOST'] = os.environ.get('DBHOST', '')
    app.config['MYSQL_USER'] = os.environ.get('DBUSER', '')
    app.config['MYSQL_PASSWORD'] = os.environ.get('DBPASS', '')
    app.config['MYSQL_DB'] = os.environ.get('DBSCHEMA', '')
    with app.app_context():
        mysql.init_app(app)
        g.mysql = mysql.connection.cursor()
        return app
app = init_app()

@app.before_request
def add_mysql():
    if 'mysql' not in g:
        g.mysql = mysql.connection.cursor()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            return redirect("/")
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return redirect("/")
        return  f(data['userid'], *args, **kwargs)
    return decorated

@app.route('/dashboard', methods=['GET'])
@token_required
def dashboard(current_users):
    return render_template('dashboard.html')

@app.route('/schedule_search', methods=['POST'])
@token_required
def schedule_search(current_user):
    schedule_data = request.get_json()
    if not validate_json(schedule_data, "./schemas/scheduled_search.json"):
        return jsonify({"error":"bad request"}), 400

    command = {"cmd":f"python /app/scheduled_search.py {current_user}"}
    if create_cronjob(command | schedule_data):
        return jsonify({"message":"search scheduled"}), 201
    return jsonify({"error":"something went wrong"}), 500

@app.route('/search', methods=['POST'])
@token_required
def search(current_user):
    try:
        data = request.get_json()
        if not validate_json(data, "./schemas/search.json"):
            return jsonify({"error":"bad request"}), 400
        url = urlparse(data['url'])
        search_param = data['search_param']
        search_result = search_engines[url.hostname](url, search_param)
        save_dir = Path(
            "/results",
            f"{current_user}_last_search"
        )
        save_dir.mkdir(parents=True, exist_ok=True)
        if save_dir.is_dir():
            for item in save_dir.iterdir():
                if item.is_file():
                    item.unlink()
        save_file = save_dir / f"{search_result['itemId']}.json"
        with open(save_file, 'w') as file:
            json.dump(search_result, file)
        return jsonify(search_result), 200
    except:
        return jsonify({"error":"something went wrong"}), 500

# login / register
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        user_data = request.get_json()
        if not validate_json(user_data, "./schemas/login.json"):
            return jsonify({"error":"bad request"}), 400

        username, userid = do_login(user_data['username'], user_data['password'])
        if username:
            token = jwt.encode(
                {'username': username, 'userid': userid},
                app.config['SECRET_KEY'])
            response = make_response(jsonify({'token' : token.decode('UTF-8')}), 200)
            response.set_cookie('access_token', token.decode('UTF-8'), httponly = True, samesite='Strict')
            return response
        return jsonify({'error':'wrong credentials'}), 401
    if request.method == "GET":
        return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "POST":
        user_data = request.get_json()
        if not validate_json(user_data, "./schemas/register.json"):
            return jsonify({"error":"bad request"}), 400
        result = do_register(user_data['username'], user_data['password'])
        if result is not None:
            return jsonify({'message' : result[1]}), result[0]
        else:
            return jsonify({'message' : 'something went wrong'}), 500

    if request.method == "GET":            
        return render_template('register.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)