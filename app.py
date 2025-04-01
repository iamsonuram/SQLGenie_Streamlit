import streamlit as st
import sqlite3
import pandas as pd
import os
import subprocess
from mistral_api import generate_sql, call_mistral_for_visualization

# Initialize session state for persistent data
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""
if "sql_query" not in st.session_state:
    st.session_state["sql_query"] = ""
if "results_df" not in st.session_state:
    st.session_state["results_df"] = None
if "plot_index" not in st.session_state:
    st.session_state["plot_index"] = 0

# Ensure directories exist
os.makedirs("db", exist_ok=True)
os.makedirs("static/plots", exist_ok=True)

# Title
st.title("SQL Genie")

# Instructions
st.markdown("""
### How to Use:
1. Enter your Mistral API key and upload a SQLite database.
2. Type a natural language query and click "Generate SQL".
3. Click "Execute Query" to see the results.
4. Click "Generate Visualization" to create plots.
5. Use the dropdown or "Next"/"Previous" buttons to view all generated plots.
6. Click "Clear" to reset outputs (API key and database remain loaded).
""")

# API Key Input
api_key = st.text_input("Mistral API Key", type="password", value=st.session_state["api_key"])
if api_key:
    st.session_state["api_key"] = api_key
    st.success("API Key loaded!")

# Database Upload
db_file = st.file_uploader("Upload SQLite Database", type=["db"])
if db_file:
    with open("db/database.db", "wb") as f:
        f.write(db_file.read())
    st.success("Database uploaded successfully!")

# Natural Language Query Input
user_query = st.text_area("Enter your natural language query")

# Generate SQL Button
if st.button("Generate SQL"):
    if not st.session_state["api_key"]:
        st.error("Please enter a Mistral API key first!")
    elif not os.path.exists("db/database.db"):
        st.error("Please upload a database first!")
    else:
        sql_query = generate_sql(user_query, st.session_state["api_key"], "db/database.db")
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
            # Generate new plots
            generated_code = call_mistral_for_visualization("generated_data.csv")
            result = subprocess.run(
                ["python", "plot.py"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                st.error(f"Plot script failed: {result.stderr}")
            else:
                st.success("Visualizations generated!")
                plots = [f for f in os.listdir("static/plots") if f.endswith(".png")]
                if not plots:
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
    
    # Next Button
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Previous Plot") and st.session_state["plot_index"] > 0:
            st.session_state["plot_index"] -= 1
            st.rerun()  # Rerun to update the displayed plot
    with col2:
        if st.button("Next Plot") and st.session_state["plot_index"] < len(plots) - 1:
            st.session_state["plot_index"] += 1
            st.rerun()  # Rerun to update the displayed plot

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

