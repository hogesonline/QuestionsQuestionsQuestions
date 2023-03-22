#import all the webserver stuff
from flask import Flask, render_template, flash, request, redirect, url_for
#import the sqlite stuff
import sqlite3, os
from werkzeug.utils import secure_filename
#the name of your app - we'll use this a bunch
app = Flask(__name__)
app.secret_key = 'any random string'
UPLOAD_FOLDER = '/images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

#when someone goes to /reset in the website...
@app.route('/reset')
#call the function reset_db()
def reset_db():
  #connect to the database
  conn = sqlite3.connect('database.db')
  #make a message that sayd "Opened the database successfully"
  msg = "Opened database successfully"
  #drop the table called animals -- allows you to change the table called "animals"
  #do this better
  
  conn.execute("DROP TABLE if exists questions;")
  conn.execute("DROP TABLE if exists tag_join;")
  conn.execute("DROP TABLE if exists tags;")
  
  #create the table called animals withe the defined fields
  conn.execute('CREATE TABLE questions(question_id INTEGER PRIMARY KEY AUTOINCREMENT, type, topic, marks INTEGER, image, text, answera, answerb, answerc, answerd, marking_criteria, correct);')
  conn.execute('CREATE TABLE tag_join(question_id INTEGER, tag_id INTEGER);')
  conn.execute('CREATE TABLE tags(tag_id INTEGER PRIMARY KEY, tag_text);')
  #add to the message with "Table created successfully"
  #the <br/> renders as a new line in HTML
  msg = msg+ "<br\>Tables created successfully"
  #close the connection to the database
  conn.close()
  #send back to the main flask webserver what it should do. 
  return render_template('reset.html', msg = msg)



  
#when someone goes to the address /enternew on the website
@app.route('/enternew')
#call the function new_animal()
def new_question():
  #which doesn't do anything but return what the webserver should do
  #go to the animal.html page
  return render_template('add_question.html')

#when someone goes to the address /addrec on the website 
#they could either be posting or getting (POST, put stuff there, GET, request stuff)
@app.route('/addrec',methods = ['POST', 'GET'])
#call the function addrec
def addrec():
  #if they POSTed information --> that means they pressed submit on our animal.html page 
    if request.method == 'POST':
      #make an empty message
      if 'image' not in request.files:
          flash('No file part')
          image = request.files['image']
          path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
          image.save(path)
      msg1 = ""
      #This is tricky, but it's just trapping errors for us. 
      #try means, see if you get to the end of a series of steps and if
      #everything works then we're fine and if it doesn't
      #do the "except" steps and undo everything you did in the try section.
      
      try:
        #assign each of hte pieces of information we receive to a new variable
        #sn is short for scientific name
        question_type = request.form['type']
        print("type "+question_type)
        topic = request.form['topic']
        marks = int(request.form['marks'])
        image = request.form['image']
        text = request.form['text']
        ansA = request.form['ansA']
        ansB = request.form['ansB']
        ansC = request.form['ansC']
        ansD = request.form['ansD']
        correct = request.form['correct']
        markingcrit = request.form['markingcrit']
        #need to add something about tags here.
        #connect to the db
        con = sqlite3.connect("database.db")
        #make a cursor which helps us do all the things
        cur = con.cursor()
        #execute the insert statement in SQL
        cur.execute(f"""INSERT INTO questions (type, topic, marks, image, text, image,  answera, answerb, answerc, answerd, marking_criteria, correct) VALUES(?,?,?,?,?,?,?,?,?,?,?);""", (question_type, topic, marks, path, text, ansA, ansB, ansC, ansD, correct, markingcrit))

        #save the database change
        con.commit()
        #set message to say that it worked
        msg1 = "Question successfully added"
        #close th database
        con.close()
      except:
        #undo the attempted insertion
        con.rollback()
        #close th database
        con.close()
        #set message to say that it didn't work
        msg1 = "error in insert operation"
      
      #regardless of whether it worked or not do this bit
      finally:
        #return what the webserver should do next, 
        #go to the result page with the msg variable as msg
        return render_template("result.html",msg = msg1)
      



        
#when someone goes to the address /list on the website
@app.route('/list')
#run the function get_list
def get_list():
  #connect to the db
  con = sqlite3.connect("database.db")
  #makes us able to reference each field by name
  con.row_factory = sqlite3.Row
  #make a cursor which helps us do all the things
  cur = con.cursor()
  #execute a select on the data in the database
  cur.execute("SELECT type, topic, marks, image, text, answera, answerb, answerc, answerd, marking_criteria, correct FROM questions")
  #fetch all the records 
  rows1 = cur.fetchall(); 
  print(rows1[0]["text"])
  #return what the webserver should do next, 
  #go to the list page with the rows variable as rows
  return render_template("list.html",rows = rows1)

@app.route('/filters')
#run the function get_list
def search():
  
  #connect to the db
  #con = sqlite3.connect("database.db")
  #makes us able to reference each field by name
  #con.row_factory = sqlite3.Row
  #make a cursor which helps us do all the things
  #cur = con.cursor()
  #execute a select on the data in the database
  #cur.execute("select scientific_name, common_name, diet, habitat, vertebrate from animals")
  #fetch all the records 
  #rows1 = cur.fetchall(); 
  #print(rows1[0]["scientific_name"])
  #return what the webserver should do next, 
  #go to the list page with the rows variable as rows
  rows1 = [things, go, here]
  return render_template("filters.html",rows = rows1)


  
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