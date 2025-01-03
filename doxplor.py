# -*- coding: utf-8 -*-
"""doxplor.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ZGjno77gI4X_1E3mIssGWi79lb-6u1PT
"""

# #installing Required Libraries
# !pip install langchain pyodbc sqlalchemy langchain-community pymssql langgraph
# !pip install google.generativeai langchain-google-genai langchain-groq

# from google.colab import userdata
# openai_api_key = userdata.get('OPENAI_API_KEY')
# gemini_api_key = userdata.get('GEMINI_API_KEY')
import streamlit as st
st.set_page_config(layout="wide")
st.title("DOXPLOR")
st.divider()

#importing Libraries
from langchain.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
import numpy as np
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from typing import Union, List
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
from langchain_groq import ChatGroq
from langchain.agents.output_parsers import ReActSingleInputOutputParser
import base64
from langchain.schema import HumanMessage
import os
import re
from typing import Annotated, Literal
from langchain_core.messages import FunctionMessage
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# #loading the csv
# #laptop_price = pd.read_csv('/content/laptop_price.csv',encoding='latin-1')
# input_dataset = pd.read_csv('/content/laptop_price.csv',encoding='latin-1')
# #creating a sqlite3 connection
# conn = sqlite3.connect('input_data.sqlite')
# #laptop_price.to_sql('laptop_price',conn,if_exists='replace',index=False)
# input_dataset.to_sql('input_dataset',conn,if_exists='replace',index=False)

import pandas as pd
import sqlite3
import os
#################################APIKeY################################################
with st.sidebar:
    gemini_api_key = st.text_input("Gemini API Key", key="gemini_api_key", type="password")
    #GROQ_API_KEY = st.text_input("GROQ API KEY", key="llama_api_key", type="password")
    #OPENAI_API_KEY = st.text_input("OPENAI API KEY", key="openai_api_key", type="password")
    
#################################APIKEY################################################

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
query = st.text_input(label='Enter your query here:')

if st.button("PROCEED") and query and uploaded_file and (gemini_api_key):
   #loading the csv
  input_dataset = pd.read_csv(uploaded_file,encoding='latin-1')
  input_dataset.columns = input_dataset.columns.str.strip()
  print(input_dataset.head())
  #creating a sqlite3 connection
  conn = sqlite3.connect('input_dataset.sqlite',check_same_thread=False)
  input_dataset.to_sql('input_dataset',conn,if_exists='replace',index=False)


# # Function to read CSV and save as SQLite table dynamically
# def save_csv_to_sqlite(file_path, conn):
#     # Extract the base name of the file (without directory and extension)
#     table_name = os.path.splitext(os.path.basename(file_path))[0]

#     # Load the CSV into a DataFrame
#     globals()[table_name]  = pd.read_csv(file_path, encoding='latin-1')

#     # Save the DataFrame to SQLite with the dynamic table name
#     globals()[table_name] .to_sql(table_name, conn, if_exists='replace', index=False)
#     print(f"Table '{table_name}' created successfully.")
#     #return {table_name:pd.read_csv(file_path, encoding='latin-1')}

# Example usage
#conn = sqlite3.connect('input_data.sqlite',check_same_thread=False)

# # List of files to upload
# file_paths = ['/content/Himalayan_Expeditions.csv']

# # Dynamically process each file
# for file_path in file_paths:
#     save_csv_to_sqlite(file_path, conn)


# Close the SQLite connection
#conn.close()



# cur = conn.cursor()
# cur.execute("select name FROM sqlite_master WHERE type='table';")
# tables = cur.fetchall()
# tables

