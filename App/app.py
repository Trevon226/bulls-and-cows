import os, csv
import random
import datetime
from json import dumps
from flask import Flask, jsonify, request, redirect, render_template, url_for, flash
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import case, desc
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
    current_user
)
from .models import db, MysteryNumber, User, Attempt

# Configure Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'MySecretKey'
app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=15)
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config['JWT_HEADER_NAME'] = "Cookie"


# Initialize App 
db.init_app(app)
app.app_context().push()
CORS(app)
jwt = JWTManager(app)

def get_gmt_start_of_day(): # could've done research or could've asked gpt cuz python :/
  # Get current date
  current_date = datetime.datetime.now().date()
  # Combine current date with midnight time
  midnight = datetime.datetime.combine(current_date, datetime.time.min)
  # Convert to Unix timestamp
  unix_timestamp = int(midnight.timestamp())
  return unix_timestamp

def get_current_mystery():
  current_mystery=MysteryNumber.query.filter_by(birthday=get_gmt_start_of_day()).first()
  if not current_mystery:
    return MysteryNumber(random.randint(0,9999), get_gmt_start_of_day())
  return current_mystery

def current_user_attempt(current_user):
  current_mystery=get_current_mystery()
  for attempt in current_user.attempts:
    if attempt.mysterynumber_id == current_mystery.id:
      return attempt
  return Attempt(current_user,current_mystery)


# JWT Config to enable current_user
@jwt.user_identity_loader
def user_identity_lookup(user):
  return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
  identity = jwt_data["sub"]
  return User.query.get(identity)

# *************************************

# Initializer Function to be used in both init command and /init route
# Parse pokemon.csv and populate database and creates user "bob" with password "bobpass"
def initialize_db():
  db.drop_all()
  db.create_all()
  bob = User(username='bob', email="bob@mail.com", password="bobpass")
  db.session.add(bob)
  db.session.commit()

# ********** Routes **************

# Template implementation (don't change)

@app.route("/", methods=['GET'])
def login_page():
  return render_template("login.html")

@app.route("/signup", methods=['GET'])
def signup_page():
  return render_template("signup.html")

@app.route("/signup", methods=['POST'])
def signup_action():
  response = None
  try:
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    response = redirect(url_for('home_page'))
    token = create_access_token(identity=user)
    set_access_cookies(response, token)
  except IntegrityError:
    flash('Username already exists')
    response = redirect(url_for('signup_page'))
  flash('Account created')
  return response

@app.route("/logout", methods=['GET'])
@jwt_required()
def logout_action():
  response = redirect(url_for('login_page'))
  unset_jwt_cookies(response)
  flash('Logged out')
  return response

# *************************************

# Page Routes (To Update)
@app.route("/app", methods=['GET'])
@jwt_required()
def home_page(pokemon_id=1):
  current_mystery = get_current_mystery()
  print(current_mystery.number)
  current_attempt = current_user_attempt(current_user)
  return render_template("home.html", current_mystery=current_mystery, current_attempt=current_attempt, user=current_user)

# Action Routes (To Update)

@app.route("/login", methods=['POST'])
def login_action():
  user = User.query.filter_by(username=request.form["username"]).first()
  if not user or not user.check_password(request.form["password"]):
    flash("Incorrect username or password")
    return redirect(url_for('login_action'))
  token = create_access_token(identity=user)
  response = redirect(url_for('home_page'))
  set_access_cookies(response, token)
  flash("Login Successful")
  return response

@app.route("/guess", methods=['POST'])
@jwt_required()
def guess():
  number = int(request.form['number'])
  attempt = current_user_attempt(current_user)
  responses = {
    "-1": "Cannot Guess any more for the day",
    "0": "Daily number failed, try again",
    "1": "Daily number successfully guessed!"
  }
  flash(responses[ str(attempt.guess(number,current_user,get_current_mystery())) ])
  return redirect(url_for('home_page'))

@app.route("/stats/<int:id>", methods=['GET'])
@jwt_required()
def stats(id):
  user = User.query.filter_by(id=id).first()
  if not user:
    return "Forbidden",403
  #users = User.query.order_by(case({User.num_success==0: 0}, else_=User.num_tries / User.num_success)).all()
  users = User.query.order_by(desc(case({User.num_tries==0: 0}, else_=User.num_success/User.num_tries))).all()
  return render_template("stats.html", user=user, users=users, mysterynumber=get_current_mystery())

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8080)
