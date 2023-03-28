import os, sqlite3
UPLOAD_FOLDER = 'static/images'

 
def reset_tables(conn, msg):
  try:
    with conn:
      #drop the tables
      
      conn.execute("DROP TABLE if exists questions;")
      conn.execute("DROP TABLE if exists tag_join;")
      conn.execute("DROP TABLE if exists tags;")
      conn.execute("DROP TABLE if exists users;")
      
      #create the table called animals withe the defined fields
      conn.execute('CREATE TABLE users(user_id INTEGER PRIMARY KEY, username, password_hash, admin);')
      conn.execute('CREATE TABLE questions(question_id INTEGER PRIMARY KEY AUTOINCREMENT, type, topic, marks INTEGER, image, text, answera, answerb, answerc, answerd, marking_criteria, correct);')
      conn.execute('CREATE TABLE tags(tag_id INTEGER PRIMARY KEY, tag_text);')
      conn.execute('CREATE TABLE tag_join(question_id INTEGER, tag_id INTEGER FOREIGN KEY(question_id) REFERENCES questions(question_id) INTEGER FOREIGN KEY(tag_id) REFERENCES tags(tag_id));')
      conn.commit()
      #add to the message with "Table created successfully"
      #the <br/> renders as a new line in HTML
      msg = msg+ "<br\>Tables created successfully"
  except:
    msg = msg+"<br\>Things went wrong with the tables"
  return msg


def get_unique_tags(conn, cur, add_tags, tags):
  add_tags = add_tags + tags
  logfile = open("logfile.txt", "w")
  tags_to_add = []
  try:
    # con.rollback() is called after the with block finishes with an exception,
    # the exception is still raised and must be caught
    with conn:
        for tag in add_tags:
          cur.execute("""SELECT tag_id FROM tags WHERE tag_text=?;""",(tag, ))
          result = cur.fetchone()
          if not result:
            # Record doesn't exists
            #add to tags
            cur.execute("""INSERT INTO tags (tag_text) VALUES (?);""", (tag, ))
            tag_id = cur.lastrowid
          
            tags_to_add.append(tag_id)
          else:
            tags_to_add.append(result[0])
  except Exception as e:
    print("well, something went wrong.")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    file.write( "\n".join("!! " + line for line in lines))
    file.write("\n")
    tags_to_add = []
    logfile.close()
  finally:
    return tags_to_add

def add_question(conn, cur, data):
  question_id = None
  try:
    with conn:
      cur.execute("""INSERT INTO questions (type, topic, marks, text, answera, answerb, answerc, answerd, marking_criteria, correct) VALUES(?,?,?,?,?,?,?,?,?,?);""", (data["question_type"], data["topic"], data["marks"],  data["text"], data["ansA"], data["ansB"], data["ansC"], data["ansD"], data["markingcrit"], data["correct"]))
      #dealing with images - need them to have the Question_num as an image name
      question_id = cur.lastrowid
  except:
    print("stuff broke")
  return question_id

def add_question_tag_links (conn, cur, ids, question_id):
  try:
    with conn:
      for tag_id in ids:
        cur.execute("""INSERT INTO tag_join (question_id, tag_id) VALUES(?,?);""", (question_id, tag_id))
      return True  
  except:
    print("things go wrong")
    return False
    
def add_image (app, conn, cur, file, image_type, question_id):        
  filename = f"Q{question_id}.{file.filename.rsplit('.', 1)[1].lower()}"
  path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  file.save(path)
  try:
    with conn:
      #save the database change
      cur.execute(f"""UPDATE questions SET image = '{path}' WHERE question_id = {question_id}""")
      return True
  except:
    print("image not inserted")
    return False

