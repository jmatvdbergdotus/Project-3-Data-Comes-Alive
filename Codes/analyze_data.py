import sqlite3
import statistics
import pandas as pd
import os

data_dir = "Data" # folder where the CSV files are located
data_file = data_dir + "/dataset.db"

conn = sqlite3.connect(data_file)
cursor = conn.cursor()

# Enable foreign key constraints
cursor.execute("PRAGMA foreign_keys = ON;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Bag (
    BagID TEXT PRIMARY KEY,
    Priority BOOLEAN,
    FlightID TEXT
);
""")

# -----------------------
# Process Table
# Composite PK: (ProcessName, BagID)
# -----------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS Process (
    ProcessName TEXT,
    BagID TEXT,
    Result TEXT CHECK(Result IN ('Success', 'Failure')),
    PRIMARY KEY (ProcessName, BagID),
    FOREIGN KEY (BagID) REFERENCES Bag(BagID)
);
""")

# -----------------------
# Event Table
# Composite PK
# -----------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS Event (
    ProcessName TEXT,
    BagID TEXT,
    Terminal TEXT,
    Zone TEXT,
    Sensor TEXT,
    Timestamp DATETIME,
    Delay INTEGER,
    Result TEXT CHECK(Result IN ('Success', 'Failure')),

    PRIMARY KEY (ProcessName, BagID, Terminal, Zone, Sensor),

    FOREIGN KEY (ProcessName, BagID)
        REFERENCES Process(ProcessName, BagID)
);
""")

# -----------------------
# SensorReading Table
# SensorID = Sensor
# -----------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS SensorReading (
    SensorID TEXT,
    ProcessName TEXT,
    BagID TEXT,
    Terminal TEXT,
    Zone TEXT,

    Temperature REAL,
    Vibration REAL,
    Speed REAL,

    PRIMARY KEY (SensorID, ProcessName, BagID, Terminal, Zone),

    FOREIGN KEY (ProcessName, BagID, Terminal, Zone, SensorID)
        REFERENCES Event(ProcessName, BagID, Terminal, Zone, Sensor)
);
""")

conn.commit()
conn.close()

print("Database schema created.")