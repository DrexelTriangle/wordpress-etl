# KENNETH BLAKE
# wordpressToDict
# PURPOSE: Take a collection of wordpress posts and convert them to a Python Dictionary, as well as a JSON Object

from imports import *


wp_xmlContent = None
myDict = {}
authorData = {}
articleData = {}

wpFile = ".\\rawdata\\tri-wpdump_4-1-24.xml"
file2_loc = ".\\Dumps\\test_dump.txt"
file3_loc = ".\\Dumps\\articleDump.txt"
file4_loc = ".\\Output\\wpSQL.txt"

# Grab XML Content, convert to dictionary, grab author & article data  
print("Converting Posts XML to Dictionary...")
with open(wpFile, "+r", encoding='utf-8') as file:
    wp_xmlContent = file.read()
    file.close()

myDict = parse(wp_xmlContent)
authorData = myDict.get('rss').get('channel').get('wp:author')
articleData = myDict.get('rss').get('channel').get('item')

# Process Authors, Articles
print("┌── Processing Authors...")
processAuthors(authorData)

print("┌── Processing Articles...")
processArticles(articleData)


with open(file3_loc, "w") as file:
    wpArticle.printArticles(file3_loc)
    file.close()


with open(file4_loc, "a+", encoding="utf-8") as file:
    file.write("CREATE TABLE authors (id INT, first_name VARCHAR(256), last_name VARCHAR(256), email VARCHAR(256), role int);\n")
    for i in wpAuthor.authorDict:
        itm = wpAuthor.authorDict[i]
        file.write(f"INSERT INTO authors (id, first_name, last_name, email, role) VALUES ({itm.id}, {itm.firstName}, {itm.lastName}, {itm.email}, {itm.role});\n")
    file.close()
