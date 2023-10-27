import sqlite3
import random, sys
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_session import Session
from datetime import date, datetime
import requests


def databaseinit():
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    # Create the Users table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Users (
        Username TEXT PRIMARY KEY AUTOINCREMENT,
        Weight INTEGER,
        Height INTEGER,
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
          WorkoutFelt INTEGER,
          PastWeight REAL,
          CalBurned INTEGER,
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
    item = days[i]
    workdate[item-1] = True #Replace any integer that has been outlined to be true, and thus a workout day.
  return workdate
def csvconvert():
    
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    # Assuming your CSV file has columns named 'column1', 'column2', etc.
    with open('megaGymDataset.csv', 'r', encoding='utf-8') as csv_file:
        linearr = csv_file.read().split('\n')
        count = 0
        for row in linearr:
            data = row.split(',')
            if len(data) == 9:
              dbcommand = "INSERT OR REPLACE INTO Activity (ActivityPK, ActivityName, Description, Type, BodyPart, Equipment, Level, Rating, RatingDesc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
              cursor.execute(dbcommand, (count, data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8]))
            count += 1

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()

def generateExercise(username, DayOfWeek):
  conn = sqlite3.connect('user_data.db')
  cursor = conn.cursor()
  dbcommand = "SELECT COUNT(*) FROM Exercise_Plan WHERE DayOfWeek = " + "'" + DayOfWeek + "'"
  cursor.execute(dbcommand)
  count = cursor.fetchone()[0]
  if count > 0:
     dbcommand = "DELETE FROM Exercise_Plan WHERE DayOfWeek = " + "'" + DayOfWeek + "'"
     cursor.execute
  ActivityPKset = []
  Repsarr = []
  Setarr = []
  for i in range(10):
    Repsarr.append(random.randint(2, 6))
    Setarr.append(3, 5)
  while len(ActivityPKset) != 10:
    ActivityPKset.append(random.randint(1, 1694))
  
  dbcommand = "INSERT OR REPLACE INTO Exercise_Plan (ActivityPK, Username, Reps, Sets, DayOfWeek) VALUES = (?, ?, ?, ?, ?)"
  for i in range(Repsarr):
    cursor.execute(dbcommand, (ActivityPKset[i], username, Repsarr[i], Setarr[i], DayOfWeek))
  cursor.close()
  conn.close()