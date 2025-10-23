import os, sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

UPLOAD_FOLDER = 'static/images'

engine = create_engine('sqlite:///database.db', echo=True)

Base = declarative_base()

class User(Base):
  # This class represents the users table in the database
  __tablename__ = 'users'
  user_id = Column(Integer, primary_key=True)
  username = Column(String, nullable=False)
  email = Column(String, nullable=False, unique=True)  # Added email field
  password_hash = Column(String, nullable=False)
  admin = Column(Boolean, default=False)
  
  def __repr__(self):
    return f"<User(id={self.user_id}, username='{self.username}', admin={self.admin})>"

class Question(Base):
  # This class represents the questions table in the database
  # questions have an id, type, topic and then other pieces depending on the type
  # the type is a string that can be one of the following: "MCQ", "short_answer", "long_answer", "programming", "diagram"
  __tablename__ = 'questions'
  question_id = Column(Integer, primary_key=True, autoincrement=True)
  type = Column(String, nullable=False)
  topic_id = Column(Integer, ForeignKey('topics.topic_id'), nullable=False)
  marks = Column(Integer, nullable=False)
  image = Column(String, nullable=True)
  scenario = Column(Integer, ForeignKey('scenarios.scenario_id'), nullable=True)  # Optional scenario reference
  text = Column(Text, nullable=False)
  answera = Column(Text, nullable=False)
  answerb = Column(Text, nullable=False)
  answerc = Column(Text, nullable=True)
  answerd = Column(Text, nullable=True)
  marking_criteria = Column(Text, nullable=True)
  correct = Column(String, nullable=False)
  source = Column(String, nullable=True)
  created_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)  # Optional user reference
  
  def __repr__(self):
    text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
    return f"<Question(id={self.question_id}, type='{self.type}', topic_id={self.topic_id}, marks={self.marks}, text='{text_preview}')>"

class Scenarios(Base):
  # This class represents the scenarios table in the database
  __tablename__ = 'scenarios'
  scenario_id = Column(Integer, primary_key=True)
  text = Column(Text, nullable=False)
  
  def __repr__(self):
    text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
    return f"<Scenario(id={self.scenario_id}, text='{text_preview}')>"

class Tag(Base):
  # This class represents the tags table in the database
  # tags are used to categorize questions
  __tablename__ = 'tags'
  tag_id = Column(Integer, primary_key=True)
  tag_text = Column(String, nullable=False)
  
  def __repr__(self):
    return f"<Tag(id={self.tag_id}, text='{self.tag_text}')>"

class TagJoin(Base):
  # This class represents the many-to-many relationship between questions and tags
  # It uses a join table to link question_id and tag_id
  __tablename__ = 'tag_join'
  question_id = Column(Integer, ForeignKey('questions.question_id'), primary_key=True)
  tag_id = Column(Integer, ForeignKey('tags.tag_id'), primary_key=True)
  

class Topic(Base):
  # This class represents the topics table in the database
  # topics are used to categorize questions
  __tablename__ = 'topics'
  topic_id = Column(Integer, primary_key=True)
  topic_short_name = Column(String, nullable=False)
  topic_long_name = Column(String, nullable=False)
  
  def __repr__(self):
    return f"<Topic(id={self.topic_id}, short_name='{self.topic_short_name}', long_name='{self.topic_long_name}')>"

def reset_tables(engine):
  # This function resets the database tables by dropping existing ones and creating new ones
  #drop the tables if they exist
  Base.metadata.drop_all(engine)
  #create the tables
  Base.metadata.create_all(engine)

  return "Tables reset successfully"

def login_user(engine, username, password):
  # This function checks if a user exists with the given username and password
  with Session(engine) as session:
    user = session.query(User).filter(User.username == username).first()
    # Return the user object if found and password matches, else None
    if user and check_password_hash(user.password_hash, password):
      return user
    else: 
      return None
  
def register_user(engine, username, email, password, is_admin=False):
  # This function registers a new user in the database
  with Session(engine) as session:
    try:
      # Check if email already exists before attempting to create user
      existing_user = session.query(User).filter(User.email == email).first()
      if existing_user:
        return {"success": False, "error": "email_exists"}
      
      # hash the password and query the database
      password_hash = generate_password_hash(password)
      new_user = User(username=username, email=email, password_hash=password_hash, admin=is_admin)
      session.add(new_user)
      session.commit()
      return {"success": True, "user": new_user}
    except IntegrityError as e:
      session.rollback()
      # Check if the error is specifically about the email constraint
      if "UNIQUE constraint failed: users.email" in str(e):
        return {"success": False, "error": "email_exists"}
      else:
        return {"success": False, "error": f"database_error: {str(e)}"}

