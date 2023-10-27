from server.functoins import *



app = Flask(  # Create a flask app
	__name__,
	template_folder='templates',  # Name of html file folder
	static_folder='static'  # Name of directory for static files
)
app.secret_key = 'hello'
app.config['SESSION_TYPE'] = 'filesystem'


databaseinit()
csvconvert()

@app.route('/', endpoint='index')  # What happens when the user visits the site
def loginpage():
  return render_template('misc/index.html')

@app.route("/submit", methods=["POST"])
def submit():
  
  entereduser = request.form["username"]
  if usernamecheck(entereduser) or entereduser == 'test':
    session["user_id"] = entereduser
    print(session)
    return redirect(url_for('home'))
  flash('Username not found. Please try again.', 'error')
  return render_template('misc/index.html')

@app.route("/home")
def home():
  username = sessioncheck('user_id')
  print(username)
  if not sessioncheck('user_id'):
    return redirect(url_for('index'))
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Streak, Freezes, Coins, Wager FROM Users WHERE Username = " + "'" + username + "'" #Get Streak, Freezes, Coins, Wager from Users table
  cursor.execute(dbcommand)
  record = cursor.fetchone()
  conn.commit()
  print(record)
  streak, freezes, coins, wager = record #Unpack tuple
  dbcommand = "SELECT DayOfWeek FROM Exercise_Plan WHERE Username = " + "'" + username + "'" #Get DayOfWeek (Workout Date) from Exercise_Plan table
  cursor.execute(dbcommand)
  days = cursor.fetchall()
  conn.commit()
  workdate = [False, False, False, False, False, False, False] #Define workout date array
  for i in range(len(days)):
    item = days[i]
    workdate[item-1] = True #Replace any integer that has been outlined to be true, and thus a workout day.
  dbcommand = "SELECT ServingSize, ServingType, IngredientName FROM Shopping_List WHERE Username = " + "'" + username + "'" #Get ServingSize, ServingType, IngredientName from the shopping list
  cursor.execute(dbcommand)
  record = cursor.fetchall()
  conn.commit()
  ServingSize = []
  IngredientName = []
  ServingType = []
  for i in record:
    SSizeTemp, INameTemp, STypeTemp = i
    ServingSize.append(SSizeTemp)
    IngredientName.append(INameTemp)
    ServingType.append(STypeTemp)
  
  dayarray = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  
  DayOfWeek = date.today().weekday()
  conn.close()
  
  return render_template('misc/home.html', dayarray=dayarray, servingtype=ServingType, coins=coins, streak=streak, freezes=freezes, wager=wager, workdate=workdate, day=DayOfWeek, shoppinging=IngredientName, shoppingquant=ServingSize)
    
@app.route('/signup')
def signup():
  return render_template('misc/signup.html')

