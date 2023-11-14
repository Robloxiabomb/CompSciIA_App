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
    return redirect(url_for('home'))
  flash('Username not found. Please try again.', 'error')
  return render_template('misc/index.html')

@app.route("/home")
def home():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    return redirect(url_for('index'))
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Streak, Freezes, Coins, Wager FROM Users WHERE Username = " + "'" + username + "'" #Get Streak, Freezes, Coins, Wager from Users table
  cursor.execute(dbcommand)
  record = cursor.fetchone()
  conn.commit()
  streak, freezes, coins, wager = record #Unpack tuple
  dbcommand = "SELECT DayOfWeek FROM Exercise_Plan WHERE Username = " + "'" + username + "'" #Get DayOfWeek (Workout Date) from Exercise_Plan table
  cursor.execute(dbcommand)
  days = list(set(cursor.fetchall()))
  print(days)
  conn.commit()
  workdate=workdatearr(username)
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
  DayOfWeek = datetime.date.today().weekday()
  conn.close()
  
  return render_template('misc/home.html', dayarray=dayarray, servingtype=ServingType, coins=coins, streak=streak, freezes=freezes, wager=wager, workdate=workdate, day=DayOfWeek, shoppinging=IngredientName, shoppingquant=ServingSize)
    
@app.route('/signup')
def signup():
  return render_template('misc/signup.html')

@app.route('/signupsubmit', methods=['POST'])
def signupsubmit():
  # Retrieve form data
  username = request.form['username']
  injectflag = False
  sex = request.form['dropdown-choice']
  weight = request.form['weight']
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
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "INSERT INTO Users (Username, Weight, Sex, Streak, Freezes, Coins, Wager) VALUES (?, ?, ?, 0, 0, 0, 0)"
  cursor.execute(dbcommand, (username, weight, sex))
  conn.commit()
  dbcommand = "INSERT INTO MealRestrictions (Username, Restriction) VALUES (? ?)"
  for i in dietaryrestrictions:
    cursor.execute(dbcommand, (username, i))
  conn.commit()
  return redirect(url_for('index'))

@app.route("/settings")
def settings():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[3:-1]
  return render_template('misc/settings.html', streak=streak, freezes=freezes, coins=coins)

@app.route('/settingssubmit', methods=['POST'])
def settingssubmit():
  # Retrieve form data
  username = sessioncheck('user_id')
  usernamechange = request.form['username']
  injectflag = False
  sex = request.form['dropdown-choice']
  weight = request.form['weight']
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
    dbcommand = "UPDATE SET Username = ?, Weight = ?, Sex = ? WHERE Username = " + "'" + username + "'"
    cursor.execute(dbcommand, (usernamechange, weight, sex))
    conn.commit()
    dbcommand = "UPDATE MealRestrictions SET Username = ?, Restriction = ? WHERE Username = " + "'" + username + "'"
    for i in dietaryrestrictions:
      cursor.execute(dbcommand, (username, i))
    conn.commit()
  except Exception as e:
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
  streak, freezes, coins = results[3:-1]


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
  

  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Date, MealTypes, MealName FROM Meals WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  MealPlanData = cursor.fetchall()
  
  mealplanarr = [x[2] for x in MealPlanData]
  results = getuserdata(username)

  streak, freezes, coins = results[3:-1]
  return render_template('meal/meal.html',streak=streak, freezes=freezes, coins=coins, mealplanarr=mealplanarr)

@app.route('/generatemeal')
def generatemeal() :
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Restriction FROM MealRestrictions WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  restrictions = cursor.fetchall()
  CheckboxData = []
  for i in range(21):
    CheckboxData.append(request.args.get(str(i)))
  print(CheckboxData)

  tagsarr = [x[0] for x in restrictions]
  tags = ','
  for i in tagsarr:
    tag = tagsarr.pop()
    tags = tags + ',' + tag 

  api_key="d35c0fc0abd64e91b6c3c0cb305de419"
  URL = 'https://api.spoonacular.com/mealplanner/generate?timeFrame=week&apiKey=' + api_key + '&tags=' + tags

  response = requests.get(URL).json()
  NameList, IDList = mealIngredientAPIHandler(response)
  NameGroupedList = []
  IDGroupedList = []
  for i in range(len(NameList)):
    if i%3 == 0: 
      NameGroupedList.append([])
      TempIndex = i
      NameGroupedList[int(TempIndex/3)].append(NameList[i])
    else:
      NameGroupedList[int(TempIndex/3)].append(NameList[i])
  for i in range(len(IDList)):
    if i%3 == 0: 
      IDGroupedList.append([])
      TempIndex = i
      IDGroupedList[int(TempIndex/3)].append(IDList[i])
    else:
      IDGroupedList[int(TempIndex/3)].append(IDList[i])
    
  IDList = [[IDList[x], IDList[x+1], IDList[x+2]] for x in range(3, len(IDList)-3)]
  WeekDateToday = datetime.date.today().weekday()
  if WeekDateToday == 6:
    WeekDateToday = 0
  else:
    WeekDateToday += 1
  DateToday = datetime.date.today()
  DatesArray = []
  for i in range(WeekDateToday, 0, -1):
    DatesArray.append(DateToday - datetime.timedelta(days=i))
  for i in range(WeekDateToday, 7):
    DatesArray.append(DateToday + datetime.timedelta(days=i-WeekDateToday))
  for i in range(len(DatesArray)):
    DatesArray[i] = DatesArray[i].strftime('%d-%m-%Y')
  

  
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  MealTypes = ['breakfast', 'lunch', 'dinner']
  dbcommand = "DELETE FROM Meals WHERE Username = ? AND Date = ? AND MealTypes = ?"
  for i in range(len(DatesArray)):
    for j in range(3):
      if CheckboxData[i] == None:
        print(CheckboxData[i])
        cursor.execute(dbcommand, (username, DatesArray[i], MealTypes[j]))
        conn.commit()
  dbcommand = "INSERT INTO Meals (Username, APIMealID, MealTypes, Date, MealName) VALUES (?, ?, ?, ?, ?)"
  for i in range(len(DatesArray)):
    for j in range(len(IDGroupedList[i])):
      if CheckboxData[(i+1)*(j+1) - 1] == None:
        IDItem = IDGroupedList[i][j]
        NameItem = NameGroupedList[i][j]
        cursor.execute(dbcommand, (username, IDItem, MealTypes[j], DatesArray[i], NameItem))
        conn.commit()
  return 'a'

