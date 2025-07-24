import streamlit as st
import os
import sqlite3
import google.generativeai as genai
import pandas as pd # For displaying query results nicely

# --- Configuration and API Key Initialization ---
# Ensure GOOGLE_API_KEY is set as an environment variable.
# For local development, you might set it directly in your shell or use python-dotenv.
# In a deployed environment (like Canvas), it might be provided automatically or via secrets.
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("GOOGLE_API_KEY environment variable not set. Please set it to your Gemini API key.")
    st.stop() # Stop the app if API key is missing

genai.configure(api_key=API_KEY)

# Database file name
DB_NAME = "data.db"

# --- Database Interaction Functions ---
def read_query(sql_query, db_path=DB_NAME):
    """
    Purpose: Reads results from an SQL query.
    Parameters:
        sql_query: SQL query to execute.
        db_path: Database file path.
    Functionality:
        Connects to the specified SQLite database.
        Creates a cursor object to interact with the database.
        Executes the provided SQL query.
        Fetches all the rows returned by the query.
        Commits any pending transaction to the database (important for DML).
        Closes the connection to the database.
        Returns the fetched rows and column names.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)

        # Check if it's a SELECT query to fetch results
        if sql_query.strip().upper().startswith("SELECT"):
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return columns, rows
        else:
            conn.commit() # Commit changes for INSERT, UPDATE, DELETE
            return "Query executed successfully.", None
    except sqlite3.Error as e:
        return f"Database error: {e}", None
    except Exception as e:
        return f"An unexpected error occurred: {e}", None
    finally:
        if conn:
            conn.close()

def get_sqlite_schema(db_path=DB_NAME):
    """
    Extracts the schema (table names and column details) from an SQLite database.
    This information is crucial for the LLM to generate accurate SQL.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        schema_info = {}

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table_tuple in tables:
            table_name = table_tuple[0]
            schema_info[table_name] = []

            # Get column details for each table
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            for col in columns:
                column_name = col[1]
                column_type = col[2]
                schema_info[table_name].append(f"{column_name} {column_type}")
        return schema_info
    except sqlite3.Error as e:
        st.error(f"Error extracting schema: {e}")
        return {}
    finally:
        if conn:
            conn.close()

# --- Gemini Pro Model Interaction ---
# Prompt Configuration for Converting English Questions to SQL Queries
prompt = [
    """
    You are an expert in converting English questions to SQL queries.
    Your task is to convert natural language questions into accurate SQL queries based on the provided database schema.
    Ensure the generated SQL query is syntactically correct for SQLite.
    The SQL database is named data.db and contains a table named Students with the following columns:
    - Name (TEXT)
    - Class (TEXT)
    - Marks (INTEGER)
    - Company (TEXT)

    Here are some examples:
    Example 1:
    Question: How many entries of records are present?
    SQL Query: SELECT COUNT(*) FROM Students;

    Example 2:
    Question: Tell me all the students studying in MCom class?
    SQL Query: SELECT * FROM Students WHERE Class="MCom";

    Example 3:
    Question: What is the average marks scored by students?
    SQL Query: SELECT AVG(Marks) FROM Students;

    Example 4:
    Question: Show me the name and company of students who scored more than 80 marks.
    SQL Query: SELECT Name, Company FROM Students WHERE Marks > 80;

    Example 5:
    Question: Display all records from the Students table.
    SQL Query: SELECT * FROM Students;
    """
]

def get_response(user_question, instruction_prompt):
    """
    Function Definition for Generating SQL Queries from Natural Language Questions
    Defines a function named get_response that takes two parameters:
    user_question (the query in natural language) and
    instruction_prompt (the list containing the instructional prompt for the LLM).
    """
    model = genai.GenerativeModel("gemini-pro")
    # Calls the generate_content method on the model instance, passing a list
    # containing the instructional prompt and the user's question.
    response = model.generate_content([instruction_prompt[0], user_question])
    # Returns the textual content of the generated response, cleaning up markdown.
    sql_query = response.text.strip()
    if sql_query.startswith("sql"):
        sql_query = sql_query[len("sql"):].strip()
    if sql_query.endswith(""):
        sql_query = sql_query[:-len("")].strip()
    return sql_query

# --- Streamlit UI Functions ---

# Custom CSS for styling the Streamlit app
st.markdown("""
    <style>
    .main-header {
        font-size: 3em;
        color: #4CAF50; /* Green */
        text-align: center;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .subheader {
        font-size: 1.5em;
        color: #555;
        text-align: center;
        margin-bottom: 30px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 10px 20px;
        font-size: 1.1em;
        border: none;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }
    .stTextArea>div>div>textarea {
        border-radius: 12px;
        border: 2px solid #ddd;
        padding: 15px;
        font-size: 1.1em;
    }
    .stCode {
        background-color: #f0f0f0;
        border-left: 5px solid #4CAF50;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
    }
    .data-frame-container {
        border: 1px solid #ddd;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .sidebar .sidebar-content {
        background-color: #2E2E2E; /* Dark gray for sidebar */
        color: white;
    }
    .content {
        color: white;
    }
    .tool-input {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #333; /* Dark text for input area */
    }
    .response {
        background-color: #e9e9e9;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        color: #333; /* Dark text for response area */
    }
    </style>
    """, unsafe_allow_html=True)

