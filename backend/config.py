import os
from dotenv import load_dotenv

# This loads the variables from the .env file
load_dotenv()

# Get the database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("ERROR: DATABASE_URL not found in .env file!")