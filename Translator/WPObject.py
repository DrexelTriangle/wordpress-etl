import json

class WPObject:
  def __init__(self):
    self.data = {}
  
  def __str__(self):
    jsonData = json.dumps(self.data)
    return jsonData