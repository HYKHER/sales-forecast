import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="nezuko2405",
    database="retailiq"
)

print("Connected successfully!")
