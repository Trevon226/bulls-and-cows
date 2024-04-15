from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

ALLOWED_TRIES=3
class User(db.Model):
  __tablename__ = "User"
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(120), nullable=False)
  attempts = db.relationship('Attempt', backref='user') #list of all attempts from every mysterynumber this user tried
  #attributes below can be calculated from attempts but is inefficient
  num_tries = db.Column(db.Integer, nullable=False, default=0)
  num_success = db.Column(db.Integer, nullable=False, default=0)
  num_attempts = db.Column(db.Integer, nullable=False, default=0)

  def __init__(self, username, email, password):
    self.username = username
    self.email = email
    self.set_password(password)
    # trying to commit here because YO WHY NOT
    # db.session.add(self)
    # db.session.commit()
  
  def set_password(self, password):
    self.password = generate_password_hash(password, method='sha256')
  
  def check_password(self, password):
    return check_password_hash(self.password, password)
  
  def __repr__(self):
    return f'<User {self.id}: {self.username}>'
  
  def get_json(self):
    return {
      'id': self.id,
      'username': self.username,
      'email': self.email
    }


class Attempt(db.Model):
  __tablename__ = "Attempt"
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
  mysterynumber_id = db.Column(db.Integer, db.ForeignKey('MysteryNumber.id'), nullable=False)
  success = db.Column(db.Boolean, nullable=False, default=False)
  tries = db.Column(db.Integer, nullable=False)
  
  def __init__(self, user, mystery):
    self.user_id = user.id
    self.mysterynumber_id = mystery.id
    # trying to commit here because YO WHY NOT
    db.session.add(self)
    db.session.commit()

  def guess(self, number, user, mystery):
    bulls = 0
    cows = 0
    if self.tries==ALLOWED_TRIES:
      return
    self.tries += 1
    user.num_tries += 1
    mystery.num_tries += 1
    success = number==mystery.number
    if success or self.tries==ALLOWED_TRIES:
      user.num_attempts += 1
      user.num_success += int(success)
      mystery.num_attempts += 1
      mystery.num_success += int(success)
    # trying to commit here because YO WHY NOT
    db.session.add(self)
    db.session.add(user)
    db.session.add(mystery)
    db.session.commit()
    return {"bulls":bulls, "cows":cows}


class MysteryNumber(db.Model):
  __tablename__ = "MysteryNumber"
  id = db.Column(db.Integer, primary_key=True)
  number = db.Column(db.Integer, nullable=False)
  birthday = db.Column(db.Integer, nullable=False) #treated as date
  attempts = db.relationship('Attempt', backref='MysteryNumber') #list of all attempts from each user on this mysterynumber
  #attributes below can be calculated from attempts but is inefficient
  num_tries = db.Column(db.Integer, nullable=False, default=0)
  num_success = db.Column(db.Integer, nullable=False, default=0)
  num_attempts = db.Column(db.Integer, nullable=False, default=0)

  def __init__(self, number, birthday):
    self.number = number
    self.birthday = birthday
    # trying to commit here because YO WHY NOT
    db.session.add(self)
    db.session.commit()