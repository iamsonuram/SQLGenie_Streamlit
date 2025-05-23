# SQLGenie_Streamlit
SQLGenie is an intuitive web application that transforms natural language queries into executable SQL queries, executes them on an uploaded SQLite database, and generates visualizations for the results. Built with Streamlit and powered by the Mistral API, SQLGenie simplifies database interaction for users without deep SQL knowledge.

---

## Features

- **Natural Language Processing**: Convert plain English queries (e.g., "Show me all employees with a salary above 50000") into SQL queries using Mistral AI.
- **Database Upload**: Upload your own SQLite `.db` file to query custom datasets.
- **Query Execution**: Execute generated SQL queries and view results in a table format.
- **Visualization**: Automatically generate Matplotlib-based plots from query results, with a dropdown and navigation buttons to view multiple plots.
- **Persistent UI**: Generated SQL queries and result tables remain visible across actions until explicitly cleared.
- **Clear Functionality**: Reset outputs (queries, results, and plots) while retaining the API key and database.

---

## Tech Stack

- **Frontend & Backend**: [Streamlit](https://streamlit.io/) (Python-based UI framework)
- **SQL Generation**: [Mistral API](https://mistral.ai/) for natural language to SQL conversion
- **Visualization**: Matplotlib (via AI-generated Python scripts)
- **Database**: SQLite
- **Dependencies**: Pandas, Requests

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Git (for cloning)

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/iamsonuram/SQLGenie_streamlit
   cd SQLGenie_Streamlit

2. **Install Dependencies**: Create a virtual environment and install required packages:

     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     pip install -r requirements.txt
      ```
  
4. **Prepare Directory Structure**: Ensure the following directories exist (they’ll be created automatically on first run):
  db/ (for uploaded SQLite databases)
  static/plots/ (for generated plot images)
  
3. **Run the Application**:
  `streamlit run app.py`
  Open your browser to *http://localhost:8501* to access SQLGenie.
