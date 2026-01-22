from pathlib import Path
from Utils.Constants import *
import zipfile
import shutil

class Utility:
  def unzip(zipPath):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zipPath, 'r') as zip_ref:
      zip_ref.extractall(DATA_DIR)


  def _delete_dir(dir):
    path = Path(dir)
    if not path.exists():
      return
    if path.is_dir():
      shutil.rmtree(path, ignore_errors=True)
      return
    path.unlink(missing_ok=True)

  
  def _html_text_norm(text):
    result = ''
    
    if (text is None):
      return None 
    result = text.replace('&amp;', '&')
    result = result.replace('&nbsp;', ' ')
    return result
