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

  
  def _visualize(dict, fileName):
    result = pprint.pformat(dict)
    with open(fileName, 'w+', encoding='utf-8') as file:
      file.write(result)
      file.close()
