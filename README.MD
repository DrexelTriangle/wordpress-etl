
# Preface
The Triangle's current website is hosted on Wordpress, using a large number of PHP extensions to fit their needs. Over 11 years of use, the build has become very unstable. Updates to PHP lead to many of the extensions breaking, forcing hotfix after hotfix. One of the current missions of the IT team is to migrate all of this data onto our new server, PRISM. The goal of this tool is to handle the migration of needed data from wordpress onto our own local machine.

# General Idea
```mermaid
flowchart LR
    db[(Wordpress Data)] 
    db --> g1
    g1 --> ma[Main]
    ma --> g2
    ma --> g4
    g4 --> cmd@{ shape: docs, label: "SQL_Commands.txt"}

subgraph g1[1]
    ex[Extractor]
end

subgraph g2[2]
direction LR
    tr[Translator]
    tr --> au[Authors]
    tr --> ga[Guest Authors]
    tr --> ar[Articles]
end

g2 --> g3

subgraph g3[3]
    sa[Sanitizer]
end

sa --> ma

subgraph g4[4]
    fm[SQL Formatter]
end
```
The project boils down into 4 main components:
1. The Extractor brings in .xml files into a Python dictionaries.
2. The Translator parses the dictionaries into objects for easier editing.
3. The Sanitizer parses all of our data and unifies all of our data.
4. The Formatter formats our data to fit into SQL tables.

The rest of the README will explain each one of these steps in further detail.
---
## 1. Extractor
```python
class Extractor:
  def __init__(self, posts, guestAuths):
    self.value = 0
    self.postsFile = posts
    self.guestAuthsFile = guestAuths
    self.data = {
      'auth': None,
      'guestAuth': None,
      'art': None 
    }
```
The extractor class is responsible for grabbing the data from Wordpress(WP) and converting it into Python dictionary objects for easier data manipulation. WordPress data can be exported from the admin page as a `.xml` file. In addition to exporting any posts, we need to also grab Guest Authors, as that was a plugin we used to handle non-Triangle member authors. As of now, we have no way of remotely grabbing fresh data from WP, so the repo is currently using a zipped file which holds the two `.xml` files currently in question. The class unzips them and converts them to necessary dictionaries, which then get inserted into the `data` instance variable.

A future goal would be to remotely grab the data so no one has to manually login and grap `.zip` files, but that will be revisted after the main job is done.

## 2. Translator
```python
class Translator:
  def __init__(self, source):
    self.source = source
    self.objCount = 0
    self.objDataDict = {}
```

The Translator's main purpose is to parse the data inside an Extractor's `data` variable, iterating over each dictionary to translate Wordpress keys into more readable values. You can think of it as a filter: looking through each dictionary, grabbing the data that we need to then be mapped to a new variable name, and omit everything else. Each object made will then be added to a giant dictionary. This allows not only for logging the data, but will let us sift through this data at a later time for further manipulation, which you will see shortly. 

As of now, there should only be three items that need translating:
1. Authors
2. Guest Authors (gAuthors)
3. Articles

A child class will be made to inherit the Translator class, and each child's `translate()` function will be overloaded. This is for later convenience when we call these functions:
```python
translators = {
  "articles": ArticleTranslator(extracted["art"]),
  "gAuth": GuestAuthorTranslator(extracted["guestAuth"]),
  "auth": AuthorTranslator(extracted["auth"])
}

for key in translators:
  translators[key].translate()
```

## 3. Sanitizer
```python
class Sanitizer:
  def __init__(self, policies):
    self.policies = policies
  
  def sanitize():
    ...
```
This will probebly be where the most annoying step of this entire process will occur. If you look into text of articles, or the names of some authors/g-authors, you'll notice irregularities inside the data. 