def reset_user_password(engine, username, email, new_password):
  # This function resets a user's password if the username and email match
  with Session(engine) as session:
    user = session.query(User).filter(User.username == username, User.email == email).first()
    if user:
      # Update the password hash
      user.password_hash = generate_password_hash(new_password)
      session.commit()
      return {"success": True}
    else:
      return {"success": False, "error": "user_not_found"}

def get_unique_tags(engine):
  with Session(engine) as session:
    # Query to get unique tags from the tags table
    unique_tags = session.query(Tag.tag_text).distinct().all()
    # Convert the result to a list of tag texts
    return [tag[0] for tag in unique_tags]

def get_topics(engine):
  with Session(engine) as session:
    # Query to get all topics from the topics table
    topics = session.query(Topic).all()
    # Convert the result to a list of dictionaries
    return [{"topic_id": topic.topic_id, "topic_short_name": topic.topic_short_name, "topic_long_name": topic.topic_long_name} for topic in topics] 


def add_mc_question(engine, data, user_id):
  with Session(engine) as session:
    #if scenario is provided, fetch the scenario_id or create a new scenario
    if "scenario" in data and data["scenario"]:
      scenario = session.query(Scenarios).filter(Scenarios.text == data["scenario"]).first()
      if not scenario:
        scenario = Scenarios(text=data["scenario"])
        session.add(scenario)
        session.commit()
      scenario_id = scenario.scenario_id
    else:
      scenario_id = None
    question = Question(
      type="MCQ",
      topic_id=data["topic_id"],
      marks=data["marks"],
      scenario=scenario_id,
      text=data["text"],
      answera=data["ansA"],
      answerb=data["ansB"],
      answerc=data.get("ansC", None),
      answerd=data.get("ansD", None),
      marking_criteria=data.get("markingcrit", None),
      correct=data["correct"],
      source=data.get("source", None),  # Optional source field
      created_by=user_id  
    )
    session.add(question)
    session.commit()
    return question.question_id


def add_question_tag_links (engine, ids, question_id):
  with Session(engine) as session:
    for tag_id in ids:
      tag_join = TagJoin(question_id=question_id, tag_id=tag_id)
      session.add(tag_join)
    session.commit()
    return True

    
def add_image (app, engine, file, image_type, question_id):    

  #save the image to the static/images folder
  if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
  #create the filename
  if image_type == "question":
    filename = f"Q{question_id}.{file.filename.rsplit('.', 1)[1].lower()}"
  elif image_type == "answer":
    filename = f"A{question_id}.{file.filename.rsplit('.', 1)[1].lower()}"
  else:
    filename = f"Q{question_id}_A{image_type}.{file.filename.rsplit('.', 1)[1].lower()}"
  #save the file to the path
  path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  file.save(path)
  #update the database with the path
  with Session(engine) as session:
    question = session.query(Question).filter(Question.question_id == question_id).first()
    if question:
      question.image = path
      session.commit()
      return True
    else:
      print("Question not found")
      return False
  


def get_questions(engine, filters=[]):
  # This function retrieves all questions from the database, optionally filtered by text
  with Session(engine) as session:
    # Join with Topic and Tag tables via TagJoin, and concatenate tags
    query = session.query(
      Question,
      Topic,
      func.group_concat(Tag.tag_text, ';').label('tags')
    ).join(Topic, Question.topic_id == Topic.topic_id
    ).outerjoin(TagJoin, Question.question_id == TagJoin.question_id
    ).outerjoin(Tag, TagJoin.tag_id == Tag.tag_id
    ).group_by(Question.question_id, Topic.topic_id)
    
    #apply filters if any
    if filters:
      for filter in filters:
        query = query.filter(Question.text.ilike(f"%{filter}%"))
    
    return query.all()
    


def get_question(engine, q_id):

  # This function retrieves a specific question by its ID, along with its topic and tags
  with Session(engine) as session:
    question = session.query(
      Question,
      Topic,
      func.group_concat(Tag.tag_text, ';').label('tags')
    ).join(Topic, Question.topic_id == Topic.topic_id
    ).outerjoin(TagJoin, Question.question_id == TagJoin.question_id
    ).outerjoin(Tag, TagJoin.tag_id == Tag.tag_id
    ).filter(Question.question_id == q_id
    ).group_by(Question.question_id, Topic.topic_id).first()
    
    return question
  
  

