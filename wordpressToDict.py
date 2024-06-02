# KENNETH BLAKE
# wordpressToDict
# PURPOSE: Take a collection of wordpress posts and convert them to a Python Dictionary, as well as a JSON Object

import xmltodict
import pprint
import json
import time
import progressBar as pb
import utility as util
import customClasses as c
import re



print("imports -> successful")

kenneth_wpFile = "C:\\Users\\kenne\\OneDrive\\Documents\\GitHub\\shkenanigans\\tri-wpdump_4-1-24.xml"
kenneth_file2_loc = "C:\\Users\\kenne\OneDrive\\Documents\\GitHub\\shkenanigans\\test_dump.txt"
kenneth_file3_loc = "C:\\Users\\kenne\\OneDrive\\Documents\\GitHub\\shkenanigans\\articleDump.txt"

cole_wpFile = "C:\\Users\\Cole\\skennanigans\\shkenanigans\\tri-wpdump_4-1-24.xml"
cole_file2_loc = "C:\\Users\\Cole\\skennanigans\\shkenanigans\\test_dump.txt"
cole_file3_loc = "C:\\Users\\Cole\\skennanigans\\shkenanigans\\articleDump.txt"


wp_xmlContent = None
wpFile = kenneth_wpFile
file2_loc = kenneth_file2_loc
file3_loc = kenneth_file3_loc


# Grab XML Content  
with open(wpFile, "+r", encoding='utf-8') as file:
    wp_xmlContent = file.read()
    file.close()
print("Obtained File Contents!")


# convert xml to dictionary  
print("Converting XML to Dictionary")
myDict = xmltodict.parse(wp_xmlContent)
print("Already Loaded")

# Grab Author Data
authorData = myDict.get('rss').get('channel').get('wp:author')
articleData = myDict.get('rss').get('channel').get('item')

# Generate article name list.
pb.printProgressBar(0, len(articleData), length = 20)

for i, item in enumerate(articleData):
    title = '' #can never be none
    pubDate = '' #can never be none
    modDate = '' #can never be none. Can be in gmt / est
    description = '' #can be none
    comment_status = '' #can never be none
    priority = False
    breaking_news = False 
    tags = []
    text = '' 

  
    title = util.charMorph(articleData[i].get('title'))
    pubDate = util.charMorph(articleData[i].get('wp:post_date_gmt'))
    modDate = util.charMorph(articleData[i].get('wp:post_modified_gmt'))
    description = util.charMorph(articleData[i].get('description'))
    comment_status = util.charMorph(articleData[i].get('wp:comment_status'))
    tags = util.processArticleTags(articleData[i].get('category'))
    # text = util.charMorph(articleData[i].get('content:encoded'))
    text = 'test'
   
    objArt = c.wpArticle(i, title,pubDate,modDate,description,comment_status,tags,text)

    time.sleep(0.00001)

    pb.printProgressBar(i, len(articleData), length = 20)
# print(c.wpArticle.generic_articleDict[1])
print('Article List Generated')
with open(file3_loc, "w") as file:
    file.write(c.wpArticle.printArticles())
    file.close()
