import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re

# Initialize session state for persistent data
if "sql_query" not in st.session_state:
    st.session_state["sql_query"] = ""
if "results_df" not in st.session_state:
    st.session_state["results_df"] = None
if "plot_index" not in st.session_state:
    st.session_state["plot_index"] = 0
if "db_tables" not in st.session_state:
    st.session_state["db_tables"] = []

# Ensure directories exist
os.makedirs("db", exist_ok=True)
os.makedirs("static/plots", exist_ok=True)

# Mistral API Configuration
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_AGENT_URL = "https://api.mistral.ai/v1/agents/completions"
MISTRAL_API_KEY = "jDcCdZ0dkkTKEjAfVIoLWbRcmZ4ktwBs"
MISTRAL_AGENT_ID = "ag:79ec7e4f:20250328:untitled-agent:36859aa3"

def load_database_schema(db_path):
    """Loads the schema of the uploaded SQLite database and returns schema and table names."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema = ""

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema += f"Table: {table_name}\n"
        schema += ", ".join([f"{col[1].lower()} ({col[2]})" for col in columns]) + "\n\n"

    conn.close()
    return schema.strip(), [table[0] for table in tables]

def generate_sql(user_input, db_path):
    """Converts a natural language query to SQL using Mistral API, handling only SELECT queries."""
    table_schema, _ = load_database_schema(db_path)

    prompt = (
        f"Based on the following database schema, generate only a complete and executable SQL SELECT query without any explanation. "
        f"Ensure the query includes the FROM clause and necessary conditions. "
        f"If the request is unrelated to the schema or cannot be translated to a SELECT query, return 'ERROR: No relevant table found'.\n"
        f"Schema:\n{table_schema}\n"
        f"User request: '{user_input}'"
    )

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-medium",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    response = requests.post(MISTRAL_URL, headers=headers, data=json.dumps(payload))
    print(f"🟢 Sending request to Mistral with schema:\n{table_schema}")
    print(f"🟢 User Query: {user_input}")
    print(f"🟢 Mistral Response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        result = response.json()["choices"][0]["message"]["content"].strip()
        # Extract SQL query from potential code block
        sql_match = re.search(r'```sql\n(.*?)\n```', result, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
        else:
            sql_query = result.strip()

        print(f"🟢 Extracted SQL Query: {sql_query}")  # Debug log

        if sql_query == "ERROR: No relevant table found":
            return None
        if sql_query.lower().startswith("select"):
            return sql_query
        return None  # Return None for non-SELECT queries
    else:
        return f"Error: {response.status_code}, {response.text}"

def extract_python_code(response_text):
    """Extracts the Python code block from the Mistral response, ignoring explanatory text."""
    # Look for the code block starting with the first import statement
    code_start = re.search(r'^(import|from)\s', response_text, re.MULTILINE)
    if not code_start:
        return None
    
    code_start_pos = code_start.start()
    # Find the end of the code by looking for explanatory text or the end of the string
    explanatory_text = re.search(r'\n\s*This script|\n\s*Here\'s a', response_text[code_start_pos:], re.MULTILINE)
    if explanatory_text:
        code_end_pos = code_start_pos + explanatory_text.start()
    else:
        code_end_pos = len(response_text)
    
    code = response_text[code_start_pos:code_end_pos].strip()
    return code

def call_mistral_for_visualization(csv_file):
    """Uses Mistral to generate a visualization script based on CSV data."""
    with open(csv_file, "r") as f:
        csv_data = f.read()

    prompt = f"""
    You are an expert Python developer.
    Given the following CSV data, generate only a valid Python script that:
    - Sets Matplotlib to the non-interactive 'Agg' backend BEFORE ANY IMPORTS using:
    ```python
    import matplotlib
    matplotlib.use('Agg')
    ```
    - Includes all necessary imports (e.g., pandas, matplotlib.pyplot).
    - Reads the CSV file 'generated_data.csv' using pd.read_csv('generated_data.csv').
    - Creates plots (e.g., bar, scatter, box, line, word cloud,) based on the data.
    - Saves the plot as 'static/plots/plot1.png', 'static/plots/plot1.png', and so on.
    - Clears old plots from 'static/plots' before generating new ones.
    - Do NOT include any explanations, comments, or markdown formatting outside the code.

    CSV Data:
    {csv_data}
    """

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "agent_id": MISTRAL_AGENT_ID,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(MISTRAL_AGENT_URL, headers=headers, json=payload)
    print(f"🟢 Visualization Request Response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        response_text = response.json()["choices"][0]["message"]["content"].strip()
        # Extract the actual Python code
        code = extract_python_code(response_text)
        if code:
            return code
        else:
            raise Exception("No valid Python code found in Mistral response")
    else:
        raise Exception(f"Mistral API failed: {response.status_code} - {response.text}")

# Title
st.title("SQL Genie")


# Instructions
st.markdown("""
### How to Use:
1. Upload a SQLite database to start.
2. View the tables present in the uploaded database below.
3. Type a natural language query and click "Generate SQL".
4. Click "Execute Query" to see the results.
5. Click "Generate Visualization" to create plots.
6. Use the dropdown or "Next"/"Previous" buttons to view all generated plots.
7. Click "Clear" to reset outputs (database remains loaded). """)

# Database Upload
db_file = st.file_uploader("Upload SQLite Database", type=["db"])
if db_file:
    with open("db/database.db", "wb") as f:
        f.write(db_file.read())
    st.success("Database uploaded successfully!")
    # Load and display tables
    schema, table_names = load_database_schema("db/database.db")
    st.session_state["db_tables"] = table_names
    st.subheader("Tables in Uploaded Database:")
    # Display tables in a tabular format
    df_tables = pd.DataFrame(table_names, columns=["Table Name"])
    st.table(df_tables)

# Natural Language Query Input
user_query = st.text_area("Enter your natural language query")

# Generate SQL Button
if st.button("Generate SQL"):
    if not os.path.exists("db/database.db"):
        st.error("Please upload a database first!")
    else:
        sql_query = generate_sql(user_query, "db/database.db")
        if sql_query:
            st.session_state["sql_query"] = sql_query
        else:
            st.session_state["sql_query"] = "ERROR: No relevant table found"

# Display Generated SQL Query (Persistent)
if st.session_state["sql_query"]:
    st.subheader("Generated SQL Query:")
    st.code(st.session_state["sql_query"], language="sql")

# Execute Query Button
if st.button("Execute Query"):
    if not st.session_state["sql_query"] or "ERROR" in st.session_state["sql_query"]:
        st.error("Generate a valid SQL query first!")
    else:
        try:
            conn = sqlite3.connect("db/database.db")
            df = pd.read_sql_query(st.session_state["sql_query"], conn)
            st.session_state["results_df"] = df
            df.to_csv("generated_data.csv", index=False)
            conn.close()
        except Exception as e:
            st.error(f"Query Execution Failed: {str(e)}")

# Display Query Results (Persistent)
if st.session_state["results_df"] is not None:
    st.subheader("Query Results:")
    st.dataframe(st.session_state["results_df"])

# Generate Visualization Button
if st.button("Generate Visualization"):
    if not os.path.exists("generated_data.csv"):
        st.error("Execute a query first to generate results!")
    else:
        try:
            # Clear old plots
            for file in os.listdir("static/plots"):
                os.remove(os.path.join("static/plots", file))
            # Generate visualization code
            try:
                generated_code = call_mistral_for_visualization("generated_data.csv")
                # Execute the generated code directly
                exec_globals = {
                    "matplotlib": matplotlib,
                    "plt": plt,
                    "pd": pd,
                    "os": os
                }
                exec(generated_code, exec_globals)
            except Exception as e:
                st.warning(f"Mistral API visualization failed: {str(e)}. Using fallback visualization.")
                # Fallback: Hardcoded visualization
                df = pd.read_csv("generated_data.csv")
                plt.bar(df.iloc[:, 0], df.iloc[:, 1])
                plt.xlabel(df.columns[0])
                plt.ylabel(df.columns[1])
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig("static/plots/fallback_plot.png")
                plt.close()

            plots = [f for f in os.listdir("static/plots") if f.endswith(".png")]
            if plots:
                st.success("Visualizations generated successfully!")
            else:
                st.warning("No plots found in static/plots/ after generation.")
        except Exception as e:
            st.error(f"Visualization Generation Failed: {str(e)}")

# Display Plots with Dropdown and Next Button
plots = [f for f in os.listdir("static/plots") if f.endswith(".png")]
if plots:
    st.subheader("Visualizations:")
    
    # Dropdown for plot selection
    plot_options = [f"Plot {i+1}: {plot}" for i, plot in enumerate(plots)]
    selected_plot = st.selectbox("Select a plot", plot_options, index=st.session_state["plot_index"])
    st.session_state["plot_index"] = plot_options.index(selected_plot)
    
    # Display selected plot
    plot_path = os.path.join("static/plots", plots[st.session_state["plot_index"]])
    st.image(plot_path, caption=plots[st.session_state["plot_index"]], use_column_width=True)
    
    # Navigation Buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Previous Plot") and st.session_state["plot_index"] > 0:
            st.session_state["plot_index"] -= 1
            st.rerun()
    with col2:
        if st.button("Next Plot") and st.session_state["plot_index"] < len(plots) - 1:
            st.session_state["plot_index"] += 1
            st.rerun()

# Clear Button
if st.button("Clear"):
    st.session_state["sql_query"] = ""
    st.session_state["results_df"] = None
    st.session_state["plot_index"] = 0
    if os.path.exists("generated_data.csv"):
        os.remove("generated_data.csv")
    for file in os.listdir("static/plots"):
        os.remove(os.path.join("static/plots", file))
    st.success("Cleared all outputs!")
