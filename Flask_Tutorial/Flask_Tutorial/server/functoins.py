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
        Username TEXT PRIMARY KEY,
        Weight REAL,
        Sex BOOLEAN,
        Streak INTEGER,
        Freezes INTEGER,
        Coins INTEGER,
        Wager INTEGER
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
    Username TEXT,
    Restriction TEXT, 
    FOREIGN KEY (Username) REFERENCES Users (Username)
)
  ''')

    # Create the Exercise_Plan table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Exercise_Plan (
          ExerciseKey INTEGER PRIMARY KEY AUTOINCREMENT,
          ActivityPK INTEGER,
          Username INTEGER,
          Reps INTEGER,
          Sets INTEGER,
          DayOfWeek INTEGER,
          FOREIGN KEY (ActivityPK) REFERENCES Activity (ActivityPK),
          FOREIGN KEY (Username) REFERENCES Users (Username)
      )
    ''')


    # Create the UserDiary table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS UserDiary (
          DiaryPK INTEGER PRIMARY KEY AUTOINCREMENT,
          Username INTEGER,
          Date DATE,
          Diary TEXT,
          PastWeight REAL,
          Difficulty REAL,
          FOREIGN KEY (Username) REFERENCES Users (Username)
      )
  ''')

    # Create the ExtraExercises table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS ExtraExercises (
          ExtraExercisesPK INTEGER PRIMARY KEY AUTOINCREMENT,
          DiaryPK INTEGER,
          Username INTEGER,
          Sets INTEGER,
          Reps INTEGER,
          Distance REAL,
          Time INTEGER,
          FOREIGN KEY (DiaryPK) REFERENCES UserDiary (DiaryPK),
          FOREIGN KEY (Username) REFERENCES Users (Username)
      )
  ''')

    # Create the Shopping_List table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Shopping_List (
        ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username INTEGER,
        ServingSize REAL,
        ServingType TEXT,
        IngredientName TEXT,
        FOREIGN KEY (Username) REFERENCES Users (Username)
      )
  ''')

    # Create the Meals table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Meals (
          MealID INTEGER PRIMARY KEY AUTOINCREMENT,
          Username INTEGER,
          Date DATE,
          APIMealID INTEGER,
          MealName STRING,
          MealTypes STRING,
          FOREIGN KEY (Username) REFERENCES Users (Username)
      )
  ''')

    conn.commit()
    conn.close()
def usernamecheck(entereduser):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  sqlstatement = "SELECT * FROM Users WHERE Username = " + "'" + entereduser + "'"
  cursor.execute(sqlstatement)
  results = cursor.fetchall()
  if len(results) == 1:
    return True
  else:
     return False
def sessioncheck(requested):
    try:
        item = session[requested]
        return session[requested]
    except:
        return False
def getuserdata(username):
   conn = sqlite3.connect('user_data.db')
   cursor = conn.cursor()
   dbrequest = "SELECT * FROM Users WHERE Username = " + "'" + username + "'"
   cursor.execute(dbrequest)
   results = cursor.fetchone()
   return results
def workdatearr(username):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  
  dbcommand = "SELECT DayOfWeek FROM Exercise_Plan WHERE Username = " + "'" + username + "'" #Get DayOfWeek (Workout Date) from Exercise_Plan table
  cursor.execute(dbcommand)
  days = cursor.fetchall()
  conn.commit()
  workdate = [False, False, False, False, False, False, False] #Define workout date array
  for i in range(len(days)):
    item = days[i][0]
    workdate[item] = True #Replace any integer that has been outlined to be true, and thus a workout day.
  return workdate
def csvconvert(): #Original code taken from https://datatofish.com/import-csv-sql-server-python/ then modified it to make the code actually work because I believe the code at the website was assuming an SQL server whereas I'm using an SQLite database.
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
def generateExercise(username, DayOfWeek):
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
  dbcommand = "INSERT INTO Exercise_Plan (ActivityPK, Username, Reps, Sets, DayOfWeek) VALUES (?, ?, ?, ?, ?)"
  for i in range(len(RepsArray)):
    cursor.execute(dbcommand, (ActivityPrimaryKeyArray[i], username, RepsArray[i], SetsArray[i], DayOfWeek))
  dbcommand = "SELECT ActivityPK, Reps, Sets, DayOfWeek FROM Exercise_Plan WHERE Username = " + "'" + username + "'"
  cursor.execute(dbcommand)
  data = cursor.fetchall()
  conn.commit()
  cursor.close()
  conn.close()
def GetExerciseDayData(Day, username):

  #Get Sets, and Reps based on the day
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT ExerciseKey, ActivityPK, Sets, Reps  FROM Exercise_Plan WHERE Username = ? AND DayOfWeek = ?"
  cursor.execute(dbcommand, (username, Day))
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