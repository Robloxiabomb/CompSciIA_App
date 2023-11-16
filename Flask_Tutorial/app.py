from server.functions import *



app = Flask(  # Create a flask app
	__name__,
	template_folder='templates',  # Name of html file folder
	static_folder='static',
  static_url_path='/static'  # Name of directory for static files
)
app.secret_key = 'hello'
app.config['SESSION_TYPE'] = 'filesystem'


databaseinit()
csvConvert()

#NOT DONE (NO BUGS)
#NEEED TO FIX SIZING ISSUES WITH CODE
@app.route('/', endpoint='index')  # What happens when the user visits the site
def loginpage():
  return render_template('misc/index.html')


@app.route("/submit", methods=["POST"])
def submit():
  entereduser = request.form["username"]
  if usernamecheck(entereduser):
    session["user_id"] = entereduser
    username = sessioncheck(entereduser)
    UserPK = getUserPK()
    if not StreakCheck(UserPK):
      endStreak(UserPK)
    elif not WagerCheck(UserPK):
      endWager(UserPK)
    return redirect(url_for('home'))
  flash('Username not found. Please try again.', 'error')
  return render_template('misc/index.html')

#NOT DONE
#LOG BUTTON NEEDS TO BE ALIGNED
#CANNOT PLACE MEAL NAMES LIKE THAT WILL RESULT IN UNREADABILITY
#USERNAME ERROR
#DAYOFWEEK EXERCISE PLAN NEEDS TO BE FIXED
@app.route("/home")
def home():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()

  record = getuserdata(UserPK)
  streak, freezes, coins, wager = record[4:8]

  dbcommand = "SELECT DayOfWeek FROM Exercise_Plan WHERE UserPK = " + str(UserPK)#Get DayOfWeek (Workout Date) from Exercise_Plan table
  cursor.execute(dbcommand)
  days = list(set(cursor.fetchall()))
  conn.commit()
  workdate=workDateArrayification(UserPK)
  dbcommand = "SELECT ServingSize, ServingType, IngredientName FROM Shopping_List WHERE UserPK = " + str(UserPK) #Get ServingSize, ServingType, IngredientName from the shopping list
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
  if DayOfWeek == "6":
    DayOfWeek = 0
  else:
    DayOfWeek += 1
  conn.close()
  
  return render_template('misc/home.html', dayarray=dayarray, servingtype=ServingType, coins=coins, streak=streak, freezes=freezes, wager=wager, workdate=workdate, day=DayOfWeek, shoppinging=IngredientName, shoppingquant=ServingSize)

#DONE (FOR NOW NO BUGS)
@app.route('/signup')
def signup():
  return render_template('misc/signup.html')

#DONE (FOR NOW NO BUGS)
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
  #All valid. Generate user record. Validation could be optimised. Look into later.
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "INSERT INTO Users (Username, Weight, Sex, Streak, Freezes, Coins) VALUES (?, ?, ?, 0, 0, 0)"
  cursor.execute(dbcommand, (username, weight, sex))
  conn.commit()

  dbcommand = "SELECT * FROM Users WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  
  session["user_id"] = username
  UserPK = getUserPK()

  dbcommand = "INSERT INTO MealRestrictions (UserPK, Restriction) VALUES (?, ?)"
  restrictionlist = ['Vegetarian', 'Vegan', 'Celery', 'Crustaceans', 'Eggs', 'Dairy', 'Fish', 'Lupin', 'Milk', 'Molluscs', 'Mustards', 'SoyBeans', 'Peanuts', 'SesameSeeds', 'Gluten', 'Sulphites']
  dietaryrestrictions = [item for item in restrictionlist if request.form.get(item) is not None]
  for i in dietaryrestrictions:
    cursor.execute(dbcommand, (UserPK, i))
    conn.commit()
  conn.close()
  return redirect(url_for('index'))

#NOT DONE
#I JUST REALISED IF YOU CHANGED USERNAME FOR SETTINGS IT WON'T UPDATE SESSION SO NOTHING WILL WORK ANYMORE
@app.route("/settings")
def settings():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Restriction FROM MealRestrictions WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  dietaryRestrictionArr = cursor.fetchall()
  conn.commit()
  results = getuserdata(UserPK)
  username, weight, sex, streak, freezes, coins = results[1:7]
  return render_template('misc/settings.html', streak=streak, freezes=freezes, coins=coins, sex=sex, username=username, weight=weight, dietaryRestrictionArr=dietaryRestrictionArr)