def get_questions(conn, cur, filters=[]):
  
  with conn:
    if not filters:
      cur.execute('''SELECT 
                    q.question_id, 
                    type, 
                    topic, 
                    CASE
                      WHEN topic="social_ethical" THEN "Social and ethical issues"
                      WHEN topic="hardware_software" THEN "Hardware and software"
                      WHEN topic="sda" THEN "Software development approaches"
                      WHEN topic="dppd" THEN "Defining and understanding the problem, and planning and designing software solutions"
                      WHEN topic="implementing" THEN "Implementing software solutions"
                      WHEN topic="testing" THEN "Testing and evaluating software solutions"
                      WHEN topic="maintaining" THEN "Maintaining software solutions"
                      WHEN topic="developing_solutions" THEN "Developing Software Solutions"
                      WHEN topic="application_sda" THEN "Application of software development approaches"
                      WHEN topic="defining" THEN "Defining and understanding the problem"
                      WHEN topic="planning" THEN "Planning and designing software solutions"
                      WHEN topic="implementing" THEN "Implementation of software solution"
                      WHEN topic="developing_package" THEN "Developing a Solution Package"
                      WHEN topic="paradigms" THEN "Programming Paradigms"
                      WHEN topic="interrelationship" THEN "The interrelationship between software and hardware"
                    END AS topic_long, 
                    marks, 
                    image, 
                    text, 
                    answera, 
                    answerb, 
                    answerc, 
                    answerd, 
                    marking_criteria, 
                    correct, 
                    GROUP_CONCAT(tag_text,";") tags FROM questions q
LEFT JOIN tag_join tj ON q.question_id = tj.question_id INNER JOIN tags t ON tj.tag_id = t.tag_id 
                    GROUP BY  
                    q.question_id, 
                    type, 
                    topic, 
                    marks, 
                    image, 
                    text, 
                    answera, 
                    answerb, 
                    answerc, 
                    answerd, 
                    marking_criteria, 
                    correct;''')
      #fetch all the records 
      questions = cur.fetchall();
      print(questions[0]["text"])
    #need to add the ability to filter
  return questions 

def get_question(conn, cursor, q_id):
  with conn:
    cursor.execute('''SELECT 
                    q.question_id qid, 
                    type, 
                    topic, 
                    CASE
                      WHEN topic="social_ethical" THEN "Social and ethical issues"
                      WHEN topic="hardware_software" THEN "Hardware and software"
                      WHEN topic="sda" THEN "Software development approaches"
                      WHEN topic="dppd" THEN "Defining and understanding the problem, and planning and designing software solutions"
                      WHEN topic="implementing" THEN "Implementing software solutions"
                      WHEN topic="testing" THEN "Testing and evaluating software solutions"
                      WHEN topic="maintaining" THEN "Maintaining software solutions"
                      WHEN topic="developing_solutions" THEN "Developing Software Solutions"
                      WHEN topic="application_sda" THEN "Application of software development approaches"
                      WHEN topic="defining" THEN "Defining and understanding the problem"
                      WHEN topic="planning" THEN "Planning and designing software solutions"
                      WHEN topic="implementing" THEN "Implementation of software solution"
                      WHEN topic="developing_package" THEN "Developing a Solution Package"
                      WHEN topic="paradigms" THEN "Programming Paradigms"
                      WHEN topic="interrelationship" THEN "The interrelationship between software and hardware"
                    END AS topic_long, 
                    marks, 
                    image, 
                    text, 
                    answera, 
                    answerb, 
                    answerc, 
                    answerd, 
                    marking_criteria, 
                    correct, 
                    GROUP_CONCAT(tag_text,";") tags FROM questions q
LEFT JOIN tag_join tj ON q.question_id = tj.question_id INNER JOIN tags t ON tj.tag_id = t.tag_id 
                    WHERE
                    q.question_id = ?
                    GROUP BY  
                    q.question_id, 
                    type, 
                    topic, 
                    marks, 
                    image, 
                    text, 
                    answera, 
                    answerb, 
                    answerc, 
                    answerd, 
                    marking_criteria, 
                    correct;''', (q_id,))
    question = cursor.fetchone()
    return question