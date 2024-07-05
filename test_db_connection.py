import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from config import Config

def test_db_connection():
    load_dotenv()
    
    # Get the database URI from the Config class
    database_uri = Config.SQLALCHEMY_DATABASE_URI
    
    print(f"Attempting to connect to database: {database_uri}")
    
    try:
        # Create an engine
        engine = create_engine(database_uri)
        
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Successfully connected to the database!")
            print(f"Query result: {result.fetchone()}")
    
    except Exception as e:
        print(f"Error connecting to the database: {str(e)}")

if __name__ == "__main__":
    test_db_connection()
