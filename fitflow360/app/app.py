from functions import (
                                database_init,
                                check_username,
                                check_session,
                                get_meal_plan,
                                get_user_data,
                                get_user_pk,
                                convert_csv,
                                check_wager,
                                end_wager,
                                check_streak,
                                end_streak,
                                get_workout_days_array,
                                generate_exercise,
                                get_exercise_day_data,
                                week_day_formatting,
                                update_meal_plan,
                                get_dietary_restrictions,
                                meal_ingredient_api,
                                shopping_list_add,
                                get_graph_data,
                                log_database_update,
                                log_submit_validation,
                                meal_search_api,
                                get_recipe_url,
                                update_settings_data,
                                settings_form_validation,
                                shopping_list_formatting,
                                db_connection,
                                buy_freeze,
                                create_wager,
                                signup_form_validation,
                                streak_update
                              )

from flask import Flask, render_template, request, flash, redirect, url_for, session
from datetime import datetime, date
import requests


app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)
app.secret_key = 'hello'
app.config['SESSION_TYPE'] = 'filesystem'



database_init()
convert_csv()

@app.route('/', endpoint='index')
def login_page():
    return render_template('misc/index.html')


@app.route("/submit", methods=["POST"])
def submit():
    conn, cursor = db_connection('user_data.db')
    entered_user = request.form["Username"]
    if check_username(entered_user, conn, cursor):
        session["session_id"] = entered_user
        user_pk = get_user_pk(conn, cursor)

        # Update streak and wager if necessary.
        streak_valid = check_streak(user_pk, conn, cursor)
        if not streak_valid:
            end_streak(user_pk, conn, cursor)
        wager_valid = check_wager(user_pk, conn, cursor)
        if not wager_valid:
            end_wager(user_pk, conn, cursor)
        return redirect(url_for('home'))
    flash('Username not found. Please try again.', 'error')
    return render_template('misc/index.html')


@app.route("/home")
def home():
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    # Get User Primary Key. Set up database connection
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Get workout days
    work_date = get_workout_days_array(user_pk, conn, cursor)

    # Get current day
    day_of_week = week_day_formatting(datetime.today().weekday())

    # Get shopping list arrays
    result = shopping_list_formatting(user_pk, cursor)
    serving_size_arr, serving_type, ingredient_name_array = result

    # Get user data
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)
    wager = user_data.get("Wager", 0)

    # Initialise day array
    day_array = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return render_template('misc/home.html',
                           day_array=day_array,
                           serving_type=serving_type,
                           streak=streak,
                           freezes=freezes,
                           wager=wager,
                           work_date=work_date,
                           coins=coins,
                           day=day_of_week,
                           shopping_ingredients=ingredient_name_array,
                           shopping_quant=serving_size_arr)


@app.route('/signup')
def signup():
    return render_template('misc/signup.html')


@app.route('/signupsubmit', methods=['POST'])
def signupsubmit():
    #Connect to database
    conn, cursor = db_connection('user_data.db')
    
    # Retrieve form data
    username = request.form['Username']
    sex = request.form['dropdown-choice']
    weight = request.form['Weight']

    # Validate form data
    result = signup_form_validation(username, sex, weight, conn, cursor)
    valid_flag, validation_message_dict = result
    if valid_flag:
        for key in validation_message_dict:
            flash(validation_message_dict[key], key)
        return redirect(url_for('signup'))

    # Set up User record
    db_command = "INSERT INTO Users (Username, Weight, Sex, Streak, Freezes, Coins) VALUES (?, ?, ?, 0, 0, 0)"
    cursor.execute(db_command, (username, weight, sex))
    conn.commit()

    # Update session
    session["session_id"] = username
    user_pk = get_user_pk(conn, cursor)

    # Set up MealRestrictions records
    db_command = "INSERT INTO MealRestrictions (UserPK, Restriction) VALUES (?, ?)"
    restriction_list = ['Vegetarian', 'Vegan', 'Celery', 'Crustaceans',
                        'Eggs', 'Dairy', 'Fish', 'Lupin', 'Milk', 'Molluscs',
                        'Mustards', 'SoyBeans', 'Peanuts', 'SesameSeeds',
                        'Gluten', 'Sulphites']
    dietary_restrictions = [item for item in restriction_list if request.form.get(item) is not None]
    for i in dietary_restrictions:
        cursor.execute(db_command, (user_pk, i))
        conn.commit()

    conn.close()
    return redirect(url_for('index'))


