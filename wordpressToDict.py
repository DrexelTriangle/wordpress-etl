# KENNETH BLAKE
# wordpressToDict
# PURPOSE: Take a collection of wordpress posts and convert them to a Python Dictionary, as well as a JSON Object

import xmltodict
import pprint
import json
import time
import progressBar as pb
import utility as util
import wpArticle as wpArt
import wpAuthor as wpAuth
import re


# LOCAL FILE VARIABLES
kenneth_wpFile = "C:\\Users\\kenne\\OneDrive\\Documents\\GitHub\\shkenanigans\\tri-wpdump_4-1-24.xml"
kenneth_file2_loc = "C:\\Users\\kenne\OneDrive\\Documents\\GitHub\\shkenanigans\\test_dump.txt"
kenneth_file3_loc = "C:\\Users\\kenne\\OneDrive\\Documents\\GitHub\\shkenanigans\\articleDump.txt"

cole_wpFile = "C:\\Users\\Cole\\skennanigans\\shkenanigans\\tri-wpdump_4-1-24.xml"
cole_file2_loc = "C:\\Users\\Cole\\skennanigans\\shkenanigans\\test_dump.txt"
cole_file3_loc = "C:\\Users\\Cole\\skennanigans\\shkenanigans\\articleDump.txt"

# ---------- INITIAL VARIABLES & FUNCTIONS ------------------------------------------------------------------------------
wp_xmlContent = None
wpFile = kenneth_wpFile
file2_loc = kenneth_file2_loc
file3_loc = kenneth_file3_loc

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







# ---------- PART 3: PROCESS ARTICLES -----------------------------------------------------------------------------------
pb.printProgressBar(0, len(articleData), length = 20)

for i, item in enumerate(articleData):
    processArticlePost(articleData[i])

    time.sleep(0.00001)
    pb.printProgressBar(i, len(articleData), length = 20)

print('Article List Generated' + '(' + str(len(articleData)) + ')')

with open(file3_loc, "w") as file:
    wpArt.wpArticle.printArticles(file3_loc)
    file.close()
