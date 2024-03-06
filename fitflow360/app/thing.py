import sqlite3

conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()

DBcommand = 'SELECT * FROM Users'
cursor.execute(DBcommand)
requestData = cursor.fetchall()
DataArray = [[x for x in requestData[i]] for i in range(len(requestData))]
print(DataArray)
f = open('Usernames.txt', 'a')
for i in DataArray:
    f.write(str(i) + '\n')
f.close()