import zipfile
import shutil

class Utility:
  def unzip(zipPath):
    with zipfile.ZipFile(zipPath, 'r') as zip_ref:
      zip_ref.extractall('.\\Data')

      
  def _delete_dir(dir):
    shutil.rmtree(dir)