@app.route("/settings")
def settings():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    
    # Connect to database
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Get dietary restrictions
    dietary_restriction_arr = get_dietary_restrictions(user_pk, conn, cursor)

    # Get user data
    user_data = get_user_data(user_pk, cursor)
    username = user_data.get("Username", 'N/A')
    weight = user_data.get("Weight", 0.0)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)
    sex = user_data.get("Sex", 0)

    return render_template('misc/settings.html',
                           freezes=freezes,
                           streak=streak,
                           sex=sex,
                           username=username,
                           weight=weight,
                           coins=coins,
                           dietary_restriction_arr=dietary_restriction_arr
                           )


@app.route('/settingssubmit', methods=['POST'])
def settingssubmit():
    # Validate session
    username = check_session('session_id')
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    #Connect to database
    conn, cursor = db_connection('user_data.db')

    user_pk = get_user_pk(conn, cursor)
    restriction_list = ['Vegetarian', 'Vegan', 'Celery', 'Crustaceans', 'Eggs', 'Dairy', 'Fish', 'Lupin', 'Milk', 'Molluscs', 'Mustards', 'SoyBeans', 'Peanuts', 'SesameSeeds', 'Gluten', 'Sulphites']

    # Get form data
    username_change = request.form['username']
    sex = request.form['dropdown-choice']
    weight = request.form['weight']
    dietary_restrictions = [item for item in restriction_list if request.form.get(item) is not None]

    # Validate form
    valid_flag, settings_form_dict = settings_form_validation(username_change, username, sex, weight, conn, cursor)
    if valid_flag:
        for key in settings_form_dict:
            flash(settings_form_dict[key], key)
        return redirect(url_for('settings'))

    # Update form data
    update_settings_data(username_change, weight, sex, user_pk, dietary_restrictions, restriction_list, conn, cursor)

    # Update dietary restrictions
    return redirect(url_for('home'))

@app.route("/shop")
def shop():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    
    # Database Connection
    conn, cursor = db_connection('user_data.db')

    # Get user data
    user_pk = get_user_pk(conn, cursor)
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)

    conn.close()
    return render_template('misc/shop.html',
                           streak=streak,
                           freezes=freezes,
                           coins=coins
                           )

@app.route('/shopbuy', methods=['GET'])
def shopbuy():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    conn, cursor = db_connection('user_data.db')

    # Set up user data (Needs to be done beforehand for shop information)
    user_pk = get_user_pk(conn, cursor)
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    db_freezes = user_data.get("Freezes", 0)
    db_coins = user_data.get("Coins", 0)
    db_wager = user_data.get("Wager", 0)

    if 'Freeze' in request.args:
        # Buy a freeze
        freeze_message = buy_freeze(db_coins=db_coins,
                                    db_freezes=db_freezes,
                                    user_pk=user_pk,
                                    cursor=cursor,
                                    conn=conn
                                    )
        flash(freeze_message[1])
    elif 'Wager' in request.args:
        # Create a wager
        wager = request.args.get('Wager')
        wager_message = create_wager(
                                    wager=wager,
                                    db_wager=db_wager,
                                    db_coins=db_coins,
                                    user_pk=user_pk,
                                    streak=streak,
                                    cursor=cursor,
                                    conn=conn
                                    )
        flash(wager_message[1])

    conn.close()
    return redirect(url_for('shop'))


@app.route('/meal')
def meal():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    # Connect to database
    conn, cursor = db_connection('user_data.db')

    # Get user primary key
    user_pk = get_user_pk(conn, cursor)

    # Get meal plan array
    meal_plan_arr = get_meal_plan(user_pk, conn, cursor)

    # Get user data
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)

    conn.close()
    return render_template('meal/meal.html',
                           streak=streak,
                           freezes=freezes,
                           coins=coins,
                           meal_plan_arr=meal_plan_arr
                           )


@app.route('/generatemeal')
def generatemeal():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    # Make database connection
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Get restrictions
    db_command = f"SELECT Restriction FROM MealRestrictions WHERE UserPK = {user_pk}"
    cursor.execute(db_command)
    restrictions = cursor.fetchall()

    # Format restrictions
    exclude_arr = [x[0] for x in restrictions if x[0].lower() not in ['vegan', 'vegetarian']]
    diet_arr = [x[0] for x in restrictions if x[0].lower() in ['vegan', 'vegetarian']]
    exclude_tags = ','.join(exclude_arr)
    diet_tags = ','.join(diet_arr)

    # Get saved checkbox data
    check_box_data = []
    for i in range(21):
        check_box_data.append(request.args.get(str(i)))

    # Format URL
    api_key = "d35c0fc0abd64e91b6c3c0cb305de419"
    url = f"https://api.spoonacular.com/mealplanner/generate?timeFrame=week&apiKey= \
        {api_key}&exclude={exclude_tags}&diet={diet_tags}"

    # Update Meal Plan
    update_meal_plan(url, user_pk, check_box_data, conn, cursor)

    conn.close()
    return redirect(url_for('meal'))


