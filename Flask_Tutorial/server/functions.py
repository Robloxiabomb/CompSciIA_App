import sqlite3
import random, sys
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_session import Session
import datetime
import pandas as pd
import requests
import time

def databaseinit():
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    # Create the Users table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Users (
        UserPK INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT,
        Weight REAL,
        Sex BOOLEAN,
        Streak INTEGER,
        Freezes INTEGER,
        Coins INTEGER
      )
    ''')
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS WagerInfo (
        UserPK INTEGER,
        Wager Integer,
        WagerDate DATE,
        StreakAtTimeOfWager INTEGER,
        WagerCount INTEGER,
        FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
      )
    ''')
    # Create the Activity table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Activity(
        ActivityPK INTEGER PRIMARY KEY AUTOINCREMENT,
        ActivityName STRING,
        Description STRING,
        Type STRING,
        BodyPart STRING,
        Equipment STRING,
        Level STRING,
        Rating REAL,
        RatingDesc STRING
)
  ''')

    # Create the Dietary Restrictions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MealRestrictions (
    UserPK INTEGER,
    Restriction TEXT, 
    FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
)
  ''')

    # Create the Exercise_Plan table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Exercise_Plan (
          ExerciseKey INTEGER PRIMARY KEY AUTOINCREMENT,
          ActivityPK INTEGER,
          UserPK INTEGER,
          Username STRING,
          Reps INTEGER,
          Sets INTEGER,
          DayOfWeek INTEGER,
          FOREIGN KEY (ActivityPK) REFERENCES Activity (ActivityPK),
          FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
      )
    ''')


    # Create the UserDiary table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS UserDiary (
          DiaryPK INTEGER PRIMARY KEY AUTOINCREMENT,
          UserPK INTEGER,
          Date DATE,
          Diary TEXT,
          PastWeight REAL,
          Difficulty REAL,
          FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
      )
  ''')

    # Create the ExtraExercises table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS ExtraExercises (
          ExtraExercisesPK INTEGER PRIMARY KEY AUTOINCREMENT,
          DiaryPK INTEGER,
          UserPK INTEGER,
          Sets INTEGER,
          Reps INTEGER,
          Distance REAL,
          Time INTEGER,
          FOREIGN KEY (DiaryPK) REFERENCES UserDiary (DiaryPK),
          FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
      )
  ''')

    # Create the Shopping_List table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Shopping_List (
        ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserPK INTEGER,
        ServingSize REAL,
        ServingType TEXT,
        IngredientName TEXT,
        FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
      )
  ''')

    # Create the Meals table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Meals (
          MealID INTEGER PRIMARY KEY AUTOINCREMENT,
          UserPK STRING,
          Date DATE,
          APIMealID INTEGER,
          MealName STRING,
          MealTypes STRING,
          FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
      )
  ''')

    conn.commit()
    conn.close()

def usernamecheck(entereduser):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  sqlstatement = "SELECT * FROM Users WHERE Username = " + "'" + str(entereduser) + "'"
  cursor.execute(sqlstatement)
  results = cursor.fetchall()
  if len(results) >= 1:
    return True
  else:
     return False

def sessioncheck(requested):
    try:
        return session[requested]
    except:
        return False

def getuserdata(UserPK):
   conn = sqlite3.connect('user_data.db')
   cursor = conn.cursor()
   dbrequest = "SELECT * FROM Users WHERE UserPK = " +  str(UserPK)
   cursor.execute(dbrequest)
   results = cursor.fetchone()
   dbcommand = "SELECT Wager FROM WagerInfo WHERE UserPK = " + str(UserPK)
   cursor.execute(dbcommand)
   Wager = cursor.fetchone()
   return results + Wager

def workDateArrayification(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  
  dbcommand = "SELECT DayOfWeek FROM Exercise_Plan WHERE UserPK = " +  str(UserPK) #Get DayOfWeek (Workout Date) from Exercise_Plan table
  cursor.execute(dbcommand)
  days = cursor.fetchall()
  conn.commit()
  workdate = [False, False, False, False, False, False, False] #Define workout date array
  for i in range(len(days)):
    item = days[i][0]
    workdate[item] = True #Replace any integer that has been outlined to be true, and thus a workout day.
  return workdate

def csvConvert(): #Original code taken from https://datatofish.com/import-csv-sql-server-python/ then modified it to make the code actually work because I believe the code at the website was assuming an SQL server whereas I'm using an SQLite database.
  # Import CSV
  data = pd.read_csv(r'C:\Users\cmcin\Documents\Programming\Python\Flask_Tutorial\megaGymDataset.csv')
  df = pd.DataFrame(data)

  # Connect to SQLite
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  # Insert DataFrame to Table
  for row in df.itertuples():
    dbcommand = '''INSERT INTO Activity (ActivityName, Description, Type, BodyPart, Equipment, Level, Rating, RatingDesc) VALUES (?,?,?,?,?,?,?,?)'''
    cursor.execute(dbcommand,
    (row.ActivityName, 
    row.Description,
    row.Type,
    row.BodyPart,
    row.Equipment,
    row.Level,
    row.Rating,
    row.RatingDesc)
    )

  conn.commit()

def generateExercise(UserPK, DayOfWeek):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()

  dbcommand = "SELECT COUNT(*) FROM Exercise_Plan WHERE DayOfWeek = " + "'" + str(DayOfWeek) + "'"
  cursor.execute(dbcommand)
  count = cursor.fetchone()[0]
  if count > 0:
    dbcommand = "DELETE FROM Exercise_Plan WHERE DayOfWeek = " + "'" + str(DayOfWeek) + "'"
    cursor.execute(dbcommand)
    conn.commit()

  ActivityPrimaryKeyArray = []
  RepsArray = []
  SetsArray = []
  ActivityPrimaryKeySet = set(ActivityPrimaryKeyArray)

  for i in range(10):
    RepsArray.append(random.randint(2, 6))
    SetsArray.append(random.randint(3, 5))

  while len(ActivityPrimaryKeySet) < 10:
    ActivityPrimaryKeyArray.append(random.randint(1, 1600))
    ActivityPrimaryKeySet = set(ActivityPrimaryKeyArray)

  ActivityPrimaryKeyArray = list(ActivityPrimaryKeySet)
  dbcommand = "INSERT INTO Exercise_Plan (ActivityPK, UserPK, Reps, Sets, DayOfWeek) VALUES (?, ?, ?, ?, ?)"
  for i in range(len(RepsArray)):
    cursor.execute(dbcommand, (ActivityPrimaryKeyArray[i], UserPK, RepsArray[i], SetsArray[i], DayOfWeek))
  dbcommand = "SELECT ActivityPK, Reps, Sets, DayOfWeek FROM Exercise_Plan WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  data = cursor.fetchall()
  conn.commit()
  cursor.close()
  conn.close()

def getExerciseDayData(Day, UserPK):

  #Get Sets, and Reps based on the day
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT ExerciseKey, ActivityPK, Sets, Reps  FROM Exercise_Plan WHERE UserPK = ? AND DayOfWeek = ?"
  cursor.execute(dbcommand, (UserPK, Day))
  DayData = cursor.fetchall()
  conn.commit()
  #Get Activity Name from Activity table based on ActivityPK for day
  ActivityNameArray = []
  SetsArray = []
  RepsArray = []
  ExerciseKeyArray = []
  for i in range(len(DayData)):
    #Get ExerciseKey
    ExerciseKey = DayData[i][0]
    ExerciseKeyArray.append(ExerciseKey)

    #Get ActivityPK
    ActivityPK = DayData[i][1]
    dbcommand = "SELECT ActivityName FROM Activity WHERE ActivityPK = " + "'" + str(ActivityPK) + "'"
    cursor.execute(dbcommand)
    conn.commit()
    Key = cursor.fetchone()
    ActivityNameArray.append(Key[0])

    
    #Get Sets
    Sets = DayData[i][2]
    SetsArray.append(Sets)

    #Get Reps
    Reps = DayData[i][3]
    RepsArray.append(Reps)
  return (ExerciseKeyArray, ActivityNameArray, SetsArray, RepsArray)

def mealIngredientAPIHandler(APIresponse):
  WeekList = ["monday", 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
  NameList = []
  IDList = []
  for i in range(len(APIresponse["week"])):
    for j in range(len(APIresponse["week"][WeekList[i]])+1):
      IDList.append(APIresponse["week"][WeekList[i]]["meals"][j]["id"])
      NameList.append(APIresponse["week"][WeekList[i]]["meals"][j]["title"])
  return (NameList, IDList)

def convertDate(dateString):
  dateString = datetime.datetime.strptime(dateString, '%Y-%m-%d')
  return dateString

def WeekDayFormatting(WeekDay):
  if WeekDay == 6:
    WeekDay = 0
  else:
    WeekDay += 1
  return WeekDay

def WagerCheck(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  #Grab Streak. If it's 7 then I guess wager is complete?
  dbcommand = "SELECT StreakAtTimeOfWager, WagerDate FROM WagerInfo WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  #Should work just unpacks tuple due to it being fetchone it will return a tuple rather than an array
  try:
    StreakAtTimeOfWager, WagerDate = cursor.fetchone()
  except TypeError:
    dbcommand = "INSERT INTO WagerInfo (UserPK, Wager, WagerDate, StreakAtTimeOfWager, WagerCount) VALUES (" + str(UserPK) + ", 0, NULL, 0, 0) "
    cursor.execute(dbcommand)
    conn.commit()
    return True
  dbcommand = "SELECT STREAK FROM Users WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  Streak = cursor.fetchone()
  dbcommand = "SELECT DayOfWeek FROM Exercise_Plan WHERE UserPK = " + str(UserPK) +  " ORDER BY DayOfWeek DESC"
  cursor.execute(dbcommand)
  DaysOfWeek = cursor.fetchall() #Array containing tuples. Don't care about tuples care about length
  DateToday = datetime.datetime.today().date().weekday()
  if WagerDate == None:
    return "Continued"
  WagerDate = convertDate(WagerDate)
  Delta = DateToday - WagerDate
  DaysPassed = Delta.datetime.days
  if len(DaysOfWeek) <= (Streak - StreakAtTimeOfWager) and DaysPassed >= 7: #This can probably be exploited in some way through logging on at certain times, but IDC as long as it doesn't mess with the tables exploits don't matter and it's not something that you would come up with in your normal day-to-day time.
    return True
  elif StreakAtTimeOfWager > Streak:
    return False
  else:
    return "Continued"
  #True is wager complete
  #False is wager failed
  #Continued is wager not failed or complete

def StreakCheck(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Streak, Freezes FROM Users WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  Streak, Freezes = cursor.fetchone()
  dbcommand = "SELECT DATE FROM UserDiary WHERE UserPK = " + str(UserPK) + " ORDER BY DATE DESC LIMIT 1"
  cursor.execute(dbcommand)
  ExerciseDates = cursor.fetchone()
  if ExerciseDates != None:
    ExerciseDateFormatted = convertDate(dateString=ExerciseDates[0])
  elif Freezes >= 0:
    #Returns freezes because user is alerted if a freeze is used
    Freezes -= 1
    dbcommand = "UPDATE Freezes FROM Users WHERE UserPK = " + str(UserPK) + " VALUE (?)"
    return "Freezes"
  else:
    #Handles 0 diary dates. No reason to remove streak.
    return True
  dbcommand = "SELECT DayOfWeek FROM Exercise_Plan WHERE UserPK = " + str(UserPK) + " ORDER BY DayOfWeek DESC"
  cursor.execute(dbcommand, (Freezes))
  DaysOfWeek = cursor.fetchall()
  #If there are no days to miss then there's no reason go be worrying about streak.
  if DaysOfWeek == None:
    return True
  #Loop through the dates that we were given, find when the last one from the current day is that should have been done. If it hasn't been done return an error.
  WeekDayToday = WeekDayFormatting(datetime.datetime.today().date().weekday())
  #Break. It. Down.
  #What do we need to end up with?
    #We need to find out if there were any days between the last log date, and the current date.
  #What do we need to get there?
    #We need the current date
    #We need the last log date as a weekday.
    #We need to know if there were any days between those two dates that are in the exercise plan.
  #How can we do that?
    #Iterate through every single date between the last log date and today
    #Convert that to a day of week
    #If that day of week is in the DaysOfWeek array set streak to 0. Return False
    #If day is not in DaysOfWeek array Return True. End Function.
  #Used code from https://www.geeksforgeeks.org/python-iterating-through-a-range-of-dates/
  Delta = datetime.timedelta(days=1)
  #Just demonstrates algorithm above:
  while (ExerciseDateFormatted <= WeekDayToday):    
      if WeekDayFormatting(ExerciseDateFormatted.weekday()) in DaysOfWeek:
        dbcommand = "UPDATE Streak FROM Users WHERE UserPK = " + str(UserPK) + " VALUE (0)"
        cursor.execute(dbcommand)
        conn.commit()
        conn.close()
        return False
      ExerciseDateFormatted += Delta
  return True

def coinsIncrement(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Coins FROM Users WHERE UserPK = '" + str(UserPK)
  cursor.execute(dbcommand)
  Coins = cursor.fetchone()[0]
  Coins += 200
  dbcommand = "UPDATE Coins FROM Users WHERE UserPK = " + str(UserPK) + " VALUE (?)"
  cursor.execute(dbcommand, (Coins))
  conn.commit()
  conn.close()

def StreakUpdate(UserPK):
  #Small issue is that streak doesn't get updated on days when you don't have workouts, so if you were to follow this routine for 7 days you might only get a streak of 2. Figured that's just how it'll be designed
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  #Get Streak
  dbcommand = "SELECT Streak FROM Users WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  Streak = cursor.fetchone()[0]
  #Get lastworkoutdate
  dbcommand = "SELECT Date FROM UserDiary WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  conn.commit()
  try:
    LastWorkoutDate = cursor.fetchone()[0]
  except TypeError:
    print("TypeError")
    Streak += 1
    dbcommand = "UPDATE Users SET Streak = " + str(Streak) + " WHERE UserPK = " + str(UserPK)
    cursor.execute(dbcommand)
    conn.commit()
    return True
  LastWorkoutDate = convertDate(LastWorkoutDate)
  #Check if last workout date is today.
  DateToday = datetime.datetime.today().date()
  if LastWorkoutDate.date() == DateToday:
    #If it is do not update streak
    return False
  elif LastWorkoutDate != DateToday:
    #If it isn't do update streak.
    Streak += 1
    dbcommand = "UPDATE Users SET Streak = " + str(Streak) + " WHERE UserPK = " + str(UserPK)
    cursor.execute(dbcommand)
    conn.commit()
    conn.close()
    return True

def getUserPK():
  username = sessioncheck('user_id')
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT UserPK FROM Users WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  UserPK = cursor.fetchone()[0]
  conn.close()
  return UserPK

def endStreak(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "UPDATE Users SET Streak = 0 WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  conn.commit()
  conn.close()

def endWager(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "UPDATE WagerInfo SET Wager = 0, StreakAtTimeOfWager = NULL, WagerDate = NULL, WagerCount = NULL WHERE UserPK = " + str(UserPK) + " VALUE (0, NULL, NULL, NULL)"
  cursor.execute(dbcommand)
  conn.commit()
  conn.close()

def wagerSuccess(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT Coins FROM Users WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  Coins = cursor.fetchone()[0]
  dbcommand = "UPDATE Coins FROM Users WHERE UserPK = " + str(UserPK) + " VALUE (?)"
  cursor.execute(dbcommand, (Coins))
  conn.commit()
  conn.close()

def getMealID(UserPK):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT APIMealID FROM MEALS WHERE UserPK = " + str(UserPK)
  cursor.execute(dbcommand)
  conn.commit()
  conn.close()
