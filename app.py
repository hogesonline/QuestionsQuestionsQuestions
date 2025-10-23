#import all the webserver stuff
from flask import Flask, render_template, flash, request, redirect, url_for, session
# from flask_talisman import Talisman
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
#import the sqlite stuff
import sqlite3
from functools import wraps
from sqlalchemy import engine as eng
from database_functions import *

#set up the app and the ability to session stuff
app = Flask(__name__)
app.secret_key = "super secret key $%^$%^$"
Session(app)

# Force HTTPS in production - DISABLED for local development
# if not app.debug:
#     Talisman(app, force_https=True)

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

engine = eng.create_engine('sqlite:///database.db')

#check correct filetype
def allowed_file(filename):     
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#writing a wrapper function to check for login -- not applying yet
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function  

def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", top=code, bottom=message), code
  
#when someone goes to /reset in the website...
# login is required to reset the database

@app.route('/reset')
@login_required
#call the function reset_db()
def reset_db():
  msg = reset_tables(engine)
  return render_template('reset.html', msg = msg)

@app.route("/login", methods=["GET", "POST"])
def login():
  """Log user in"""
  # Forget any user_id
  if session.get("user_id") is not None:
      return redirect('/')

  # User reached route via POST (as by submitting a form via POST)
  if request.method == "POST":
      username = request.form.get("username")
      password = request.form.get("password")
      # Ensure username was submitted
      if not username:
          return apology("must provide username", 403)
      # Ensure password was submitted
      elif not password:
          return apology("must provide password", 403)
      # Query database for username - pass plain text password, not hash
      user = login_user(engine, username, password)
      if user is None:
          return apology("invalid username and/or password", 403)
      # Remember which user has logged in
      session["user_id"] = user.user_id
      session["username"] = user.username
      # Redirect user to home page
      return redirect('/')
  # User reached route via GET (as by clicking a link or via redirect)
  else:
      return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
  """Register user"""

  if session.get("user_id") is not None:
      return redirect('/')

  # User reached route via POST (as by submitting a form via POST)
  if request.method == "POST":
      username = request.form.get("username")
      email = request.form.get("email")
      password = request.form.get("password")
      confirm_password = request.form.get("confirm_password")
      # Ensure username was submitted
      if not username:
          return apology("must provide username", 403)
      # Ensure email was submitted
      elif not email:
          return apology("must provide email", 403)
      # Ensure password was submitted
      elif not password:
          return apology("must provide password", 403)
      # Ensure confirm password was submitted
      elif not confirm_password:
          return apology("must provide confirm password", 403)
      # Ensure passwords match
      elif password != confirm_password:
          return apology("passwords must match", 403)
      # Attempt to register user
      result = register_user(engine, username, email, password)
      
      # Check if registration was successful
      if not result["success"]:
          if result["error"] == "email_exists":
              return apology("Email already exists. Please use a different email address.", 403)
          else:
              return apology(f"Registration failed: {result['error']}", 500)

      # Redirect user to login page
      return redirect('/login')
  # User reached route via GET (as by clicking a link or via redirect)
  else:
      return render_template("register.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
  """Forgot password"""
  
  if session.get("user_id") is not None:
      return redirect('/')
  # TODO: Implement email verification for password reset
  # User reached route via POST (as by submitting a form via POST)
  if request.method == "POST":
      email = request.form.get("email")
      uname = request.form.get("username")
      new_password = request.form.get("password")
      confirm_password = request.form.get("confirm_password")
      # Ensure username was submitted
      if not uname:
          return apology("must provide username", 403)
      # Ensure email was submitted
      if not email:
          return apology("must provide email", 403)
      if not new_password:
          return apology("must provide new password", 403)
      if not confirm_password:
          return apology("must provide confirm password", 403)
      if new_password != confirm_password:
          return apology("passwords must match", 403)
      # Attempt to reset password
      result = reset_user_password(engine, uname, email, new_password)
      if not result["success"]:
          return apology(f"Password reset failed: {result['error']}", 500)
      return redirect('/login')
  
  # User reached route via GET (as by clicking a link or via redirect)
  else:
      return render_template("pwd_reset.html")
  
#when someone goes to the address /enternew on the website
@app.route('/enternew')
@login_required
#call the function new_animal()
def new_question():
  #connect to the db
  # get tags
  tags = get_unique_tags(engine)
  # get topics
  topics = get_topics(engine)
  tags.sort()
  print(tags)
  print(topics)
  #go to the add_question.html page
  return render_template('add_question.html', tags = tags, topics=topics)

#when someone goes to the address /addrec on the website 
#they could either be posting or getting (POST, put stuff there, GET, request stuff)
@app.route('/addrec',methods = ['POST'])
#call the function addrec
@login_required
def addrec():
  #if they POSTed information --> that means they pressed submit on our animal.html page 
    success = False
    success2 = False
    if request.method == 'POST':
      #make an empty message
      
      msg1 = ""
      
      #try means, see if you get to the end of a series of steps and if
      #everything works then we're fine and if it doesn't
      #do the "except" steps and undo everything you did in the try section.
      #assign each of the pieces of information we receive to a new variable

      data = {}
      data["question_type"] = request.form['type']
      data["topic"] = request.form['topic']
      data["marks"] = int(request.form['marks'])
      data["text"] = request.form['text']
      data["ansA"] = request.form['ansA']
      data["ansB"] = request.form['ansB']
      data["ansC"] = request.form['ansC']
      data["ansD"] = request.form['ansD']
      data["correct"] = request.form['correct']
      data["markingcrit"] = request.form['markingcrit']
      tags = request.form.getlist('tags')
      add_tags = [tag.strip() for tag in request.form['add_tags'].lower().split(';')]

      #need to add something about tags here.
      #connect to the db
      conn = sqlite3.connect("database.db")
      #make a cursor which helps us do all the things
      cur = conn.cursor()
      #run the function that manages all the tag additions and 
      ids_to_add = get_unique_tags(conn, cur, add_tags, tags)
        
      question_id = add_question(conn, cur, data)

      if ids_to_add and question_id:
        #link question to ids from in bridging table
        success = add_question_tag_links(conn, cur, ids_to_add, question_id)
        if 'image' not in request.files:
            flash('No file part')
        else:
            file = request.files['image']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file')
                success2 = True
            else:
              success2 = add_image(app, conn, cur, file, "question", question_id)
      #set message to say that it worked
      if success and success2:
        msg1 = "Question successfully added"
      else:
        msg1 = f"Question not added s1:{success}, s2:{success2}"
      #close th database
      conn.close()
        
      return render_template("result.html",msg = msg1)

#when someone goes to the address /list on the website
@app.route('/list')
@login_required
#run the function get_list
def get_list():
  conn = sqlite3.connect("database.db")
  conn.row_factory = sqlite3.Row
  #make a cursor which helps us do all the things
  cur = conn.cursor()
  questions = get_questions(conn, cur)
  
    
  #return what the webserver should do next, 
  #go to the list page with the rows variable as rows
  return render_template("list.html",rows = questions)

@app.route('/addquest',methods = ['POST'])
#run the function add_quest
@login_required
def add_quest():
  conn = sqlite3.connect("database.db")
  conn.row_factory = sqlite3.Row
  #make a cursor which helps us do all the things
  cur = conn.cursor()
  try:
    _question_id = int(request.form['question_id'])
    # validate the received values
    if _question_id and request.method == 'POST':
      question = get_question(conn, cur, _question_id)
      qArray = { question['qid'] : {
        'type' : question['type'], 
        'topic' : question['topic'], 
        'topic_long' : question['topic_long'], 
        'marks' : question['marks'],
        'image' : question['image'],
        'text' : question['text'],
        'answera' : question['answera'],
        'answerb' : question['answerb'],
        'answerc' : question['answerc'],
        'answerd' : question['answerd'],
        'marking_criteria' : question['marking_criteria'],
        'correct' : question['correct'],
        'tags' : question['tags']
        }}
      total_questions = 0
      total_marks = 0
      
      session.modified = True
      if 'questions' in session:
        if question['qid'] not in session['questions']:
          session['questions'] = qArray
          total_questions += 1
          total_marks += question['marks']
        else: #loop through all and work out number and marks
          for key, details in session['questions'].items():
            total_questions += 1
            total_marks += details['marks']
          
      else:
        session['questions'] = qArray
        total_questions += 1
        total_marks += question['marks']
      session['total_questions'] = total_questions
      session['total_marks'] = total_marks
      print(f"num qs: {session['total_questions']} tot marks: {session['total_marks']} ")
      
      
      return redirect(url_for('get_list'))
    else:			
      return 'Error while adding item to question bank'
  except Exception as e:
    print(f"exception: {e}")
    return redirect(url_for('get_list'))
  finally:
    cur.close() 
    conn.close()
  
@app.route('/filters')
#run the function get_list
@login_required
def filters():
  conn = sqlite3.connect("database.db")
  #make a cursor which helps us do all the things
  cur = conn.cursor()
  #execute the insert statement in SQL
  cur.execute("""SELECT tag_text FROM tags""")
  tags = [x[0] for x in cur.fetchall()]
  tags.sort()
  #just redirects to the page where you can search for a question after looking up the available tags
  return render_template("filters.html", rows = tags)

@app.route('/filtered')
@login_required
#run the function get_list
def filtered():
  print("Hello")


  
#when someone goes to the address / (i.e. the home page, no extra address)
@app.route('/')
#run the function home
def home():
  #which does nothing
  #but returns what the webserver should do next
  #go to the home page
  return render_template('home.html')




  
#Check that this isn't being run by another module
if __name__ == '__main__':
  #run on the host 0.0.0.0
  app.run(debug = True, host = '0.0.0.0')


#using the animal cards from https://aca.edu.au/resources/decision-trees-animal-trading-cards/