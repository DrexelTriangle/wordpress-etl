from Constants import *
import zipfile
import shutil
import pprint

class Utility:
  def unzip(zipPath):
    with zipfile.ZipFile(zipPath, 'r') as zip_ref:
      zip_ref.extractall(DATA_DIR)


  def _delete_dir(dir):
    shutil.rmtree(dir)

  
  def _html_text_norm(text):
    result = ''
    
    if (text == None):
      return None 
    result = text.replace('&amp;', '&')
    result = result.replace('&nbsp;', ' ')
    return result