#NOT DONE
@app.route('/settingssubmit', methods=['POST'])
def settingssubmit():
  # Retrieve form data
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  usernamechange = request.form['username']
  injectflag = False
  sex = request.form['dropdown-choice']
  weight = request.form['weight']
  validflag = False
  for i in ['=', '*', ',', '(', ')', '$',' #', '@', '!', '&', '<', '>', '/', '?', '.']:
    if i in usernamechange:
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
  if usernamecheck(usernamechange) and username != usernamechange: #Ensure that the username is not taken
    flash('Username taken. Please enter another username', 'usernametaken')
    validflag = True
  elif injectflag: #Ensure that it's not an SQL injection
    flash("Username cannot contain the following letters: =, *, ',', (, ), $, #, @, !, &, <, >, /, ?, .", 'usernameinvalid')
    validflag = True
  elif sex == 'Invalid':
    flash('Please choose Male or Female.', 'dropdown')
    validflag = True
  if validflag:
    return redirect(url_for('settings'))
  restrictionlist = ['Vegetarian', 'Vegan', 'Celery', 'Crustaceans', 'Eggs', 'Dairy', 'Fish', 'Lupin', 'Milk', 'Molluscs', 'Mustards', 'SoyBeans', 'Peanuts', 'SesameSeeds', 'Gluten', 'Sulphites']
  dietaryrestrictions = [item for item in restrictionlist if request.form.get(item) is not None]
  #All valid. Generate user record. Validation could be optimised. Look into later.
  try:
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    dbcommand = f"UPDATE SET Username = ?, Weight = ?, Sex = ? WHERE UserPK = " + str(UserPK) 
    cursor.execute(dbcommand, (usernamechange, weight, sex))
    conn.commit()
    dbcommand = f"UPDATE MealRestrictions SET UserPK = ?, Restriction = ? WHERE UserPK = " + str(UserPK)
    for i in dietaryrestrictions:
      cursor.execute(dbcommand, (UserPK, i))
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

#DONE FOR NOW (NO BUGS)
@app.route("/shop")
def shop():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  results = getuserdata(UserPK)
  streak, freezes, coins = results[4:7]


  return render_template('misc/shop.html',streak=streak, freezes=freezes, coins=coins)

#DONE FOR NOW (NO BUGS)
@app.route('/shopbuy', methods=['GET'])
def shopbuy():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  results = getuserdata(UserPK)
  dbfreezes = results[5]
  dbcoins = 5000
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = f"SELECT Wager FROM WagerInfo WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  dbwager = cursor.fetchone()[0]
  if 'freeze' in request.args:
    if dbcoins < 200:
      flash("Cannot buy freeze. Not enough coins!")
      return redirect(url_for('shop'))
    else:
      coins = dbcoins-200
      freezes = dbfreezes + 1
      dbcommand = f"UPDATE Users SET Coins = ?, Freezes = ? WHERE UserPK = " + str(UserPK) 
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
      dbcommand = "SELECT Streak FROM Users WHERE UserPK = " + str(UserPK)
      cursor.execute(dbcommand)
      Streak = cursor.fetchone()[0]
      dbcommand = "UPDATE WagerInfo SET Wager = ?, WagerDate = ?, StreakAtTimeOfWager = ?, WagerCount = 0  WHERE UserPK = " + str(UserPK)
      TodayDate = datetime.datetime.today().day()
      cursor.execute(dbcommand, (wager, TodayDate, Streak))
      dbcoins -= wager
      dbcommand = "UPDATE Users SET Coins = ? WHERE UserPK = " + str(UserPK)
      cursor.execute(dbcommand, (dbcoins))
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
  UserPK = getUserPK()
  
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = f"SELECT Date, MealTypes, MealName FROM Meals WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  MealPlanData = cursor.fetchall()
  
  mealplanarr = [x[2] for x in MealPlanData]
  results = getuserdata(UserPK)

  streak, freezes, coins = results[4:7]
  return render_template('meal/meal.html',streak=streak, freezes=freezes, coins=coins, mealplanarr=mealplanarr)

@app.route('/generatemeal')
def generatemeal() :
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = f"SELECT Restriction FROM MealRestrictions WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  restrictions = cursor.fetchall()
  CheckboxData = []
  for i in range(21):
    CheckboxData.append(request.args.get(str(i)))

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
    DatesArray[i] = DatesArray[i].strftime('%Y-%m-%d')
  

  
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  MealTypes = ['breakfast', 'lunch', 'dinner']
  dbcommand = "DELETE FROM Meals WHERE UserPK = ? AND Date = ? AND MealTypes = ?"
  for i in range(len(DatesArray)):
    for j in range(3):
      if CheckboxData[i] == None:
        cursor.execute(dbcommand, (UserPK, DatesArray[i], MealTypes[j]))
        conn.commit()
  dbcommand = "INSERT INTO Meals (UserPK, APIMealID, MealTypes, Date, MealName) VALUES (?, ?, ?, ?, ?)"
  for i in range(len(DatesArray)):
    for j in range(len(IDGroupedList[i])):
      if CheckboxData[(i+1)*(j+1) - 1] == None:
        IDItem = IDGroupedList[i][j]
        NameItem = NameGroupedList[i][j]
        cursor.execute(dbcommand, (UserPK, IDItem, MealTypes[j], DatesArray[i], NameItem))
        conn.commit()
  return redirect(url_for('meal'))

