import sqlite3
import pandas as pd
import os

data_dir = "Data" # folder where the CSV files are located
data_file = data_dir + "/dataset.db"

if os.path.exists(data_file): # if the database already exists, delete it
    print("Removing existing database file ", data_file)
    os.remove(data_file)

conn = sqlite3.connect(data_file) # open the database

# check for all files in the folder
for file in os.listdir(data_dir): 
    print("Found file with name ",file)
    if file.endswith(".csv"): # if the file is CSV
        # get the table name from the file name and replace double _ with single _
        table = file.replace(".csv", "").replace("_", "")
        # put the file in a dataframe
        df = pd.read_csv(f"data/{file}", sep=";") 
        print(df.columns)
        # add dataframe to the the right database table
        df.to_sql(table, conn, index=False, if_exists="replace")   
print("Finished loading data into database ", data_file)
conn.close()