@app.route('/ingredient')
def ingredient():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[3:-1]
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
  streak, freezes, coins = results[3:-1]
  return render_template('meal/searchmeal.html',streak=streak, freezes=freezes, coins=coins)

@app.route('/shoppinglist')
def shoppinglist():
  return render_template('meal/shoppinglist.html')

@app.route('/exercise')
def exercise():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  elif not sessioncheck('selectedday'):
    session['selectedday'] = 1
  SelectedDay = session['selectedday']
  #Returns Selected Day Tuple
  SelectedDayData = GetExerciseDayData(SelectedDay, username)
  #Returns Today's Day Tuple
  DateToday = datetime.date.today().weekday()
  if DateToday == 6:
    DateToday = 1
  else:
    DateToday += 2
  TodayData = GetExerciseDayData(DateToday, username)
  #Set up ordering later through either the command and setting it through asc or through sorting here.
  TodayData = TodayData[1::]
  SelectedDayData = SelectedDayData[1::]
  
  workdate=workdatearr(username)
  results = getuserdata(username)
  streak, freezes, coins = results[3:-1]
  freezes = 200
  return render_template('exercise/exercise.html',streak=streak, freezes=freezes, coins=coins,workdate=workdate, SelectedDayData=SelectedDayData, TodayData=TodayData)

@app.route('/exercisedays', methods=['GET'])
def exercisedays():
  session['selectedday'] = int(request.args['SelectDay'])-1
  return redirect(url_for('exercise'))
  
@app.route('/exercisegen')
def exercisegen():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  elif not sessioncheck('selectedday'):
    return redirect(url_for('exercise'))
  else:
    selectedday = session['selectedday']
  generateExercise(username, selectedday)
  return redirect(url_for('exercise'))

@app.route('/log', endpoint = 'log')
def exerciselog():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  results = getuserdata(username)
  streak, freezes, coins = results[3:-1]
  return render_template('exercise/exerciselog.html',streak=streak, freezes=freezes, coins=coins)

@app.route('/logsubmit', methods=['POST'])
def logsubmit():
  username = sessioncheck('user_id')
  difficulty = request.form['difficulty']
  weight = request.form['weight']
  diary = request.form['diary']
  try:
    weight = float(weight)
    difficulty = float(difficulty)
    if float(weight) < 0: #Ensure weight is positive
      flash('Weight must be a positive number!', 'error')
      return redirect(url_for('log'))
    elif difficulty > 10 or difficulty < 1:
      flash('Difficulty must be a number between 1 and 10', 'error')
      return redirect(url_for('log'))
  except ValueError:
    flash('Weight must be a positive decimal or integer', 'error')
    return redirect(url_for('logsubmit'))
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  #Needs to update: User's weight, Create new record in UserDiary, Ensure that record hasn't been created already. If no record has been created then add 1 to streak.
  dbcommand = "INSERT INTO UserDiary (Username, Date, Diary, Difficulty, PastWeight) VALUES (?, ?, ?, ?, ?)"
  cursor.execute(dbcommand, (username, datetime.now().date(), diary, difficulty, weight))
  dbcommand = "UPDATE Users SET Weight= ? WHERE Username = ?"
  cursor.execute(dbcommand, (weight, username)) 
  conn.commit()
  conn.close()
  return redirect(url_for('exercise'))

@app.route('/graph')
def exercisegraph():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Diary, Date FROM UserDiary WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  DiaryData = cursor.fetchall()
  print(DiaryData)
  dbcommand = "SELECT Difficulty, PastWeight, Date FROM UserDiary WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  GraphData = cursor.fetchall()
  print(GraphData)
  results = getuserdata(username)
  
  streak, freezes, coins = results[3:-1]
  return render_template('exercise/graphscreen.html',streak=streak, freezes=freezes, coins=coins, GraphData=GraphData, DiaryData=DiaryData)

if __name__ == "__main__":  # Makes sure this is the main process
  app.run( # Starts the site
    host='0.0.0.0',
    port=80,
    debug=True
  )