import tomllib
from sqlalchemy import create_engine

with open('config/env.toml', 'rb') as f:
    config = tomllib.load(f)
    
connection_string = config['dev']['connection_string']
engine = create_engine(connection_string)

# check connection
with engine.connect() as conn:
    print("Database connection successful")
    conn.close()
