from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

ALLOWED_TRIES=10
#in the below classes, only User and Guess do not automatically add and commit upon __init__
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


class Guess(db.Model):
  __tablename__ = 'Guess'
  id = db.Column(db.Integer, primary_key=True)
  attempt_id = db.Column(db.Integer, db.ForeignKey('Attempt.id'), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
  #while user_id won't be used here for now, why not have the ability to use this data easily
  number = db.Column(db.Integer, nullable=False)
  bulls = db.Column(db.Integer, nullable=False)
  cows = db.Column(db.Integer, nullable=False)

  def __init__(self, attempt_id, user_id, number, bulls, cows):
    self.attempt_id = attempt_id
    self.user_id = user_id
    self.number = number
    self.bulls = bulls
    self.cows = cows


class Attempt(db.Model):
  __tablename__ = "Attempt"
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
  mysterynumber_id = db.Column(db.Integer, db.ForeignKey('MysteryNumber.id'), nullable=False)
  success = db.Column(db.Boolean, nullable=False, default=False)
  tries = db.Column(db.Integer, nullable=False, default=0)
  guesses = db.relationship('Guess', backref='Guess')
  
  def __init__(self, user, mystery):
    self.user_id = user.id
    self.mysterynumber_id = mystery.id
    # trying to commit here because YO WHY NOT
    db.session.add(self)
    db.session.commit()

  def guess(self, number, user, mystery):
    #before we begin
    if self.tries>=ALLOWED_TRIES or self.success is True:
      return -1 #"Cannot Guess any more for the day"
    #calculating bulls and cows begin
    bulls = 0
    cows = 0
    user_num = [int(x) for x in str(number)]
    mystery_num = [int(x) for x in str(mystery.number)]
    mystery_dict = {}
    for n in mystery_num:
      mystery_dict[n] = True
    for i in range(0,len(mystery_num)):
      if user_num[i]==mystery_num[i]:
        bulls+=1
      elif mystery_dict.get(user_num[i]):
        cows+=1
    #calculating bulls and cows over
    self.tries += 1
    user.num_tries += 1
    mystery.num_tries += 1
    success = number==mystery.number
    if success or self.tries==ALLOWED_TRIES:
      self.success = success
      user.num_attempts += 1
      user.num_success += int(success)
      mystery.num_attempts += 1
      mystery.num_success += int(success)
    # trying to commit here because YO WHY NOT
    db.session.add(self)
    db.session.add(user)
    db.session.add(mystery)
    db.session.add( Guess(self.id,user.id,number,bulls,cows) )
    db.session.commit()
    return int(success) #0="Daily number failed, try again" 1="Daily number successfully guessed!"


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