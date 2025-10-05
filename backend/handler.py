import tomllib
from sqlalchemy import create_engine

engine = None

def setup_database():
    global engine
    
    with open('config/env.toml', 'rb') as f:
        config = tomllib.load(f)
        
    connection_string = config['dev']['connection_string']
    engine = create_engine(connection_string)

    # check connection
    try:
        with engine.connect() as conn:
            print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")