import pandas as pd
import sqlite3
import os

db_name = 'airport_operations.db'
if os.path.exists(db_name):
    os.remove(db_name)

conn = sqlite3.connect(db_name)
cursor = conn.cursor()

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
df = db_name
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