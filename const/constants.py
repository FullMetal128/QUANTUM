import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='../private_files/private_file.env')

QUANTUM_TOKEN_API = os.getenv("QUANTUM_TOKEN")

