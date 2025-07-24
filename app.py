import streamlit as st
import os
import sqlite3
import google.generativeai as genai
# Configure the API key
api_key = os.getenv('API_KEY')
if api_key is None:
    st.error("API key not found. Please set the API_KEY environment variable.")
else:
    genai.configure(api_key=api_key)
# Define the prompt for the model
prompt = [
    """
    You are an expert in converting English questions to SQL queries!
    The SQL database has the name STUDENTS and has the following columns - NAME, CLASS, 
    MARKS, COMPANY. \n\nFor example 1 - How many entries of the record are present?
    The SQL command will be something like this: SELECT COUNT(*) FROM STUDENTS;
    \nExample 2 - Tell me all the students studying in MCom class?
    The SQL command will be something like this: SELECT * FROM STUDENTS
    WHERE CLASS = "MCom";
    """
]
# Initialize the model outside the function
model = genai.GenerativeModel("gemini-pro")
def get_response(que, prompt):
    response = model.generative_content([prompt[0], que])
    return response.text
