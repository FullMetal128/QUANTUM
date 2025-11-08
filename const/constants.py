import os
from pathlib import Path
from dotenv import load_dotenv

local_path = Path('../private_files/private_file.env')
current_parent_path = Path(__file__).parent
global_path = (current_parent_path / local_path).resolve()

load_dotenv(global_path)


QUANTUM_TOKEN_API = os.environ.get("QUANTUM_TOKEN")