@app.route('/ingredient')
def ingredient():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  results = getuserdata(UserPK)
  streak, freezes, coins = results[4:7]
  #GET MEAL NAME FROM FORM DATA (SHOULDN'T NEED TO WORRY ABOUT ID OF MEAL BECAUSE OF THE FACT THAT APIMEALID MAPS TO EVERYTHING)
  #GET API KEY FROM MEAL NAME
  #GET JSON FROM URL
  #GET LIST OF INGREDIENTS, UNIT TYPES, AND THE NUMBER REQUIRED FROM JSON FORMATTED INTO AN ARRAY
  #SEND RENDER TEMPLATE

  ingredientlist=['about frozen cauliflower florets, thawed, cut into bite-sized pieces','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p']
  servinglist=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
  unittypelist=['tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp','tsp', 'tsp',]
  return render_template('meal/mealingredients.html',streak=streak, freezes=freezes, coins=coins, ingredientlist=ingredientlist,servinglist=servinglist, unittypelist=unittypelist)

@app.route('/searchmeal')
def searchmeal():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  results = getuserdata(UserPK)
  streak, freezes, coins = results[4:7]
  return render_template('meal/searchmeal.html',streak=streak, freezes=freezes, coins=coins)

@app.route('/searchmealform', methods=["GET"])
def searchmealform():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  
  # GET FORM DATA FROM SEARCH
  
  # RUN SPOONACULAR API SEARCH (ONLY ALLOWS AUTOCOMPLETE SO INCLUDE THAT IN HTML)
  # DISPLAY EVERY RESPONSE FROM SPOONACULAR
  # IF NO RESPONSES DISPLAY "NO RESPONSES"
  return redirect(url_for('recipenamelist'))
@app.route('/shoppinglist')
def shoppinglist():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  
  #GET INGREDIENTNAME, SERVINGSIZE, SERVINGTYPE FROM SHOPPING_LIST TABLE
  #FORMAT IT INTO ARRAY
  #SEND IT THROUGH SHOPPINGLIST HTML
  results = getuserdata(UserPK)
  streak, freezes, coins = results[4:7]
  return render_template('meal/shoppinglist.html',streak=streak, freezes=freezes, coins=coins)

@app.route('/exercise')
def exercise():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
  elif not sessioncheck('selectedday'):
    session['selectedday'] = 1
  UserPK = getUserPK()
  SelectedDay = session['selectedday']
  #Returns Selected Day Tuple
  SelectedDayData = getExerciseDayData(SelectedDay, UserPK)
  #Returns Today's Day Tuple
  DateToday = datetime.date.today().weekday()
  if DateToday == 6:
    DateToday = 1
  else:
    DateToday += 2
  TodayData = getExerciseDayData(DateToday, UserPK)
  #Set up ordering later through either the command and setting it through asc or through sorting here.
  TodayData = TodayData[1::]
  SelectedDayData = SelectedDayData[1::]
  
  workdate=workDateArrayification(UserPK)
  results = getuserdata(UserPK)
  streak, freezes, coins = results[4:7]
  return render_template('exercise/exercise.html',streak=streak, freezes=freezes, coins=coins,workdate=workdate, SelectedDayData=SelectedDayData, TodayData=TodayData)

@app.route('/exercisedays', methods=['GET'])
def exercisedays():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
  UserPK = getUserPK()
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
  UserPK = getUserPK()
  generateExercise(UserPK, selectedday)
  return redirect(url_for('exercise'))

@app.route('/log', endpoint = 'log')
def exerciselog():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  results = getuserdata(UserPK)
  streak, freezes, coins = results[4:7]
  return render_template('exercise/exerciselog.html',streak=streak, freezes=freezes, coins=coins)

#Test Streak Update
@app.route('/logsubmit', methods=['POST'])
def logsubmit():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
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
  dbcommand = "INSERT INTO UserDiary (UserPK, Date, Diary, Difficulty, PastWeight) VALUES (?, ?, ?, ?, ?)"
  cursor.execute(dbcommand, (UserPK, datetime.datetime.now().date(), diary, difficulty, weight))
  dbcommand = "UPDATE Users SET Weight= ? WHERE UserPK = ?"
  cursor.execute(dbcommand, (weight, UserPK)) 
  conn.commit()
  conn.close()
  StreakUpdate(UserPK)
  return redirect(url_for('exercise'))

@app.route('/graph')
def exercisegraph():
  username = sessioncheck('user_id')
  if not sessioncheck('user_id'):
    flash('Please log in')
    return redirect(url_for('index'))
  UserPK = getUserPK()
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = f"SELECT Diary, Date FROM UserDiary WHERE UserPK = " + "'" + str(UserPK) + "'"
  cursor.execute(dbcommand)
  DiaryData = cursor.fetchall()
  dbcommand = f"SELECT Difficulty, PastWeight, Date FROM UserDiary WHERE UserPK = " + "'" + str(UserPK) + "'"
  cursor.execute(dbcommand)
  GraphData = cursor.fetchall()
  results = getuserdata(UserPK)
  
  streak, freezes, coins = results[4:7]
  return render_template('exercise/graphscreen.html',streak=streak, freezes=freezes, coins=coins, GraphData=GraphData, DiaryData=DiaryData)

if __name__ == "__main__":  # Makes sure this is the main process
  app.run( # Starts the site
    host='0.0.0.0',
    port=80,
    debug=True
  )