def page_home():
    """
    Purpose: Renders the home page of IntelliSQL.
    """
    st.markdown('<p class="main-header">Welcome to IntelliSQL!</p>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Revolutionizing Database Querying with Advanced LLM Capabilities</p>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.image("https://placehold.co/400x300/4CAF50/FFFFFF?text=Data+Warehouse+Icon", caption="Intelligent Data Management")

    with col2:
        st.markdown("""
        <div style="font-size: 1.1em; line-height: 1.6;">
        <h3 style="color:#4CAF50;">Our Offerings:</h3>
        <ul>
            <li>✨ <strong>Intelligent Query Assistance:</strong> Guides users in crafting complex SQL queries with ease.</li>
            <li>📊 <strong>Data Exploration & Insights:</strong> Translate natural language questions into SQL to uncover hidden patterns and trends.</li>
            <li>🚀 <strong>Efficient Data Retrieval:</strong> Streamline your database interaction experience.</li>
            <li>⚙ <strong>Performance Optimization:</strong> Get suggestions for optimizing query performance.</li>
            <li>💡 <strong>Syntax Suggestions:</strong> Receive real-time SQL syntax help.</li>
            <li>📈 <strong>Trend Analysis:</strong> Facilitate deep data exploration for insightful discoveries.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

def page_about():
    """
    Purpose: Renders the about page of IntelliSQL.
    """
    st.markdown('<h1 style="color:#4CAF50;">About IntelliSQL</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="content">
    <p style="font-size: 1.1em; line-height: 1.6;">
    IntelliSQL is a cutting-edge project designed to revolutionize how users interact with SQL databases.
    Leveraging advanced Large Language Model (LLM) architecture, specifically Google's Gemini Pro,
    IntelliSQL provides an intelligent and intuitive platform for database querying, data exploration,
    and insights generation.
    </p>
    <p style="font-size: 1.1em; line-height: 1.6;">
    Our mission is to empower both novice and experienced users to effortlessly craft complex SQL queries,
    optimize performance, and uncover valuable patterns within their data, all through natural language.
    </p>
    </div>
    """, unsafe_allow_html=True)
    st.image("https://placehold.co/600x300/4CAF50/FFFFFF?text=Database+Management+Logo", caption="Powered by Modern Database Technologies")


def page_intelligent_query_assistance():
    """
    Purpose: Renders the Intelligent Query Assistance page of IntelliSQL.
    """
    st.markdown('<h1 style="color:#4CAF50;">Intelligent Query Assistance</h1>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size: 1.1em; line-height: 1.6;">
    IntelliSQL guides you through crafting complex queries with ease. By understanding natural language,
    it suggests relevant SQL statements, offers syntax suggestions, and assists in optimizing query performance.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    user_question = st.text_area(
        "Enter your natural language question about the Students database:",
        "Show me all students from Infosys."
    )

    if st.button("Generate SQL & Get Results", use_container_width=True):
        if user_question:
            with st.spinner("Generating SQL query..."):
                generated_sql = get_response(user_question, prompt)
            
            st.markdown("### Generated SQL Query:")
            st.code(generated_sql, language="sql")

            if generated_sql and not generated_sql.startswith("Error"):
                with st.spinner("Executing SQL query and fetching results..."):
                    columns, data_rows = read_query(generated_sql)
                
                st.markdown("### Query Results:")
                if data_rows is not None:
                    if isinstance(columns, list): # If it's a SELECT query, columns will be a list
                        if data_rows: # Check if there are any rows returned
                            df = pd.DataFrame(data_rows, columns=columns)
                            st.markdown('<div class="data-frame-container">', unsafe_allow_html=True)
                            st.dataframe(df)
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.info("Query executed successfully, but no data found.")
                    else: # For non-SELECT queries (columns will be a message string)
                        st.success(columns) # Display the success message
                else: # An error occurred during execution (data_rows is None)
                    st.error(columns) # Display the error message
            else:
                st.error(f"Could not generate a valid SQL query: {generated_sql}")
        else:
            st.warning("Please enter a natural language question.")

    st.markdown("---")
    st.markdown("### Direct SQL Query Execution (for advanced users)")
    direct_sql_input = st.text_area("Enter SQL query directly:", height=100)
    if st.button("Execute Direct SQL", use_container_width=True):
        if direct_sql_input:
            with st.spinner("Executing direct SQL query..."):
                columns, data_rows = read_query(direct_sql_input)

            st.markdown("### Direct SQL Results:")
            if data_rows is not None:
                if isinstance(columns, list):
                    if data_rows:
                        df = pd.DataFrame(data_rows, columns=columns)
                        st.markdown('<div class="data-frame-container">', unsafe_allow_html=True)
                        st.dataframe(df)
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("Direct query executed successfully, but no data found.")
                else:
                    st.success(columns)
            else:
                st.error(columns)
        else:
            st.warning("Please enter a SQL query to execute directly.")


# --- Main Application Control ---
def main():
    """
    Purpose: Sets up the main structure and navigation of the IntelliSQL application.
    """
    st.set_page_config(
        page_title="IntelliSQL",
        page_icon="✨", # Star emoji as icon
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("""
        <style>
        .sidebar .sidebar-content {
            background-color: #2E2E2E; /* Dark gray */
            color: white;
        }
        .stRadio>label {
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

    pages = {
        "Home": page_home,
        "Intelligent Query Assistance": page_intelligent_query_assistance,
        "About IntelliSQL": page_about,
    }

    selected_page = st.sidebar.radio("Go to", list(pages.keys()))

    # Render the selected page
    pages[selected_page]()

    st.sidebar.markdown("---")
    st.sidebar.caption("IntelliSQL - Powered by Google Gemini Pro")


if _name_ == "_main_":
    main()