@app.route('/signupsubmit', methods=['POST'])
def signupsubmit():
  # Retrieve form data
  print(request.form)
  username = request.form['username']
  injectflag = False
  sex = request.form['dropdown-choice']
  weight = request.form['weight']
  height = request.form['height']
  validflag = False
  for i in ['=', '*', ',', '(', ')', '$',' #', '@', '!', '&', '<', '>', '/', '?', '.']:
    if i in username:
      injectflag = True
      break
  try:
    weight = float(weight)
    if float(weight) < 0: #Ensure weight is positive
      flash('Weight must be a positive number. Please try again.', 'weight')
      validflag = True
  except ValueError:
    flash('Weight must be a positive decimal or integer. Please try again.', 'weight')
    validflag = True
  try:
    height = float(height)
    if height < 0: #Ensure that height is positive
      flash('Height must be a positive decimal or integer. Please try again.', 'height')
  except ValueError:
    flash('Height must be a positive integer. Please try again.', 'height')
    validflag = True
  if usernamecheck(username): #Ensure that the username is not taken
    flash('Username taken. Please enter another username', 'usernametaken')
    validflag = True
  elif injectflag: #Ensure that it's not an SQL injection
    flash("Username cannot contain the following letters: =, *, ',', (, ), $, #, @, !, &, <, >, /, ?, .", 'usernameinvalid')
    validflag = True
  elif sex == 'Invalid':
    flash('Please choose Male or Female.', 'dropdown')
    validflag = True
  if validflag:
    return redirect(url_for('signup'))
  restrictionlist = ['Vegetarian', 'Vegan', 'Celery', 'Crustaceans', 'Eggs', 'Dairy', 'Fish', 'Lupin', 'Milk', 'Molluscs', 'Mustards', 'SoyBeans', 'Peanuts', 'SesameSeeds', 'Gluten', 'Sulphites']
  dietaryrestrictions = [item for item in restrictionlist if request.form.get(item) is not None]
  #All valid. Generate user record. Validation could be optimised. Look into later.
  try:
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    dbcommand = "INSERT INTO Users (Username, Weight, Height, Sex, Streak, Freezes, Coins, Wager) VALUES (?, ?, ?, ?, 0, 0, 0, 0)"
    cursor.execute(dbcommand, (username, weight, height, sex))
    conn.commit()
    dbcommand = "INSERT INTO MealRestrictions (Username, Restriction) VALUES (? ?)"
    for i in dietaryrestrictions:
      cursor.execute(dbcommand, (username, i))
    conn.commit()
  except Exception as e:
    print('a')
    #Error handling
    f = open('static/errorlog.txt', 'w')
    f.write(e)
    f.close()
    return redirect(url_for('index'))
  finally:
    conn.close()
    return redirect(url_for('home'))

@app.route("/settings")
def settings():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]
  return render_template('misc/settings.html', streak=streak, freezes=freezes, coins=coins)

@app.route('/settingssubmit', methods=['POST'])
def settingssubmit():
  # Retrieve form data
  username = sessioncheck('user_id')
  usernamechange = request.form['username']
  injectflag = False
  sex = request.form['dropdown-choice']
  weight = request.form['weight']
  height = request.form['height']
  validflag = False
  for i in ['=', '*', ',', '(', ')', '$',' #', '@', '!', '&', '<', '>', '/', '?', '.']:
    if i in username:
      injectflag = True
      break
  try:
    weight = float(weight)
    if float(weight) < 0: #Ensure weight is positive
      flash('Weight must be a positive number. Please try again.', 'weight')
      validflag = True
  except ValueError:
    flash('Weight must be a positive decimal or integer. Please try again.', 'weight')
    validflag = True
  try:
    height = float(height)
    if height < 0: #Ensure that height is positive
      flash('Height must be a positive decimal or integer. Please try again.', 'height')
  except ValueError:
    flash('Height must be a positive integer. Please try again.', 'height')
    validflag = True
  if usernamecheck(username): #Ensure that the username is not taken
    flash('Username taken. Please enter another username', 'usernametaken')
    validflag = True
  elif injectflag: #Ensure that it's not an SQL injection
    flash("Username cannot contain the following letters: =, *, ',', (, ), $, #, @, !, &, <, >, /, ?, .", 'usernameinvalid')
    validflag = True
  elif sex == 'Invalid':
    flash('Please choose Male or Female.', 'dropdown')
    validflag = True
  if validflag:
    return redirect(url_for('signup'))
  restrictionlist = ['Vegetarian', 'Vegan', 'Celery', 'Crustaceans', 'Eggs', 'Dairy', 'Fish', 'Lupin', 'Milk', 'Molluscs', 'Mustards', 'SoyBeans', 'Peanuts', 'SesameSeeds', 'Gluten', 'Sulphites']
  dietaryrestrictions = [item for item in restrictionlist if request.form.get(item) is not None]
  #All valid. Generate user record. Validation could be optimised. Look into later.
  try:
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    dbcommand = "UPDATE SET Username = ?, Weight = ?, Height = ?, Sex = ? WHERE Username = " + "'" + username + "'"
    cursor.execute(dbcommand, (usernamechange, weight, height, sex))
    conn.commit()
    dbcommand = "UPDATE MealRestrictions SET Username = ?, Restriction = ? WHERE Username = " + "'" + username + "'"
    for i in dietaryrestrictions:
      cursor.execute(dbcommand, (username, i))
    conn.commit()
  except Exception as e:
    print('a')
    #Error handling
    f = open('static/errorlog.txt', 'w')
    f.write(e)
    f.close()
    return redirect(url_for('index'))
  finally:
    conn.close()
    return redirect(url_for('home'))

