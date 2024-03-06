import sqlite3
import random
from flask import session, flash
import requests
from datetime import datetime, timedelta, date
import pandas as pd


def convert_csv():
    # Import CSV
    data = pd.read_csv('/fitflow360/app/megaGymDataset.csv')

    DataFrame = pd.DataFrame(data)

    # Connect to SQLite
    conn, cursor = db_connection("user_data.db")
    # Insert DataFrame to Table
    for row in DataFrame.itertuples():
        db_command = '''INSERT INTO Activity (ActivityName, Description, Type, BodyPart, Equipment, Level, \
              Rating, RatingDesc) VALUES (?,?,?,?,?,?,?,?)'''
        cursor.execute(db_command,
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

 
def check_username(entered_user, conn, cursor):
    # Get username data
    db_command = f"SELECT * FROM Users WHERE Username = '{str(entered_user)}'"
    cursor.execute(db_command)
    results = cursor.fetchall()
    conn.close

    # Check if username exists
    if len(results) >= 1:
        return True
    else:
        return False


def check_session(requested):
    try:
        return session[requested]
    except Exception as e:
        print(e)
        return False


def get_table_name_info(cursor):
    cursor.execute("PRAGMA table_info(Users)")
    column_list = [row[1] for row in cursor.fetchall()]
    column_text = ','.join(column_list)
    return column_text, column_list


def get_user_data(user_pk, cursor):
    # Get table name info
    column_text, column_list = get_table_name_info(cursor)
    
    # Get user info from Users table
    db_request = f"SELECT {column_text} FROM Users WHERE UserPK = {str(user_pk)}"
    cursor.execute(db_request)
    users_data = cursor.fetchone()
    
    # Get user info from wager table
    db_command = "SELECT Wager FROM WagerInfo WHERE UserPK = " + str(user_pk)
    cursor.execute(db_command)
    wager_data = cursor.fetchone()
    
    # Format data into dictionary
    user_data_dict = dict(zip(column_list, users_data))
    user_data_dict["Wager"] = wager_data[0] if wager_data is not None else None
    return user_data_dict


def get_user_pk(conn, cursor):
    username = check_session('session_id')
    db_command = "SELECT UserPK FROM Users WHERE Username = " + "'" + username + "'"
    cursor.execute(db_command)
    user_pk = cursor.fetchone()[0]
    return user_pk


def update_settings_data(username_change, weight, sex, user_pk, dietary_restrictions, restriction_list, conn, cursor):
    
    # Update session
    session["session_id"] = username_change

    # Update user info
    db_command = "UPDATE Users SET Username= ?, Weight = ?, Sex = ? WHERE UserPK = " + str(user_pk)
    cursor.execute(db_command, (username_change, weight, sex))
    conn.commit()

    # Set up meal restrictions commands and format dietary restrictions array.
    db_command_delete = "DELETE FROM MealRestrictions WHERE UserPK = ? AND Restriction = ?"
    db_command_insert = "INSERT INTO MealRestrictions (UserPK, Restriction) VALUES (?, ?)"
    db_command_read = "SELECT Restriction FROM MealRestrictions WHERE UserPK = " + str(user_pk)
    cursor.execute(db_command_read)
    db_dietary_restrictions = [x[0] for x in cursor.fetchall()]
    
    # Update meal restrictions table.
    for i in restriction_list:
        if i in db_dietary_restrictions and i not in dietary_restrictions:
            cursor.execute(db_command_delete, (user_pk, i))
            conn.commit()
        elif i not in db_dietary_restrictions and i in dietary_restrictions:
            cursor.execute(db_command_insert, (user_pk, i))
            conn.commit()


def signup_form_validation(username, sex, weight, conn, cursor):
    valid_flag = False
    forbidden_characters = ['=', '*', ',', '(', ')', '$', '# ', '@', '!', '&', '<', '>', '/', '?', '.']
    validation_message_dict = {}

    # Injection check
    if any(char in username for char in forbidden_characters):
        validation_message_dict['Usernameinvalid'] = "Username cannot contain the following characters: = \
                                                     , *, ',', (, ), $, # , @, !, &, <, >, /, ?, ."
        valid_flag = True

    # Validate weight
    try:
        weight = float(weight)
        weight_flag = False
        if weight < 0:
            weight_flag = True
    except ValueError:
        flash('Weight must be a positive decimal or integer. Please try again.', 'Weight')
        weight_flag = True
    if weight_flag:
        validation_message_dict['Weight'] = "Weight must be a positive decimal or integer. Please try again."

    # Ensure username isn't taken.
    if check_username(username, conn, cursor):
        validation_message_dict['Usernametaken'] = 'Username taken. Please enter another username.'
        valid_flag = True

    # Ensure sex is not empty.
    if sex == 'Invalid':
        flash('Please choose Male or Female.', 'dropdown')
        validation_message_dict['dropdown'] = 'Please choose Male or Female'
        valid_flag = True
    return (valid_flag, validation_message_dict)


def check_wager(user_pk, conn, cursor):
    db_command = f"SELECT StreakAtTimeOfWager, WagerDate FROM WagerInfo WHERE UserPK = {str(user_pk)}"
    cursor.execute(db_command)
    # If the wager record does not exist. Create one. Wager has not failed.
    try:
        streak_at_time_of_wager, wager_date = cursor.fetchone()
    except TypeError:
        db_command = f"INSERT INTO WagerInfo (UserPK, Wager, WagerDate, StreakAtTimeOfWager, WagerCount) VALUES ({str(user_pk)}, 0, NULL, 0, 0) "
        cursor.execute(db_command)
        conn.commit()
        return "Continued"
    
    # Wager_date is none means no exercise has been created.
    if wager_date is None:
        return "Continued"

    # Get streak
    db_command = f"SELECT STREAK FROM Users WHERE UserPK = {str(user_pk)}"
    cursor.execute(db_command)
    streak = cursor.fetchone()
    # Get exercise plan days
    db_command = f"SELECT DayOfWeek FROM Exercise_Plan WHERE UserPK = {str(user_pk)} ORDER BY DayOfWeek DESC"
    cursor.execute(db_command)
    days_of_week = cursor.fetchall()
    date_today = datetime.today()
    # Format wager_date properly
    wager_date = convert_date(wager_date)
    Delta = date_today - wager_date
    # Calculate days passed
    days_passed = Delta.days

    # Check to see if a streak has been lost between now and current login. If it has, then the wager is kaput.
    if len(days_of_week) <= (streak[0] - streak_at_time_of_wager) and days_passed >= 7:
        # Streak kept because it's greater (or equal) than the streak_at_time_of_wager and the days that have passed is greater than 7.
        wager_success()
        end_wager()
        return True
    elif streak_at_time_of_wager > streak[0]:
        # Streak lost because it's less than streak_at_time_of_wager
        end_wager()
        return False
    else:
        # Neither is the case. Streak is kept the same.
        return "Continued"
    # True is wager complete
    # False is wager failed
    # Continued is wager not failed or complete


def end_wager(user_pk, conn, cursor):
    db_command = f"UPDATE WagerInfo SET Wager = 0, streakAtTimeOfWager = NULL, \
        wagerDate = NULL,WagerCount = NULL WHERE UserPK = {str(user_pk)}"
    cursor.execute(db_command)
    conn.commit()
    

def wager_success(user_pk, conn, cursor):
    user_data = get_user_data(user_pk, cursor)
    
    # Get required user data
    wager = user_data["Wager"]
    coins = user_data["Coins"]

    # Give coins to user
    db_command = f"UPDATE Coins FROM Users WHERE UserPK = {str(user_pk)} VALUE (?)"
    cursor.execute(db_command, (coins + wager*2))
    conn.commit()
    # Delete the wager
    end_wager(user_pk)


def check_streak(user_pk, conn, cursor):
    # Get user data
    user_data = get_user_data(user_pk, cursor)
    freezes = user_data["Freezes"]
    
    # Get dates from UserDiary
    db_command_date = f"SELECT DATE FROM UserDiary WHERE UserPK = {str(user_pk)} ORDER BY DATE DESC LIMIT 1"
    cursor.execute(db_command_date)
    exerciseDates = cursor.fetchone()
    if exerciseDates is not None:
        exercise_date_formatted = convert_date(date_string=exerciseDates[0])
    else:
        # Handles 0 diary dates. No reason to remove streak.
        return True
    db_command = f"SELECT DayOfWeek FROM Exercise_Plan WHERE UserPK = {str(user_pk)} ORDER BY DayOfWeek DESC"
    cursor.execute(db_command)
    days_of_week = cursor.fetchall()
    # If there are no days to miss then there's no reason to be worrying about streak.
    if days_of_week is None:
        return True
    week_day_today = datetime.today()
    # Used code from https://www.geeksforgeeks.org/python-iterating-through-a-range-of-dates/
    delta = timedelta(days=1)
    while (exercise_date_formatted <= week_day_today):  
        if week_day_formatting(exercise_date_formatted.weekday()) in days_of_week and freezes == 0:
            db_command = f"UPDATE Streak FROM Users WHERE UserPK = {str(user_pk)} VALUE (0)"
            cursor.execute(db_command)
            conn.commit()
            
            return False
        elif week_day_formatting(exercise_date_formatted.weekday()) in days_of_week:
            freezes -= 1
            db_command = f"UPDATE Users SET Freezes = (?) WHERE UserPK = {str(user_pk)}"
            cursor.execute(db_command, (freezes))
            return "Freezes"
        exercise_date_formatted += delta
    return True


def end_streak(user_pk, conn, cursor):
    db_command = f"UPDATE Users SET Streak = 0 WHERE UserPK = {user_pk}"
    cursor.execute(db_command)
    conn.commit()
    

def settings_form_validation(username_change, username, sex, weight, conn, cursor):
    settings_form_dict = {}
    forbidden_characters = ['=', '*', ',', '(', ')', '$', '# ', '@', '!', '&', '<', '>', '/', '?', '.']
    inject_flag = False
    valid_flag = False
    
    # Validate weight
    weight_flag = False
    try:
        weight = float(weight)
        if weight < 0:  # Ensure Weight is positive
            weight_flag = True
    except ValueError:
        weight_flag = True
    if weight_flag:
        settings_form_dict["Weight"] = 'Weight must be a positive decimal or integer. Please try again.'
    
    # Validate username
    inject_flag = any(char in forbidden_characters for char in username_change)
    if check_username(username_change, conn, cursor) and username != username_change:  # Ensure that the Username is not taken
        settings_form_dict["Usernametaken"] = "Username taken. Please choose another username."
        valid_flag = True
    elif inject_flag:  # Ensure that it's not an SQL injection
        settings_form_dict["Usernameinvalid"] = "Username cannot contain the following letters: =, *, ',', (, ), $, # , @, !, &, <, >, /, ?, ."
        valid_flag = True
    
    # Validate sex
    if sex == 'Invalid':
        settings_form_dict["dropdown"] = "Please choose male or female."
        valid_flag = True
    
    return (valid_flag, settings_form_dict)


def database_init():
    conn, cursor = db_connection('user_data.db')

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
    # Create the WagerInfo table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS WagerInfo (
            UserPK INTEGER,
            Wager Integer,
            wagerDate DATE,
            streakAtTimeOfWager INTEGER,
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
            MealPosition INTEGER,
            APIMealID INTEGER,
            MealName STRING,
            FOREIGN KEY (UserPK) REFERENCES Users (UserPK)
        )
    ''')

    conn.commit()
    

def db_connection(db_name):
    # Connect to database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    return conn, cursor


def get_meal_plan(user_pk, conn, cursor):

    # Get mealname from Meals table
    db_command = "SELECT MealName FROM Meals WHERE UserPK = " + str(user_pk) + " ORDER BY MealPosition ASC"
    cursor.execute(db_command)
    meal_plan_data = cursor.fetchall()
    

    # Format array of tuples into an array
    meal_plan_arr = [x[0] for x in meal_plan_data]

    return meal_plan_arr


def update_meal_plan(url, user_pk, check_box_data, conn, cursor):
    response = requests.get(url).json()
    #Get meal plan
    try:
        name_list, id_list = meal_name_api(response)
    except Exception as e:
        print(f"Exception: {e}")
    

    print(len(check_box_data))
    #Insert meal plan into array
    try:
        db_command_delete = "DELETE FROM Meals WHERE UserPK = ? AND MealPosition = ?"
        db_command_insert = "INSERT INTO Meals (UserPK, APIMealID, MealName, MealPosition) VALUES (?, ?, ?, ?)"
        for i in range(len(check_box_data)):
            if check_box_data[i] is None:
                cursor.execute(db_command_delete, (user_pk, i))
                conn.commit()
                cursor.execute(db_command_insert, (user_pk, id_list[i], name_list[i], i))
                conn.commit()
    except Exception as e:
        print(f"Exception: {e}")


def get_dietary_restrictions(user_pk, conn, cursor):
    #Select all restrictions. Format them into an array.
    db_command = f"SELECT Restriction FROM MealRestrictions WHERE UserPK = {user_pk}"
    cursor.execute(db_command)
    return [x[0] for x in cursor.fetchall()]


def meal_ingredient_api(api_response):
    try:
        ingredient_list = []
        serving_list = []
        unit_type_list = []

        # Format json into ingredient_list, serving_list, and unit_type_list
        for ingredient in range(len(api_response['ingredients'])):
            ingredient_list.append(api_response['ingredients'][ingredient]["name"])
            serving_list.append(api_response["ingredients"][ingredient]["amount"]["metric"]["value"])
            unit_type_list.append(api_response["ingredients"][ingredient]["amount"]["metric"]["unit"])
        return ingredient_list, serving_list, unit_type_list
    except IndexError:
        # Handles an exception where the API tokens run out.
        if api_response["code"] == 402:
            return True
        else:
            return "Failure"


def shopping_list_add(user_pk, cursor, conn, ingredient_name, serving_size, serving_type):
    # Get IngredientName and ServingSize from Shopping_List
    db_command = f"SELECT ServingSize FROM Shopping_List WHERE IngredientName = '{ingredient_name}' AND UserPK = '{str(user_pk)}'"
    cursor.execute(db_command)
    data = cursor.fetchall()

    if len(data) == 0: # If item does not exist in database
        # Add item to shopping list
        db_command = "INSERT INTO Shopping_List (UserPK, IngredientName, ServingSize, servingType) VALUES (?, ?, ?, ?)"
        cursor.execute(db_command,
                    (user_pk,
                        ingredient_name,
                        serving_size,
                        serving_type
                        )
                    )
        conn.commit()
    else:
        new_serving_size = float(data[0][0]) + float(serving_size)
        # Add value to existing item in database
        db_command = f"UPDATE Shopping_List SET ServingSize = {str(new_serving_size)} WHERE UserPK = {str(user_pk)}"
        cursor.execute(db_command)
        conn.commit()


def shopping_list_formatting(user_pk, cursor):
    # Get data
    db_command = f"SELECT ServingSize, ServingType, IngredientName FROM Shopping_List WHERE UserPK = {str(user_pk)}"
    cursor.execute(db_command)
    record = cursor.fetchall()
    # Format into arrays
    try:
        if len(record) == 0:
            return ([], [], [])
        return zip(*record)
    except ValueError:
        return ([], [], [])


def meal_search_api(api_response):
    try:
        name_list = []
        id_list = []

        # Get JSON into arrays
        for meal in range(len(api_response)):
            id_list.append(api_response[meal]["id"])
            name_list.append(api_response[meal]["title"])
        return id_list, name_list
    except IndexError:
        # API tokens run out
        if api_response["code"] == 402:
            return True
        else:
            # In case the world ends or they update the way the response is formatted.
            return "Failure"


def meal_name_api(api_response):
    week_list = ["monday", 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    name_list = []
    id_list = []
    
    #Format JSON into the arrays
    try:
        for week in range(len(api_response["week"])):
            for meal in range(len(api_response["week"][week_list[week]])+1):
                id_list.append(api_response["week"][week_list[week]]["meals"][meal]["id"])
                name_list.append(api_response["week"][week_list[week]]["meals"][meal]["title"])
        return (name_list, id_list)
    except IndexError:
        if api_response["code"] == 402:
            # Tokens run out
            return True
        else:
            return "Failure"


def get_recipe_url(api_response):
    try:
        return api_response["sourceUrl"]
    except IndexError:
        if api_response["code"] == 402: # Tokens ran out
            return True
        else: # JSON format's changed OR Everything is burning - save us!
            return "Failure"


def get_workout_days_array(user_pk, conn, cursor):
    
    # Get days on which there is a workout
    db_command = "SELECT DayOfWeek FROM Exercise_Plan WHERE UserPK = " +  str(user_pk)
    cursor.execute(db_command)
    days = cursor.fetchall()
    conn.commit()
    
    work_date = [False, False, False, False, False, False, False]
    for i in range(len(days)):
        item = days[i][0]
        work_date[item] = True # Replace any integer that has been outlined to be true, and thus a workout day.
    return work_date


def generate_exercise(user_pk, day_of_week, conn, cursor):

    # Get number of exercises on the specific day
    db_command_count = f"SELECT COUNT(*) FROM Exercise_Plan WHERE DayOfWeek = \
                        {str(day_of_week)} AND UserPK = {user_pk}"
    cursor.execute(db_command_count)
    count = cursor.fetchone()[0]
    # If there is an exercise on that day. Delete it.
    if count > 0:
        db_command_delete = f"DELETE FROM Exercise_Plan WHERE DayOfWeek \
                            = {str(day_of_week)} AND UserPK = {user_pk}"
        cursor.execute(db_command_delete)
        conn.commit()

    
    reps_array = []
    sets_array = []
    activity_primary_key_array = []

    # Generate reps array and sets array
    reps_array = [random.randint(12, 15) for x in range(10)]
    sets_array = [random.randint(1, 3) for x in range(10)]

    # Generate 10 different activities
    while len(activity_primary_key_array) < 10:
        activity_primary_key_array.append(random.randint(1, 1600))
        activity_primary_key_array = list(set(activity_primary_key_array))

    # Log information on reps, sets, and activities into database.
    db_command_insert = "INSERT INTO Exercise_Plan (ActivityPK, UserPK, Reps, Sets, DayOfWeek) VALUES (?, ?, ?, ?, ?)"
    for i in range(len(reps_array)):
        cursor.execute(db_command_insert, (activity_primary_key_array[i],
                                           user_pk, reps_array[i],
                                           sets_array[i],
                                           day_of_week))
    conn.commit()
    cursor.close()
  

def get_exercise_day_data(user_pk, day_of_week, conn, cursor):
    
    # Get Sets, and Reps based on the day
    
    db_command_select = "SELECT ExerciseKey, ActivityPK, Sets, Reps FROM Exercise_Plan WHERE UserPK = ? AND DayOfWeek = ?"
    cursor.execute(db_command_select, (user_pk, day_of_week))
    day_data = cursor.fetchall()
    conn.commit()

    # Get Activity Name from Activity table based on ActivityPK for day
    activity_name_array = []
    reps_array = [day_data[x][2] for x in range(len(day_data))]
    sets_array = [day_data[x][3] for x in range(len(day_data))]
    exercise_key_array = [[day_data[x][0] for x in range(len(day_data))]]

    # Format array properly because I was stupid JK just forgot how DB results were formatted for a bit
    activity_pk_array = [day_data[x][1] for x in range(len(day_data))]
    db_command_select_activity = "SELECT ActivityName FROM Activity WHERE ActivityPK IN ({})"
    question_mark_formatting = ",".join(["?" for x in activity_pk_array])

    # Get activity name array
    db_command_select_activity = db_command_select_activity.format(question_mark_formatting)
    cursor.execute(db_command_select_activity, (activity_pk_array))
    activity_name_results = cursor.fetchall()
    # map() might be better for this purpose. List comprehension feels easier to read though.
    activity_name_array = [activity_name_results[x][0] for x in range(len(activity_name_results))]

    return exercise_key_array, activity_name_array, reps_array, sets_array


def convert_date(date_string):
    date_string = datetime.strptime(date_string,  '%Y-%m-%d')
    return date_string


def week_day_formatting(week_day):
    # Datetime's weekday formats the day monday to sunday where monday is equal to 0. This fixes that.
    if week_day == 6:
        week_day = 0
    else:
        week_day += 1
    return week_day


def coins_increment(user_pk, conn, cursor):

    # Get coins
    db_command_select = f"SELECT Coins FROM Users WHERE UserPK = {str(user_pk)}"
    cursor.execute(db_command_select)
    coins = cursor.fetchone()[0]
    coins += 200

    # Update coins
    db_command_update = f"UPDATE Coins FROM Users WHERE UserPK = {str(user_pk)} VALUE (?)"
    cursor.execute(db_command_update, (coins))
    conn.commit()


def streak_update(user_pk, streak, conn, cursor):
    
    # Get last_workout_date
    db_command = f"SELECT Date FROM UserDiary WHERE UserPK = {str(user_pk)}"
    cursor.execute(db_command)
    conn.commit()
    # No workout date
    Data = cursor.fetchone()
    if Data is not None:
        last_workout_date = Data[0]
    else:
        print('streak')
        streak += 1
        print('streak')
        db_command = f"UPDATE Users SET Streak = {str(streak)} WHERE UserPK = {str(user_pk)}"
        cursor.execute(db_command)
        conn.commit()
        return True
        
    
    last_workout_date = convert_date(last_workout_date)
    # Check if last workout date is today.
    date_today = datetime.today().date()
    if last_workout_date.date() == date_today:
        # If it is, do not update streak
        return False
    elif last_workout_date != date_today:
        # If it isn't, update streak.
        streak += 1
        db_command = f"UPDATE Users SET Streak = {str(streak)} WHERE UserPK = {str(user_pk)}"
        cursor.execute(db_command)
        conn.commit()
        return True


def log_database_update(weight, coins, user_pk, diary, difficulty, conn, cursor):
    db_command = "INSERT INTO UserDiary (UserPK, Date, Diary, Difficulty, PastWeight) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(db_command, 
                    (
                        user_pk, 
                        datetime.today().date(),
                        diary,
                        difficulty,
                        weight
                    )
                    )
    conn.commit()
    db_command = "UPDATE Users SET Weight = ?, Coins = ? WHERE UserPK = ?"
    cursor.execute(db_command,
                    (
                        weight,
                        int(coins) + 200,
                        user_pk
                    )
                    ) 
    conn.commit()
    

def log_submit_validation(weight, difficulty):
    invalid_flag = False
    try:
        weight = float(weight)
        difficulty = float(difficulty)
        if float(weight) < 0:  # Ensure Weight is positive
            invalid_flag = True
    except ValueError:
        invalid_flag = True
    if invalid_flag:
        return ('Weight must be a positive number!', 'Error')
    return None


def get_graph_data(user_pk, cursor):
    db_command_diary = "SELECT Diary, Date FROM UserDiary WHERE UserPK = ? ORDER BY Date DESC"
    cursor.execute(db_command_diary, (user_pk,))
    diary_data = cursor.fetchall()
    db_command_graph = "SELECT Difficulty, PastWeight, Date FROM UserDiary WHERE UserPK = ?"
    cursor.execute(db_command_graph, (user_pk,))
    graph_data = cursor.fetchall()
    return graph_data, diary_data


def buy_freeze(db_coins, db_freezes, cursor, conn, user_pk):
    # Validate coins
    if db_coins < 200:
        return (False, "Cannot buy freeze. Not enough Coins!")
    else:
        # Subtract 200 from coins add 1 to freezes
        coins = db_coins - 200
        freezes = db_freezes + 1
        # Update database
        db_command = f"UPDATE Users SET Coins = ?, Freezes = ? WHERE UserPK = {str(user_pk)}"
        cursor.execute(db_command, (coins, freezes))
        conn.commit()
        
        return (True, f"Freeze bought you now have {str(freezes)} freezes!")


def validate_wager(wager, db_wager, db_coins):
    #Validates the wager
    if db_wager != 0:
        return "You cannot create another wager if you already have one active!"
    elif not wager.isdigit():
        return "Input must be an integer."
    elif int(wager) > db_coins:
        return "Cannot create wager. Not enough Coins."
    elif int(wager) <= 0:
        return "Cannot create wager for less than 1 coin."
    return False


def update_wager(wager, user_pk, streak, db_coins, cursor, conn):
    #Updates wager info
    db_command_wager = "UPDATE WagerInfo SET Wager = ?, WagerDate = ?, StreakAtTimeOfWager = ?, WagerCount = 0 WHERE UserPK = ?"
    today_date = date.today()
    cursor.execute(db_command_wager, (wager, today_date, streak, user_pk))
    db_coins -= int(wager)
    
    #Updates coins info
    db_command_coins = "UPDATE Users SET Coins = ? WHERE UserPK = ?"
    cursor.execute(db_command_coins, (db_coins, user_pk))
    conn.commit()
    
    return f"Wager set for {wager} coins! Good luck!"


def create_wager(wager, db_wager, db_coins, cursor, conn, user_pk, streak):
    # Validates wager
    validation_message = validate_wager(wager, db_wager, db_coins)
    if validation_message:
        return (False, validation_message)
    else:
        # Updates wager
        return (True, update_wager(wager, user_pk, streak, db_coins, cursor, conn))