@app.route('/ingredient')
def ingredient():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    # Connect to database
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    meal_name = request.args.get("MealPlanName")
    if meal_name is not None:
        session["IngredientMealName"] = meal_name
    elif check_session('IngredientMealName'):
        meal_name = session["IngredientMealName"]
    else:
        return redirect(url_for('meal'))

    # Get Meal ID for API
    db_command = f"SELECT APIMealID FROM Meals WHERE MealName = '{meal_name}'"
    cursor.execute(db_command)
    api_meal_id = cursor.fetchone()

    # Format ingredient arrays
    api_key = "d35c0fc0abd64e91b6c3c0cb305de419"
    url = f'https://api.spoonacular.com/recipes/{str(api_meal_id[0])}/ingredientWidget.json?&apiKey={api_key}'
    url_request = requests.get(url).json()
    data = meal_ingredient_api(url_request)
    ingredient_name_array, serving_size_arr, serving_type = data

    # Get recipe url
    url = f'https://api.spoonacular.com/recipes/{str(api_meal_id[0])}/information?includeNutrition=false&apiKey={api_key}'
    url_request = requests.get(url).json()
    recipe_link = get_recipe_url(url_request)

    # Get user data
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)

    conn.close()
    return render_template('meal/ingredients.html',
                           streak=streak,
                           freezes=freezes,
                           coins=coins,
                           ingredient_name_array=ingredient_name_array,
                           serving_size_arr=serving_size_arr,
                           serving_type=serving_type,
                           recipe_link=recipe_link
                           )


@app.route('/searchmeal', methods=["GET"])
def searchmeal():
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    # Connect to database
    conn, cursor = db_connection('user_data.db')

    # Get user data
    user_pk = get_user_pk(conn, cursor)
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)

    meal_position = request.args.get("EditMealButton")
    if meal_position is not None:
        session["MealPosition"] = meal_position

    if not check_session('IDList'):
        return render_template('meal/searchmeal.html',
                               streak=streak,
                               freezes=freezes,
                               coins=coins)
    else:
        id_list = session.pop('IDList')
        name_list = session.pop('NameList')
        return render_template('meal/searchmeal.html',
                               streak=streak,
                               freezes=freezes,
                               coins=coins,
                               NameList=name_list,
                               IDList=id_list)


@app.route('/searchmealform', methods=["POST"])
def searchmealform():
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    # GET FORM DATA FROM SEARCH
    search_data = request.form['SearchData']

    # DISPLAY EVERY Response FROM SPOONACULAR
    api_key = "d35c0fc0abd64e91b6c3c0cb305de419"
    url = f'https://api.spoonacular.com/recipes/autocomplete?number=25&apiKey={api_key}&query={search_data}'
    request_data = requests.get(url).json()
    data = meal_search_api(request_data)
    print(data)
    id_list, name_list = data

    # IF NO Responses DISPLAY "NO ResponseS"
    session["IDList"] = id_list
    session["NameList"] = name_list
    return redirect(url_for('searchmeal'))


@app.route('/searchmealselect', methods=["GET"])
def searchmealselect():
    # Verify session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    # Connect to database, get UserPK
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Get form data and meal position
    meal_position = session["MealPosition"]
    form_data = request.args.get('SearchButton').split(',,')
    api_meal_id = form_data[0]
    meal_name = form_data[1]

    # Update meal on selecting a meal
    db_command = "UPDATE Meals SET MealName = ?, APIMealID = ? WHERE UserPK = ? AND MealPosition = ?"
    cursor.execute(db_command,
                   (meal_name,
                    api_meal_id,
                    user_pk,
                    meal_position
                    )
                   )
    conn.commit()
    conn.close()
    return redirect(url_for('meal'))


@app.route('/shoppinglist')
def shoppinglist():
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    
    # Connect to database
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Format shopping list into respective arrays
    result = shopping_list_formatting(user_pk, cursor)
    serving_size_arr, serving_type, ingredient_name_array = result

    # Get user data
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)

    conn.close()
    return render_template('meal/shoppinglist.html',
                           streak=streak,
                           freezes=freezes,
                           coins=coins,
                           IngredientNameArray=ingredient_name_array,
                           servingSizeArr=serving_size_arr,
                           servingType=serving_type
                           )


@app.route('/shoppinglistadd', methods=["GET"])
def shoppinglistadd():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    
    # Make user connection
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Get form data
    form_data = request.args.get("AddShoppingList")
    # Format form data into arrays
    form_data_arr = form_data.split(",,")
    ingredient_name = form_data_arr[0]
    serving_size = form_data_arr[1]
    serving_type = form_data_arr[2]

    # Insert Into Shoppinglist
    shopping_list_add(user_pk,
                      cursor,
                      conn,
                      ingredient_name,
                      serving_size,
                      serving_type
                      )

    conn.close()
    return redirect(url_for("ingredient"))

