import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()

# Create the Users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        UserPK INTEGER PRIMARY KEY,
        UserName TEXT,
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
    CREATE TABLE IF NOT EXISTS Activity
      ActivityPK INTEGER PRIMARY KEY
      ActivityName STRING
      CalBurnedWeight REAL
''')

# Create the Dietary Restrictions table
cursor.execute('''
  CREATE TABLE IF NOT EXISTS MealRestrictions (
      FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
      Restriction TEXT,
)
''')

# Create the Exercise_Plan table
cursor.execute('''
  CREATE TABLE IF NOT EXISTS Exercise_Plan (
      ExerciseKey INTEGER PRIMARY KEY,
      ActivityPK INTEGER,
      UserPK INTEGER,
      Reps INTEGER,
      Sets INTEGER,
      Distance REAL,
      FOREIGN KEY (ActivityPK) REFERENCES Activity (ActivityPK),
      FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
)
''')

# Create the UserDiary table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS UserDiary (
        DiaryPK INTEGER PRIMARY KEY,
        UserPK INTEGER,
        Date DATE,
        Diary TEXT,
        WorkoutFelt INTEGER,
        PastWeight REAL,
        CalBurned INTEGER,
        FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
    )
''')

# Create the ExtraExercises table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ExtraExercises (
        ExtraExercisesPK INTEGER PRIMARY KEY,
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
        ItemID INTEGER PRIMARY KEY,
        UserPK INTEGER,
        ServingSize REAL,
        ServingType TEXT,
        FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
    )
''')

# Create the Meals table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Meals (
        MealID INTEGER PRIMARY KEY,
        UserPK INTEGER,
        Date DATE,
        APIMealID INTEGER,
        FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
    )
''')

conn.commit()
conn.close()