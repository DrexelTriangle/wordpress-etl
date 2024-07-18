# KENNETH BLAKE
# wordpressToDict
# PURPOSE: Take a collection of wordpress posts and convert them to a Python Dictionary, as well as a JSON Object

from imports import *
from pprint import *

wp_xmlPostContent = None
wp_xmlGuestAuthors = None
wpPostsDict = {}
wpGuestAuthorsDict = {}
authorData = {}
articleData = {}


# Grab XML Content, convert to dictionary, grab author & article data  
print("Converting Posts XML to Dictionary...")
with open(wp_postsExportFile, "+r", encoding='utf-8') as file:
    wp_xmlPostContent = file.read()
    file.close()

with open(wp_guestAuthorsExportFile, "+r", encoding='utf-8') as file:
    wp_xmlGuestAuthors = file.read()
    file.close()

print("Parsing wordpress posts...")
wpPostsDict = parse(wp_xmlPostContent)
authorData = wpPostsDict.get('rss').get('channel').get('wp:author')
articleData = wpPostsDict.get('rss').get('channel').get('item')

print("Parsing wordpress guest authors...")
wpGuestAuthorsDict = parse(wp_xmlGuestAuthors)
guestAuthorData = wpGuestAuthorsDict.get('rss').get('channel').get('item')

visualizeDictionary(wpGuestAuthorsDict, file6_loc)



# Process Authors, Articles
print("┌── Processing Authors...")
processAuthors(authorData)

print("┌── Processing Guest Authors...")
processGuestAuthors(guestAuthorData)

print("┌── Processing Articles...")
processArticles(articleData)

# Additional Testing 
# writeArticlesToFile(file3_loc)
wpAuthor.printAuthors()
with open(file7_loc, "w+", encoding="utf-8") as file:
    file.write(wpAuthor.authorTemp)
    file.close()

locateAllAuthors()
wpAuthor.printAuthors()
with open(file7_loc, "w+", encoding="utf-8") as file:
    file.write(wpAuthor.authorTemp)
    file.close()

print("Writing SQL...")
with open(file4_loc, "a+", encoding="utf-8") as file:
    file.write("CREATE TABLE authors (id INT, first_name VARCHAR(256), last_name VARCHAR(256), email VARCHAR(256), role int);\n")
    for i in wpAuthor.authorDict:
        itm = wpAuthor.authorDict[i]
        file.write(f"INSERT INTO authors (id, first_name, last_name, email, role) VALUES ({itm.id}, {itm.firstName}, {itm.lastName}, {itm.email}, {itm.role});\n")
    file.close()