@app.route("/shop")
def shop():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]


  return render_template('misc/shop.html',streak=streak, freezes=freezes, coins=coins)

@app.route('/shopbuy', methods=['GET'])
def shopbuy():
  username = sessioncheck('user_id')
  results = getuserdata(username)
  dbfreezes = results[5]
  dbcoins = 5000
  dbwager = results[7]
  if 'freeze' in request.args:
    if dbcoins < 200:
      flash("Cannot buy freeze. Not enough coins!")
      return redirect(url_for('shop'))
    else:
      coins = dbcoins-200
      freezes = dbfreezes + 1
      conn = sqlite3.connect('user_data.db')
      cursor = conn.cursor()
      dbcommand = "UPDATE Users SET Coins = ?, Freezes = ? WHERE Username = " + "'" + username + "'"
      cursor.execute(dbcommand, (coins, freezes))
      conn.commit()
      conn.close()
      flash("Freeze bought you know have " + str(freezes) + "freezes!")
      return redirect(url_for('shop'))
  elif 'wager' in request.args:
    wager = request.args['wager']
    print('wager')
    if dbwager != 0:
      flash("You cannot create another wager if you already have one active!")
      return redirect(url_for('shop'))
    elif not wager.isdigit():
      flash("Input must be an integer.")
      return redirect(url_for('shop'))
    elif int(wager) > dbcoins:
      flash("Cannot create wager. Not enough coins!")
      return redirect(url_for('shop'))
    elif int(wager) <= 0:
      flash("Cannot create wager for less than 1 coin!")
      return redirect(url_for('shop'))
    else:
      conn = sqlite3.connect('user_data.db')
      cursor = conn.cursor()
      dbcommand = "UPDATE Users SET Wager = ? WHERE Username = " + "'" + username + "'"
      cursor.execute(dbcommand, (wager))
      conn.commit()
      conn.close()
      flash("Wager set for " + str(wager) + " coins! Good luck!")
      return redirect(url_for('shop'))
  else:
    return redirect(url_for('shop'))

@app.route('/meal')
def meal():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  mealplanarr = []
  for i in range(21):
    i = 'meal' + str(i)
    mealplanarr.append(i)
  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]
  return render_template('meal/meal.html',streak=streak, freezes=freezes, coins=coins, mealplanarr=mealplanarr)

@app.route('/generatemeal')
def generatemeal():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT DietaryRestriction FROM UserRestriction WHERE User = " + "'" + username + "'"
  cursor.execute(dbcommand)
  restrictions = cursor.fetchall()
  tagsarr = [x[0] for x in restrictions]
  for i in tagsarr:
    tag = tagsarr.pop()
    tags = tag + ','
  tags = tags[:-1]
  url = 'https://api.spoonacular.com/recipes/random?number=7'+tags+'dinner'




@app.route('/ingredient')
def ingredient():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]
  ingredientlist=['about frozen cauliflower florets, thawed, cut into bite-sized pieces','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p']
  servinglist=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
  unittypelist=['tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp',]
  return render_template('meal/mealingredients.html',streak=streak, freezes=freezes, coins=coins, ingredientlist=ingredientlist,servinglist=servinglist, unittypelist=unittypelist)

@app.route('/search')
def searchmeal():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]
  return render_template('meal/searchmeal.html',streak=streak, freezes=freezes, coins=coins)

