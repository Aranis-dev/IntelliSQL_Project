import sqlite3

# Connect to the database
connection = sqlite3.connect("data.db")
cursor = connection.cursor()

# Create the Students table
cursor.execute('''
CREATE TABLE Students (
    name VARCHAR(30),
    class VARCHAR(30),
    marks INT,
    company VARCHAR(30)
)
''')

# Insert records into the Students table
cursor.execute('''INSERT INTO Students VALUES ('Sijo', 'Btech', 75, 'JSW')''')
cursor.execute('''INSERT INTO Students VALUES ('Lijo', 'Mtech', 69, 'TCS')''')
cursor.execute('''INSERT INTO Students VALUES ('Rijo', 'BSc', 79, 'WIPRO')''')
cursor.execute('''INSERT INTO Students VALUES ('Sibin', 'MSc', 89, 'INFOSYS')''')
cursor.execute('''INSERT INTO Students VALUES ('Dilsha', 'Mcom', 99, 'Cyient')''')

# Print the inserted records
print("The inserted records:")
df = cursor.execute('''SELECT * FROM Students''')

for row in df:
    print(row)

# Commit the changes and close the connection
connection.commit()
connection.close()
