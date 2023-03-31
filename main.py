#import all the webserver stuff
from flask import Flask, render_template, flash, request, redirect, url_for, session
#from flask_session import Session
#import the sqlite stuff
import sqlite3, os, traceback, sys
from database_functions import *

#set up the app and the ability to session stuff
app = Flask(__name__)
app.secret_key = b'_5#y2L"F0Rkkkk!z\n\xec]/'


UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
  
#when someone goes to /reset in the website...
@app.route('/reset')
#call the function reset_db()
def reset_db():
  #connect to the database
  conn = sqlite3.connect('database.db')
  msg = "Opened database successfully"
  #call function to drop and create the tables
  msg = reset_tables(conn, msg)
  #close the connection to the database
  conn.close()
  #send back to the main flask webserver what it should do. 
  return render_template('reset.html', msg = msg)

#not implemented
@app.route("/login", methods=["GET", "POST"])
def login():
  """Log user in"""
  conn = sqlite3.connect("database.db")
  cur = conn.cursor()
  # Forget any user_id
  session.clear()
  # User reached route via POST (as by submitting a form via POST)
  if request.method == "POST":
      # Ensure username was submitted
      if not request.form.get("username"):
          return apology("must provide username", 403)
      # Ensure password was submitted
      elif not request.form.get("password"):
          return apology("must provide password", 403)
      # Query database for username
      rows = cur.execute("SELECT * FROM users WHERE username = :username",
                        username=request.form.get("username"))
      # Ensure username exists and password is correct
      if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
          return apology("invalid username and/or password", 403)
      # Remember which user has logged in
      session["user_id"] = rows[0]["id"]
      # Redirect user to home page
      return redirect('/')
  # User reached route via GET (as by clicking a link or via redirect)
  else:
      return render_template("login.html")

#Add new questions and tag them from the list or add new tags
@app.route('/enternew')
#call the function new_animal()
def new_question():
  conn = sqlite3.connect("database.db")
  #make a cursor which helps us do all the things
  cur = conn.cursor()
  #execute the insert statement in SQL
  cur.execute("""SELECT tag_text FROM tags""")
  tags = [x[0] for x in cur.fetchall()]
  tags.sort()
  print(tags)
  #go to the add_question.html page
  return render_template('add_question.html', tags = tags)

#when someone goes to the address /addrec on the website 
#they could either be posting or getting (POST, put stuff there, GET, request stuff)
@app.route('/addrec',methods = ['POST'])
#call the function addrec
def addrec():
  #if they POSTed information --> that means they pressed submit on our animal.html page 
    success = False
    success2 = False
    if request.method == 'POST':
      #make an empty message
      
      msg1 = ""
      
      #Storing all the data from the form into a dictionary for use adding to the database
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
        msg1 = f"Question not added tags:{success}, image:{success2}"
      #close th database
      conn.close()
        
      return render_template("result.html",msg = msg1)

#viewing all questions. Can thheoretically add to question cart
@app.route('/list')
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
      qArray = { str(question['qid']) : {
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
      #if 'questions' not in the session yet
      if 'questions' not in session:
        #add it
        session['questions'] = qArray
        print(session['questions'])
        print('added')
        
      #else
      else:
        #if the current question is not in the session variable
        if str(_question_id)  not in session['questions']:
          #add it
          print("made it")
          print('before ', session['questions'])
          print('to add ', qArray)
          session['questions'].update(qArray)
          print('after ', session['questions'])
      #loop through all things in dict to add to the marks
      for key, details in session.get('questions',{}).items():
        print(key,details['marks'] )
        total_questions += 1
        total_marks += details['marks'] 
      session['total_questions'] = total_questions
      session['total_marks'] = total_marks
        
      print(f"num qs: {session.get('total_questions')} tot marks: {session.get('total_marks')} ")
      
      return redirect(url_for('get_list'))
    else:			
      return 'Error while adding item to question bank'
  except Exception as e:
    print(f"exception: {e}")
    return redirect(url_for('get_list'))
  finally:
    cur.close() 
    conn.close()

@app.route('/delquest',methods = ['POST'])
def del_quest():
  print(session['questions'])
  _question_id = request.form['question_id']
  print(_question_id, repr(_question_id))
  if 'questions' in session:
    chosen = session.pop('questions')
    if _question_id in chosen:
      del chosen[_question_id]
      print("#######found and deleted########")
    else:
      print("#######not found########")
    session['questions'] = chosen
  print(session['questions'])
  return redirect(url_for('selected'))
  

@app.route('/selected')
#run the function selected
def selected():
  questions = []
  if "questions" in session:
    print('Yay', session["questions"])
    for key in session["questions"]:
      q_deets = session["questions"][key]
      q_deets.update({"question_id":int(key)})
      q_deets["tags"] =q_deets["tags"].split(";") 
      questions.append(q_deets)
  print(questions)
  return render_template("selected.html",rows = questions)
    
    
@app.route('/filtered')
#not implemented
#run the function filtered
def filtered():
  print("Hello")
  session.clear()
  return(session.get("user", "nup"))
  
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

#not implemented  
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