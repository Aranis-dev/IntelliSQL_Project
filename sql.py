import sqlite3

def create_and_populate_database(db_name="data.db"):
    """
    Establishes a connection to a SQLite3 database, creates a Students table,
    and inserts sample records.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Define the schema for the Students table
        table_schema = '''
        CREATE TABLE IF NOT EXISTS Students (
            Name TEXT,
            Class TEXT,
            Marks INTEGER,
            Company TEXT
        );
        '''
        cursor.execute(table_schema)
        print(f"Table 'Students' ensured in {db_name}.")

        # Check if table is empty before inserting records to avoid duplicates on re-run
        cursor.execute("SELECT COUNT(*) FROM Students;")
        if cursor.fetchone()[0] == 0:
            print("Inserting sample records into 'Students' table...")
            # Inserting multiple records
            students_data = [
                ('Sijo', 'BTech', 75, 'JSW'),
                ('John', 'MCom', 80, 'Infosys'),
                ('Alice', 'BTech', 90, 'Google'),
                ('Bob', 'BSc', 65, 'TCS'),
                ('Charlie', 'MCom', 88, 'Infosys'),
                ('Eve', 'BTech', 70, 'Wipro'),
                ('Frank', 'BSc', 55, 'HCL')
            ]
            cursor.executemany("INSERT INTO Students VALUES (?, ?, ?, ?)", students_data)
            conn.commit()
            print("Sample records inserted successfully.")
        else:
            print("Students table already contains data. Skipping insertion.")

        # Query and display all records (for verification)
        print("\nRecords in Students table:")
        df = cursor.execute('''SELECT * FROM Students''')
        for row in df:
            print(row)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print(f"Connection to {db_name} closed.")

# Corrected the if __name__ check
if __name__ == "__main__":
    create_and_populate_database()