# input_dataset.head()

  def ListTables(state,conn = conn):
    print('LISTING AVAILABLE TABLES')
    cur = conn.cursor()
    cur.execute("select name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    return  {'messages': [FunctionMessage(name="ListTables", content=str(tables))]}
  # cur.execute("select name FROM sqlite_master WHERE type='table';")
  # tables = cur.fetchall()
  # tables
  def get_table_schema(state, conn=conn):
      """
      Retrieves the schema of a given table using the provided connection.

      Args:
          table_name: The name of the table.
          connection: The database connection object.

      Returns:
          A string representing the CREATE TABLE statement for the table,
          including a comment with a few example rows.  Returns an error message
          if the table is not found.
      """
      print('GETTING TABLE SCHEMA')
      messages = state['messages']
      user_question = messages[0].content
      tables = messages[-1].content

      try:
          model = ChatGoogleGenerativeAI(model='gemini-1.5-flash',api_key=gemini_api_key)
          prompt = PromptTemplate(template=""" You will provided with string that contains the table name along with some special characters like '[,(,)]'. From that, you have to just answer
                                          just the table name.
                                        example:
                                        input = '[('input_dataset',)]'
                                        your response = 'input_dataset'

                                        Instructions to follow:
                                        1) Do not give any extra information other than the table name. you response should only contain table name.

                                        Sql Schema:
                                        {tables}

                                        """,
                            input_variables=["tables"])
          prompt = prompt.format(tables=tables)
          messages = [{"role": "user", "content": prompt}]
          table_name = model.invoke(input=messages).content
          print(table_name)
          cur = conn.cursor()
          cur.execute(f"PRAGMA table_info({table_name})")
          schema = cur.fetchall()

          create_table_statement = f"CREATE TABLE {table_name} (\n"
          for column in schema:
              column_name = column[1]
              column_type = column[2]
              create_table_statement += f'\t"{column_name}" {column_type}, \n'
          create_table_statement = create_table_statement[:-2] + "\n)"

          # Add sample data as a comment
          cur.execute(f"SELECT * FROM {table_name} LIMIT 3")
          sample_rows = cur.fetchall()

          comment = "\n/*\n3 rows from " + table_name + " table:\n"
          if sample_rows:
            # Get column names for the header
            column_names = [description[0] for description in cur.description]
            comment += "\t" + "\t".join(column_names) + "\n"
            for row in sample_rows:
                comment += "\t" + "\t".join(map(str,row)) + "\n"
          else:
            comment += "Table is empty"
          comment += "*/"

          create_table_statement += comment
          print(create_table_statement)
          return {'messages': [FunctionMessage(name="get_table_schema", content=str(create_table_statement))]}
      except sqlite3.OperationalError:
          return f"Error: Table '{table_name}' not found."

  def Generate_sqlcommand(state):
    print('GENERATING SQL COMMAND')
    messages = state['messages']
    user_question = messages[0].content
    schema = messages[-1].content

    prompt = PromptTemplate(template=""" You are an expert in generating SQL queries/normal responses based on the given question and schema provided.


                                      **Instructions to follow:**
                                        1. If Any question that is related to structure or schmea of the dataset,just return the **SQL Schema** structure exactly as provided below. Do not create or modify the schema on your own or suggest any SQL queries.
                                        2. If the user asks for the description/details/columns of the dataset, return the schema exactly as provided in the input. Do not create or suggest any SQL queries.
                                        3. If the user asks for an SQL query, only return the SQL query without any additional information or formatting characters (like ```, etc.).
                                        4. Always use the exact table name and schema provided in the input. Do not assume or modify them.

                                        example questions and responses:

                                        Question1 : What are the numerical/categorical columns in the schema?
                                        Response: {schema}

                                        Question2 : What is the dataset about/explain the dataset/breif explanation of the dataset?
                                        Response: {schema}

                                        **Question:**
                                        {question}

                                        **SQL Schema:**
                                        {schema}
                                        """,
                            input_variables=["schema","question"])

    prompt = prompt.format(schema=schema,question=user_question)
    messages = [{"role": "user", "content": prompt}]
    model = ChatGoogleGenerativeAI(model='gemini-1.5-flash',api_key=gemini_api_key)
    response = model.invoke(input=messages)
    return {'messages':[response]}

  def execute_sqlcommand(state,conn=conn):
    print('EXECUTING SQL COMMAND')
    messages = state['messages']
    user_question = messages[0].content
    sql_command = messages[-1].content
    cur = conn.cursor()
    try:
      if 'CREATE TABLE input_dataset' in sql_command:
        return {'messages': [FunctionMessage(name="execute_sqlcommand", content=sql_command)]}
      else:
        cur.execute(sql_command)
        rows = cur.fetchall()
        return  {'messages': [FunctionMessage(name="execute_sqlcommand", content=str(rows))]}
    except sqlite3.OperationalError:
      return "Error in executing sql command."



  def generate_response(state):
    print('GENERATING RESPONSE')
    messages = state['messages']
    user_question = messages[0].content
    result = messages[-1].content
    model = ChatGoogleGenerativeAI(model='gemini-1.5-flash',api_key=gemini_api_key,temperature = 0 )
    prompt = PromptTemplate(template=""" You are expert in generating meaningful text based on the user question and the result.


                                        Instructions to follow:
                                        1) Just refer the user question and result to generate the response.
                                        2) dont generalize the question  and result to all the datasets, consider The given question and result is only related to a certain table,
                                        so you dont have to mention about otherdatasets and tables.
                                        3) if the given result contains table, then print the table in html format.
                                        4) If user asks the description or details of the dataset, refer the schema and explain what is the dataset about breifly.
                                        5) dont mention the 'input_dataset' table explicitly in your response. 
                                        question:
                                        {question}

                                        result:
                                        {result}

                                        """,
                            input_variables=["result","question"])

    prompt = prompt.format(result=result,question=user_question)
    messages = [{"role": "user", "content": prompt}]
    response = model.invoke(input=messages)
    return {'messages':[response]}


  def query_check(state) -> Literal['Success','Failure']:
    """ This will check the output from the execute sql command function
    and check if its correct according to the user question.

    input : Takes State(BaseMessage Format) as input.
    Output : Returns 'yes' or 'no' based on the relevency check
    """
    print("---CALL QUERY CHECKER---")
    # class grade(BaseModel):
    #   """Binary score for relevance check."""
    #   binary_score: str = Field(description="Relevance score 'yes' or 'no'")
    # model = ChatGoogleGenerativeAI(model='gemini-1.5-flash',api_key=gemini_api_key)
    # llm_with_tool = model.with_structured_output(grade)
    messages = state['messages']
    user_question = messages[0].content
    last_message = messages[-1].content

    if 'Error' in last_message:
      return 'Failure'
    else:
      return 'Success'

  def checker(state) ->  Literal['YES','NO']:
    """ This Function is used to check if the user question can be visualized. If yes, this will give output as 'YES" in String format
        or 'NO' otherwise."""
    messages = state['messages']
    user_question = messages[0].content
    last_message = messages[-1].content
    print(user_question)
    print(last_message)
    class grade(BaseModel):
      """Binary score for relevance check."""
      binary_score: str = Field(description="Relevance score 'yes' or 'no'")
    model = ChatGoogleGenerativeAI(model='gemini-1.5-pro',api_key=gemini_api_key)
    llm_with_tool = model.with_structured_output(grade)
    prompt = PromptTemplate(template=""" You are an expert data analyst. Your task is to decide if a user query about a database table needs visualization.

                                        **Guidelines:**
                                          1. Respond **"yes"** if the query involves trends, patterns, comparisons, distributions,proportions or relationships that require visual representation.
                                            - Example: "Compare sales trends across regions."
                                          2. Respond **"no"** if the query can be answered clearly with a single number, list, or text, or if it cannot be visualized.
                                            - Example 1: "How many Apple laptops with more than 15.6 screen size?"
                                            - Example 2: "Explain me about the dataset"/"what is this dataset about?".

                                            Only provide "yes" or "no" as your answer.


                                        Instructions to follow:
                                        1) Just refer the user question and Table Schema to generate the response.
                                        2) you should either respond 'YES' or 'NO'

                                        question:
                                        {question}

                                        schema:
                                        {schema}

                                        """,
                            input_variables=["result","question"])
    
    prompt = prompt.format(schema = last_message,question=user_question)
    print(prompt)
    messages = [{"role": "user", "content": prompt}]
    response = llm_with_tool.invoke(input=messages)
    # Validate response
    if response is None:
        print("Error: Model response is None.")
    print("Model Response:", response)
    score = response.binary_score
    if score.lower() == 'yes':
      print('Yes, the question can be visualized')
      return 'YES'
    elif score.lower() == 'no':
      print('No, the question cant be visualized (or) doesnt need any visualization')
      return 'NO'



  def visualize_data(state):
    """ use this tool in case if user wants to visualize the data,
    input to this tool must be the Table Schema from 'InfoSQLDatabaseTool'
    and the user's input question that is required to visualize the data from 'user_input' variable."""
    messages = state['messages']
    user_question = messages[0].content
    table_schema = messages[-1].content
    # Separate schema from the question
    # schema_start = table_schema.find("CREATE TABLE")
    # schema_end = table_schema.find("*/") + 2  # Include the closing comment
    # df_schema = table_schema[schema_start:schema_end].strip()
    # question = table_schema[schema_end:].strip()
    # print(f'{schema_start,schema_end}')
    # print(f'Schema :{df_schema}')
    # print(f'Question :{question}')

    #image_details
    img_path = 'C:/Users/naren/Downloads'
    image_filename = f"{img_path}/plot.jpeg"
    if os.path.exists(image_filename):
      os.remove(image_filename)
    if not os.path.exists(img_path):
      os.makedirs(img_path)

    # data = df.strip().split('\n')
    # headers = [col.strip() for col in data[2].split('|') if col.strip()]
    # rows = [[cell.strip() for cell in row.split('|') if cell.strip()] for row in data[4:]]
    # # Create a DataFrame
    # df = pd.DataFrame(rows, columns=headers)
    # print(df)
    # df_schema = dict(df.dtypes)
    #llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash',google_api_key=GEMINI_API_KEY)
    #llm = ChatGroq(model='llama-3.1-70b-versatile',api_key=GROQ_API_KEY, temperature=0)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_api_key)
    prompt_template = PromptTemplate(
          template="""You are an expert in visualizing data using Matplotlib, Seaborn, or Plotly. Your response should consist solely of the visualization command, without any additional text following or before the command.

  You will be provided with the following:
  1. **DataFrame Schema**: The structure of the data you will be visualizing.
  2. **User Question**: The specific user input question.

  ### Instructions:
  - **Dont Assume any data by creating your own dataframe or example data on your own. Just give the seaborn/matplotlib command by referring the table schema.**
  - **Use the Provided Table Name**: Always refer to the table name from the provided `sql_db_schema`. Do not create or use any other table names (e.g., 'df').
  - **Determine the Best Plot Type**: If the type of visualization is not specified in the question, select the most suitable plot based on the available schema.
  - **Specific Chart Requests**: If the user specifies a particular type of chart (e.g., pie chart), respond with the command for that specific plot only.
  - **Label Alignment**: Ensure proper alignment of x and y labels with appropriate spacing in the commands.
  - **Output Format**: Do not include any markdown characters (e.g., ```, ", etc.) at the beginning or end of your response. Your response should contain only the command.
  - **Column Selction** : You should not whole dataset while plotting, you should be able to selectively choose the columns by referring the provided table schema.

  ### Suggested Plot Types:
  - **Box Plot**: For checking outliers in any column.
  - **Line Plot**: For examining trends in a column over a specified period.
  - **Bar Plot/KDE Plot**: For analyzing the distribution of a column.
  - **Scatter Plot**: For investigating relationships between two numerical columns.
  - **Pie Chart**: For displaying proportions of a categorical column.
  - **Heatmap**: For assessing correlations between numerical columns.

  ------------------------------------------------------
  **Table Schema**:
  \n\n{df_schema}\n\n
  ------------------------------------------------------
  **User Question**:
  \n\n{question}\n\n
  ------------------------------------------------------
  """
  ,
          input_variables=["df_schema","question"]
      )
    #Here is the query given : \n\n{query}\n\n
    prompt = prompt_template.format(df_schema=table_schema,question = user_question)
    messages = [{"role": "user", "content": prompt}]
    #print(prompt)
    response = llm.invoke(input=messages)
    command= response.content
    command = command.replace("```python", "").replace("```","").strip()
    save_command = f"\nplt.savefig('{img_path}/plot.jpeg', bbox_inches='tight')\n"  # Specify your desired filename and format
    if 'plt.show()' in command:
      save_command = command.replace("plt.show()", f"{save_command}\nplt.show()")
    else:
      save_command = command+save_command
    print(save_command)


    # Execute the save command
    exec(save_command)
    plot_img = plt.imread(f'{img_path}/plot.jpeg')
    # Function to encode the image
    def encode_image(image_path):
      with open(f'{image_path}/plot.jpeg', "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    plot_base64 = encode_image(img_path)
    #prompt for image summary
    image_prompt = """
      You are expert in analyzing the given plot with respect to the given question. \n
      You may be provided with box plots, pie charts, bar graphs, line plots and many more. \n
      Your Job is to analyze the plot and answer according to the given question without leaving any important information. \n
      """
    message = HumanMessage(
                  content=[
                      {"type": "text", "text": image_prompt},
                      {"type": "text","text":user_question},
                      {
                          "type": "image_url",
                      "image_url": {"url": f"data:image/jpeg;base64,{plot_base64}"},
                      },
                  ]
              )


    # image_prompt = image_prompt.format(plot_image=plot_base64,question=question)
    # img_messages = [{"role": "user", "content": image_prompt}]
    # response = image_llm.invoke(input=img_messages)
    response = llm.invoke([message])

    return {'messages':[response]}

  class AgentState(TypedDict):
      # The add_messages function defines how an update should be processed
      # Default is to replace. add_messages says "append"
      messages: Annotated[Sequence[BaseMessage], add_messages]

  from langgraph.graph import END,START,StateGraph

  workflow = StateGraph(AgentState)

  #defining nodes
  workflow.add_node('List tables',ListTables)
  workflow.add_node('Get Schema',get_table_schema)
  #workflow.add_node('Viz Check',checker)
  workflow.add_node('Visualize Data',visualize_data)
  workflow.add_node('Generate SQL Command',Generate_sqlcommand)
  workflow.add_node('Execute command',execute_sqlcommand)
  workflow.add_node('Generate Response',generate_response)

  #edges
  workflow.add_edge(START,'List tables')
  workflow.add_edge('List tables','Get Schema')
  workflow.add_conditional_edges('Get Schema',checker,{'YES':'Visualize Data','NO':'Generate SQL Command'})
  workflow.add_edge('Generate SQL Command','Execute command')
  workflow.add_conditional_edges('Execute command',query_check,{'Success': 'Generate Response','Failure':'Get Schema'})
  workflow.add_edge('Generate Response',END)
  workflow.add_edge('Visualize Data',END)

  # Compile
  graph = workflow.compile()  
  img_path = 'C:/Users/naren/Downloads'
  os.makedirs(img_path, exist_ok=True)  # Ensure the plots directory exists
  image_filename = f"{img_path}/plot.jpeg"
  if os.path.exists(image_filename):
    os.remove(image_filename)
  inputs = {
    "messages": [
        ("user", query),

    ]
}
  # import pprint
  # for output in graph.stream(inputs):
  #   for key, value in output.items():
  #       pprint.pprint(f"Output from node '{key}':")
  #       pprint.pprint("---")
  #       pprint.pprint(value, indent=2, width=80, depth=None)
  #   pprint.pprint("\n---\n")
  output = graph.invoke(inputs)['messages'][-1].content
  print(output)
  # if (bool(re.search(r'<table>.*</table>', output, re.DOTALL))):
  #          response_df = pd.read_html(output)[0]
  #          st.dataframe(response_df)
  match = re.search(r'(.*?)(<table[^>]*>.*?</table>)', output, re.DOTALL)

  if match:
    preceding_text = match.group(1)  # Text before the table
    table_html = match.group(2)
    response_df = pd.read_html(table_html)[0]
    st.write(preceding_text)
    st.dataframe(response_df)
  else:
    st.write(output)
    if os.path.exists(image_filename):
      st.image('C:/Users/naren/Downloads/plot.jpeg')
    else:
      pass

# from IPython.display import Image, display

# try:
#     display(Image(graph.get_graph(xray=True).draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

# import pprint


# for output in graph.stream(inputs):
#     for key, value in output.items():
#         pprint.pprint(f"Output from node '{key}':")
#         pprint.pprint("---")
#         pprint.pprint(value, indent=2, width=80, depth=None)
#     pprint.pprint("\n---\n")

# xx=graph.invoke(inputs)['messages'][-1].content

# if (bool(re.search(r'<table>.*</table>', xx, re.DOTALL))):
#     response_df = pd.read_html(xx)[0]

# # Himalayan_Expeditions
# # query = 'SELECT trekking_agency FROM Himalayan_Expeditions GROUP BY trekking_agency ORDER BY SUM(member_deaths) DESC LIMIT 1'
# # cur.execute(query)
# # rows = cur.fetchall()
# # rows
# response_df

# xx

# content='SELECT * FROM input_dataset LIMIT 3'
# cur.execute(content)
# rows

