import mysql.connector
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

load_dotenv()

host=os.getenv('HOST')
user=os.getenv('USER')
password = os.getenv('PASSWORD')
database =  os.getenv('DATABASE')

mydb = mysql.connector.connect(
    host=host,
    user=user,
    password = password)

mycursor = mydb.cursor()
mycursor.execute("CREATE DATABASE IF NOT EXISTS "+ database)

engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}/{database}')

diretorio = './db_creation/original_csv'

for dataset in os.listdir(diretorio):
    if dataset.endswith('.csv'):
        path = os.path.join(diretorio,dataset)
        table_name = dataset.replace('_dataset.csv', '')

        print(f'Criando tabela{table_name} a partir do arquivo {dataset}')

        df = pd.read_csv(path)
        df.to_sql(table_name,con=engine,if_exists='replace',index=False)

mycursor.execute(f"USE {database}")
mycursor.execute("SHOW TABLES")

for x in mycursor:
  print(x)