@app.route('/exercise')
def exercise():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  elif not sessioncheck('selectedday'):
    session['selectedday'] = 0
  selectedday = session['selectedday']
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  
  dbcommand = "SELECT Sets, Reps, ExerciseKey ExerciseName FROM Exercise_Plan WHERE DayOfWeek = " + "'" + selectedday + "'"
  cursor.execute(dbcommand)
  SelectDayData = cursor.fetchall()
  conn.commit()
  for i in range(len(SelectDayData)):
    ExerciseKey = SelectDayData[i][2]
    SelectDayData[i][2].pop()
    dbcommand = "SELECT ActivityName FROM Activity WHERE ExerciseKey = " + "'" + ExerciseKey + "'"
    cursor.execute(dbcommand)
    conn.commit()
    Key = cursor.fetchone()
    SelectDayData[i].append(Key[0])
  
  DateToday = date.weekday()
  dbcommand = "SELECT Sets, Reps, ExerciseKey ExerciseName FROM Exercise_Plan WHERE DayOfWeek = " + "'" + DateToday + "'"
  cursor.execute(dbcommand)
  DateTodayData = cursor.fetchall()
  conn.commit()
  for i in range(len(DateTodayData)):
    ExerciseKey = DateTodayData[i][2]
    DateTodayData[i][2].pop()
    dbcommand = "SELECT ActivityName FROM Activity WHERE ExerciseKey = " + "'" + ExerciseKey + "'"
    cursor.execute(dbcommand)
    conn.commit()
    Key = cursor.fetchone()
    DateTodayData[i].append(Key[0])
  workdate=workdatearr(username)
  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]
  return render_template('exercise/exercise.html',streak=streak, freezes=freezes, coins=coins,workdate=workdate, SelectDayData=SelectDayData, DateTodayData=DateTodayData)

@app.route('/exercisedays', methods=['GET'])
def exercisedays():
  for i in range(0, 6):
    if str(i) in request.args:
      selectedday = i
      break
  session['selectedday'] = i
  return redirect(url_for('exercise'))
  
@app.route('/exercisegen')
def exercisegen():
  generateExercise()
  return redirect(url_for('exercise'))

@app.route('/log')
def exerciselog():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]
  return render_template('exercise/exerciselog.html',streak=streak, freezes=freezes, coins=coins)

@app.route('/logsubmit', methods=['POST'])
def logsubmit():
  username = sessioncheck('user_id')
  difficulty = request.form['difficulty']
  weight = request.form['weight']
  diary = request.form['diary']
  try:
    weight = float(weight)
    if float(weight) < 0: #Ensure weight is positive
      flash('Weight must be a positive number. Please try again.')
      return redirect(url_for('log'))
  except ValueError:
    flash('Weight must be a positive decimal or integer. Please try again.')
    return redirect(url_for('log'))
  if not difficulty.isdigit():
    flash('Difficulty must be an integer between 1 and 10!')
    return redirect(url_for('log'))
  elif int(difficulty) > 10 or int(difficulty) < 1:
    flash('Difficulty must be an integer between 1 and 10!')
    return redirect(url_for('log'))
  elif weight.isdigit():
    flash('Weight must be a positive number')
    return redirect(url_for('log'))
  elif int(weight) <0:
    flash('Weight must be a positive number')
    return redirect(url_for('log'))
  elif len(diary) == 0:
    flash('Diary cannot be left blank!')
    return redirect(url_for('log'))
  else:
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    #Needs to update: User's weight, Create new record in UserDiary, Ensure that record hasn't been created already. If no record has been created then add 1 to streak.
    dbcommand = "INSERT INTO UserDiary (UserPK, Date, Diary, WorkoutFelt, PastWeight, Calburned) VALUES (?, ?, ?, ?, ?, ?)"
    cursor.execute(dbcommand, (username, datetime.now().date(), diary, difficulty, weight, None))
    dbcommand = "UPDATE weight WHERE Username = " + "'" + username + "'"
    cursor.execute(dbcommand)
    conn.commit()
    conn.close()
@app.route('/graph')
def exercisegraph():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Weight, WorkoutDifficulty, Date FROM UserDiary WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  conn.commit()
  Data = cursor.fetchall()
  

  results = getuserdata(username)
  streak, freezes, coins = results[4:-1]
  return render_template('exercise/graphscreen.html',streak=streak, freezes=freezes, coins=coins)



if __name__ == "__main__":  # Makes sure this is the main process
  app.run( # Starts the site
    host='0.0.0.0',  # EStablishes the host, required for repl to detect the site
    port=random.randint(2000, 9000),  # Randomly select the port the machine hosts on.
    debug=True
  )