@app.route('/shoppinglistremove')
def shoppinglistremove():
    # Validate session
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    
    # Connnect to database
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Get form data
    ingredient_name = request.args.get('FormButton')

    # Delete item from shopping list
    db_command = f"DELETE FROM SHOPPING_LIST WHERE UserPK = + {str(user_pk)} AND IngredientName = '{ingredient_name}'"
    cursor.execute(db_command)
    conn.commit()
    conn.close()
    return redirect(url_for('shoppinglist'))


@app.route('/exercise') # Main exercise page.
def exercise():
    if not check_session('session_id'):
        flash('Please log in')
    elif not check_session('selectedday'):
        session['selectedday'] = 0

    # Database connection
    conn, cursor = db_connection('user_data.db')

    date_today = week_day_formatting(date.today().weekday())
    user_pk = get_user_pk(conn, cursor)

    # Get days of workout
    work_date = get_workout_days_array(user_pk, conn, cursor)

    # Get selected day data
    selected_day = session['selectedday']
    selected_day_data = get_exercise_day_data(user_pk, selected_day, conn, cursor)[1::]

    # Get today's data
    today_data = get_exercise_day_data(user_pk, date_today, conn, cursor)[1::]
    
    # Get user info
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)

    conn.close()
    return render_template('exercise/exercise.html',
                           streak=streak,
                           freezes=freezes,
                           coins=coins,
                           work_date=work_date,
                           day=date_today,
                           selected_day_data=selected_day_data,
                           today_data=today_data
                           )


@app.route('/exercisedays', methods=['GET']) # On day selection.
def exercisedays():
    if not check_session('session_id'):
        flash('Please log in')
    session['selectedday'] = int(request.args.get('SelectDay'))
    return redirect(url_for('exercise'))


@app.route('/exercisegen') # On press of Generate Exercise button.
def exercisegen(): 
    # Validate sessions
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))
    elif not check_session('selected_day') and check_session('selected_day') != 0:
        return redirect(url_for('exercise'))
    else: # Validation of selected day
        selected_day = session['selectedday']

    #Connect to database
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Generates Exercise
    generate_exercise(user_pk, selected_day, conn, cursor)
    return redirect(url_for('exercise'))


@app.route('/log', endpoint = 'log')
def exerciselog():
    # Validate the session.
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    # Set up database connection.
    conn, cursor = db_connection('user_data.db')

    # Get user info
    user_pk = get_user_pk(conn, cursor)
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)

    return render_template('exercise/exerciselog.html',
                            freezes = freezes,
                            streak = streak,
                            coins = coins
                          )


@app.route('/logsubmit', methods=['POST']) # On submission of form data for log
def logsubmit():
    # Validate session
    if not check_session('session_id'):
      flash('Please log in')
      return redirect(url_for('index'))

    # Connect to database
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)
    
    # Get user info
    user_data = get_user_data(user_pk, cursor)
    coins = user_data.get("Coins", 0)
    streak = user_data.get("Streak", 0)
    # Get form data
    difficulty = request.form['Difficulty']
    weight = request.form['Weight']
    diary = request.form['Diary']
    print(request.form['Weight'])

    # Validate log form data
    return_value = log_submit_validation(weight, difficulty)
    if return_value:
        print(return_value)
        flash(return_value[0], return_value[1])
        return redirect(url_for('log'))

    streak_update(user_pk, streak, conn, cursor)
    log_database_update(weight, coins, user_pk, diary, difficulty, conn, cursor)

    

    conn.close()
    return redirect(url_for('exercise'))


@app.route('/graph')
def exercisegraph():
    if not check_session('session_id'):
        flash('Please log in')
        return redirect(url_for('index'))

    # Database connection
    conn, cursor = db_connection('user_data.db')
    user_pk = get_user_pk(conn, cursor)

    # Get graph data, and diary data
    graph_data, diary_data = get_graph_data(user_pk, cursor)

    # Get user data
    user_data = get_user_data(user_pk, cursor)
    streak = user_data.get("Streak", 0)
    freezes = user_data.get("Freezes", 0)
    coins = user_data.get("Coins", 0)
    if len(diary_data) == 0 or len(graph_data) == 0:
        return redirect(url_for('exercise'))
    return render_template('exercise/graphscreen.html',
                            freezes = freezes,
                            streak = streak,
                            coins = coins,
                            diary_data=diary_data,
                            graph_data=graph_data
                          )

if __name__ == "__main__":  # Makes sure this is the main process
    app.run(  # Starts the site
        host='0.0.0.0',
        port=8080,
        debug=True
    )
