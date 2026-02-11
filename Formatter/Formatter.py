import json
from pathlib import Path
import os
import sys
import subprocess
from dotenv import load_dotenv

class Formatter():
    def __init__(self, data):
        self.data = data
        self.sqlCommands = []
        
    def getObjDataDict(self):
        return self.data.getObjDataDict()
        
    def _esc(self, value):
        if value is None:
            return "NULL"
        safe_value = str(value).replace("'", "''")
        return f"'{safe_value}'"

    def _logCommands(self, fileDestination):
        filePath = Path(fileDestination)
        filePath.parent.mkdir(parents=True, exist_ok=True)
        with filePath.open('w+', encoding='utf-8') as file:
          json.dump(self.sqlCommands, file, indent=4)
    
    def fileDump(file:str):
        load_dotenv()
        USERNAME = os.getenv("USERNAME")
        HOSTNAME = os.getenv("HOSTNAME")
        REMOTE_PATH = os.getenv("REMOTE_PATH")
        
        try:
            destination = f"{USERNAME}@{HOSTNAME}:{REMOTE_PATH}"
            command = ["scp", file, destination]
            subprocess.run(command, check=True)
            print(f"File {file} dropped on {HOSTNAME} in {REMOTE_PATH}")

        except subprocess.CalledProcessError as e:
            print(f"SCP command failed: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"The 'scp' command was not found. Make sure OpenSSH client is installed and in your PATH.")
            sys.exit(1)
    
    