if __name__ == "__main__":
  #testing functions
  engine = create_engine('sqlite:///database.db', echo=True)
  
  # # Create tables first
  # print("Creating tables...")
  # reset_result = reset_tables(engine)
  # # print(reset_result)
  # #add topics
  # print("Adding sample topics...")
  # sample_topics = [
  #   {"topic_short_name": "development", "topic_long_name": "Software development"},
  #   {"topic_short_name": "algorithms", "topic_long_name": "Designing algorithms"},
  #   {"topic_short_name": "data", "topic_long_name": "Data for software engineering"},
  #   {"topic_short_name": "programming", "topic_long_name": "Developing solutions with code"},
  #   {"topic_short_name": "mechatronics hardware/software", "topic_long_name": "Understanding mechatronic hardware and software"},
  #   {"topic_short_name": "control algorithms", "topic_long_name": "Designing control algorithms"},
  #   {"topic_short_name": "building mechatronics", "topic_long_name": "Programming and building mechatronic systems"},
  #   {"topic_short_name": "oop", "topic_long_name": "Understanding OOP"},
  #   {"topic_short_name": "programming oop", "topic_long_name": "Programming in OOP"},
  #   {"topic_short_name": "transmission", "topic_long_name": "Data transmission using the web"},
  #   {"topic_short_name": "designing web apps", "topic_long_name": "Designing web applications"},
  #   {"topic_short_name": "designing secure", "topic_long_name": "Designing secure software"},
  #   {"topic_short_name": "developing secure code", "topic_long_name": "Developing secure code"},
  #   {"topic_short_name": "paradigms", "topic_long_name": "Impact of safe and secure software development"},
  #   {"topic_short_name": "ML Algorithms", "topic_long_name": "Algorithms in machine learning"},
  #   {"topic_short_name": "programming automation", "topic_long_name": "Programming for automation"},
  #   {"topic_short_name": "ml ai impact", "topic_long_name": "Significance and impact of ML and AI"},
  #   {"topic_short_name": "identifying defining", "topic_long_name": "Identifying and defining projects"},
  #   {"topic_short_name": "research planning", "topic_long_name": "Research and planning projects"},
  #   {"topic_short_name": "producing implementing", "topic_long_name": "Producing and implementing projects"},
  #   {"topic_short_name": "testing evaluating", "topic_long_name": "Testing and evaluating software solutions"}
  # ]
  # with Session(engine) as session:
  #   for topic in sample_topics:
  #     new_topic = Topic(topic_short_name=topic["topic_short_name"], topic_long_name=topic["topic_long_name"])
  #     session.add(new_topic)
  #   session.commit()
  # # print("Sample topics added.")
  # #add tags
  # print("Adding sample tags...")
  # sample_tags = ["python", "project management", "sql", "social and ethical issues", "data structures", "algorithms"]
  # with Session(engine) as session:
  #   for tag_text in sample_tags:
  #     new_tag = Tag(tag_text=tag_text)
  #     session.add(new_tag)
  #   session.commit()
  # print("Sample tags added.")
  # #add users
  # print("Adding sample users...")
  # sample_users = [
  #   {"username": "admin", "password_hash": "hashed_admin_password", "admin": True},
  #   {"username": "user1", "password_hash": "hashed_user1_password", "admin": False}
  # ]
  # with Session(engine) as session:
  #   for user in sample_users:
  #     new_user = User(username=user["username"], password_hash=user["password_hash"], admin=user["admin"])
  #     session.add(new_user)
  #   session.commit()
  # # print("Sample users added.")



  # #add questions
  # # print("Adding sample question...")

  # sample_question = {
  #   "question_type": "MCQ",
  #   "topic_id": 11,  # Assuming topic_id 1 exists
  #   "marks": 1,
  #   "text": "In the context of a web application, what is the main role of client-side programming?",
  #   "ansA": "Managing server databases and application logic.",
  #   "ansB": "Handling user interactions and dynamic content display in the browser.",
  #   "ansC": "Storing persistent data and authenticating users on the server.",
  #   "ansD": "Processing requests and returning responses to the web server.",
  #   "markingcrit": "Correct answer is Handling user interactions and dynamic content.",
  #   "correct": "B",
  #   "source": "ITE Trial 2025"
  # }
  # question_id = add_mc_question(engine, sample_question, 1)
  # print(f"Sample question added with ID: {question_id}")


  # # Test get_questions (should return empty list since no data yet)
  # print("Testing get_questions...")
  # out = get_questions(engine)
  # print(f"Questions found: {len(out)}")
  # print(out)

  # delete all users
  # with Session(engine) as session:
  #     session.query(User).delete()
  #     session.commit()

  # test login
  # print("Testing login_user...")
  # user = login_user(engine, "hogesonline", "password")
  # if user:
  #     print(f"Login successful for user: {user.username}")
  # else:
  #     print("Login failed.")
