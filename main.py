#import all the webserver stuff
from flask import Flask, render_template, flash, request, redirect, url_for
#import the sqlite stuff
import sqlite3, os, traceback, sys
from database_functions import *
#from werkzeug.utils import secure_filename
#the name of your app - we'll use this a bunch
app = Flask(__name__)
app.secret_key = 'any random string'
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
#connect to the db

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):     
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

  

  
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



  
#when someone goes to the address /enternew on the website
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

@app.route('/filters')
#run the function get_list
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