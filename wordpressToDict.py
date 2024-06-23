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

wpFile = ".\\rawdata\\tri-wpdump_4-1-24.xml"
file2_loc = ".\\Dumps\\test_dump.txt"
file3_loc = ".\\Dumps\\articleDump.txt"
file4_loc = ".\\Output\\wpSQL.txt"

def processAuthor(author):
    fName = ''
    lName = ''
    email = ''
    if ( (authorData[i].get('wp:author_first_name') is None) and (author.get('wp:author_last_name') is None)):
        name = util.charMorph(authorData[i].get('wp:author_display_name'))
        newName = util.parseName(name)
        fName = newName[0]
        lName = newName[1]
    else:
        fName = util.charMorph(author.get('wp:author_first_name'))
        lName = util.charMorph(author.get('wp:author_last_name'))

    if ( (author.get('wp:author_email') is not None) ):
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
    pubDate = articlePost.get('wp:post_date_gmt')
    modDate = articlePost.get('wp:post_modified_gmt')
    description = util.charMorph(articlePost.get('description'))
    comment_status = articlePost.get('wp:comment_status')
    tags = util.processArticleTags(articlePost.get('category'))
    text = str(util.charMorph(articlePost.get('content:encoded')))
   
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
print()
print("┌── Processing Authors...")
pb.printProgressBar(0, len(authorData), length = 50)
for i, item in enumerate(authorData):
    processAuthor(authorData[i])
    time.sleep(0.00001)
    pb.printProgressBar(i + 1, len(authorData), length = 50)
print()
# ---------- PART 3: PROCESS ARTICLES -----------------------------------------------------------------------------------

print("┌── Processing Articles...")
pb.printProgressBar(0, len(articleData), length = 50)
for i, item in enumerate(articleData):
    processArticlePost(articleData[i])

    time.sleep(0.00001)
    pb.printProgressBar(i + 1, len(articleData), length = 50)
print("")

with open(file3_loc, "w") as file:
    wpArt.wpArticle.printArticles(file3_loc)
    file.close()


with open(file4_loc, "a+", encoding="utf-8") as file:
    file.write("CREATE TABLE authors (id INT, first_name VARCHAR(256), last_name VARCHAR(256), email VARCHAR(256), role int);\n")
    for i in wpAuth.wpAuthor.authorDict:
        itm = wpAuth.wpAuthor.authorDict[i]
        file.write(f"INSERT INTO authors (id, first_name, last_name, email, role) VALUES ({itm.id}, {itm.firstName}, {itm.lastName}, {itm.email}, {itm.role});\n")
    file.close()




# print(articleData[5])


