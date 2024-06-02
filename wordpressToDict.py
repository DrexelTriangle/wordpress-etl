# KENNETH BLAKE
# wordpressToDict
# PURPOSE: Take a collection of wordpress posts and convert them to a Python Dictionary, as well as a JSON Object

import xmltodict
import time
import progressBar as pb
import utility as util
import wpArticle as wpArt
import wpAuthor as wpAuth

# ---------- INITIAL VARIABLES & FUNCTIONS ------------------------------------------------------------------------------
wp_xmlContent = None
myDict = {}
authorData = {}
articleData = {}

wpFile = ".\\tri-wpdump_4-1-24.xml"
file2_loc = ".\\test_dump.txt"
file3_loc = ".\\articleDump.txt"

def processAuthor(author):
    fName = ''
    lName = ''
    if ( (authorData[i].get('wp:author_first_name') is None) and (author.get('wp:author_last_name') is None)):
        name = util.charMorph(authorData[i].get('wp:author_display_name'))
        newName = util.parseName(name)
        fName = newName[0]
        lName = newName[1]
    else:
        fName = util.charMorph(author.get('wp:author_first_name'))
        lName = util.charMorph(author.get('wp:author_last_name'))
        email = util.charMorph(author.get('wp:author_email'))
        obj = wpAuth.wpAuthor(fName, lName, email)

def processArticlePost(articlePost):
    title = '' #can never be none
    pubDate = '' #can never be none
    modDate = '' #can never be none. Can be in gmt / est
    description = '' #can be none
    comment_status = '' #can never be none
    priority = False
    breaking_news = False 
    tags = []
    text = '' 

  
    title = util.charMorph(articlePost.get('title'))
    pubDate = util.charMorph(articlePost.get('wp:post_date_gmt'))
    modDate = util.charMorph(articlePost.get('wp:post_modified_gmt'))
    description = util.charMorph(articlePost.get('description'))
    comment_status = util.charMorph(articlePost.get('wp:comment_status'))
    tags = util.processArticleTags(articlePost.get('category'))
    text = 'test'
   
    objArt = wpArt.wpArticle(i, title,pubDate,modDate,description,comment_status,tags,text)

    
# -----------------------------------------------------------------------------------------------------------------------
# PART 1: SETUP


# Grab XML Content, convert to dictionary, grab author & article data  
print("Converting XML to Dictionary...")
with open(wpFile, "+r", encoding='utf-8') as file:
    wp_xmlContent = file.read()
    file.close()

myDict = xmltodict.parse(wp_xmlContent)
authorData = myDict.get('rss').get('channel').get('wp:author')
articleData = myDict.get('rss').get('channel').get('item')

# ---------- PART 2: PROCESS AUTHORS -----------------------------------------------------------------------------------

pb.printProgressBar(0, len(authorData), length = 20)
for i, item in enumerate(authorData):
    processAuthor(authorData[i])
    time.sleep(0.00001)
    pb.printProgressBar(i, len(authorData), length = 20)
print('Author List Generated')

# ---------- PART 3: PROCESS ARTICLES -----------------------------------------------------------------------------------
'''
TODO: Filter by Article Type [Articles, Crossword, Sudoku, ]
    So the Triangle stores their comics, crossword, and sudoku puzzles as articles.
    Now, it would be nice if they stored them in some consistent manner, right?
    They don't...they don't at all.
    
    CROSSWORD/SUDOKU POSTS
      - 'crossword'/'sudoku' in tag
      - 'crossword'/'sudoku' in title
      - 'crossword'/'sudoku' in embed (BEST BET)
        - All of the crosswords are made using the PuzzleMe puzzle maker. 
        - The embeds will look something like: 
          - [puzzleme set=<set-string> id=<id-string> type=<"crossword" OR "sudoku">]
          - We could use a regEx pattern to look for that pattern and that should find all the corresponding puzzles!
    
    We'll worry about grabbing the necessary data later.
    Right now, we just need to worry about separating the articles into there appropriate lists.
    Here was my initial solution:

    ARTICLE SORTING SOLUTION (Ken's idea)
        1. Add a new class field called [type]
        2. Build the object, as usual.
        3. Within the __init__ constructor, add a function that sets the [type] field accordingly.
        4. Append the object to a different list, depending on the value in the [type] field

    That was my initial idea, but feel free to think about something else.
    The main issue with that answer is keeping track of ID numbers across the different lists. 
    The other idea would be to parse through everything twice: Parse everything, then sort.
    Once again, I'll let you decide how to go about doing this [o7 <- salute]
'''

pb.printProgressBar(0, len(articleData), length = 20)

for i, item in enumerate(articleData):
    processArticlePost(articleData[i])

    time.sleep(0.00001)
    pb.printProgressBar(i, len(articleData), length = 20)

print('Article List Generated' + '(' + str(len(articleData)) + ')')

with open(file3_loc, "w") as file:
    wpArt.wpArticle.printArticles(file3_loc)
    file.close()
