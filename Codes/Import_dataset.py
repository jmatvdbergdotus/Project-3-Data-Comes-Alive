import pandas as pd
import sqlite3
import os

data_dir = "Data"
data_file = data_dir + "/baggage_handling.db"


if os.path.exists(data_file): # if the database already exists, delete it
    print("Removing existing database file ", data_file)
    os.remove(data_file)

conn = sqlite3.connect(data_file) # open the database
cursor = conn.cursor()

for file in os.listdir(data_dir): 
    print("Found file with name ",file)
    if file.endswith(".csv"): # if the file is CSV
        table = file.replace(".csv", "").replace("__", "_")
        
df = pd.read_csv(f"Data/{file}", encoding='utf-8-sig')

df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "").str.lower()

print(f"Detected columns: {df.columns.tolist()}")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(by=['bag_id', 'timestamp'])
df['computed_delay'] = df.groupby('bag_id')['timestamp'].diff().dt.total_seconds() / 60.0
df['computed_delay'] = df['computed_delay'].fillna(0) 
df['mechanical_issue'] = (df['jam'] == 1) | (df['intervene'] == 1)
grouped = df.groupby(['terminal', 'zone', 'hour'])['mechanical_issue'].sum().reset_index()
grouped_sorted = grouped.sort_values(by='mechanical_issue', ascending=False)
print(grouped_sorted.head(20))
df.to_sql(table, conn, index=False, if_exists="replace")
print("Finished loading data into database ", data_file)

cursor.execute("""
CREATE TABLE IF NOT EXISTS SensorImpactAnalysis AS
SELECT 
    jam, 
    intervene, 
    AVG(temp) as avg_temp, 
    AVG(vibration) as avg_vibration, 
    AVG(speed) as avg_speed, 
    AVG(computed_delay) as avg_delay
FROM baggage_handling_dataset
GROUP BY jam, intervene;
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS HourlyThroughput AS
SELECT 
    hour, 
    COUNT(DISTINCT bag_id) as bags_processed
FROM baggage_handling_dataset
GROUP BY hour
ORDER BY bags_processed DESC;
""")

# Create Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS Bag (
    BagID TEXT PRIMARY KEY,
    Priority BOOLEAN,
    FlightID TEXT,
    terminal TEXT,
    zone TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Event (
    EventID INTEGER PRIMARY KEY AUTOINCREMENT,
    BagID TEXT,
    timestamp DATETIME,
    process TEXT,
    sensor TEXT,
    speed REAL,
    vibration REAL,
    temp REAL,
    result INTEGER,
    delay REAL,
    FOREIGN KEY (BagID) REFERENCES Bag(BagID)
);
""")


# 4. Insert Data
# Insert Bag Metadata
bags_df = df[['bag_id', 'priority', 'flight', 'terminal', 'zone']].drop_duplicates(subset=['bag_id'])
bags_df.columns = ['BagID', 'Priority', 'FlightID', 'terminal', 'zone']
bags_df.to_sql('Bag', conn, if_exists='append', index=False)

# Insert Events with computed delay
events_df = df[['bag_id', 'timestamp', 'process', 'sensor', 'speed', 'vibration', 'temp', 'result', 'computed_delay']]
events_df.columns = ['BagID', 'timestamp', 'process', 'sensor', 'speed', 'vibration', 'temp', 'result', 'delay']
events_df.to_sql('Event', conn, if_exists='append', index=False)

conn.commit()
conn.close()

print("Database created successfully with computed process delays!")