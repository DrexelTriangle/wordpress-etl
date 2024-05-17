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
wp_xmlContent = None
wpFile = "C:\\Users\\kenne\\OneDrive\\Desktop\\The Sandbox\\PythonSandbox\\tri-wpdump_4-1-24.xml"
file1_loc = "C:\\Users\\kenne\\OneDrive\Desktop\\The Sandbox\\PythonSandbox\\wpDict.json"
file2_loc = "C:\\Users\\kenne\\OneDrive\Desktop\\The Sandbox\\PythonSandbox\\test_dump.txt"
file3_loc = "C:\\Users\\kenne\\OneDrive\Desktop\\The Sandbox\\PythonSandbox\\authorDump.txt"


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

    


# Generate author list.
pb.printProgressBar(0, len(authorData), length = 20)
for i, item in enumerate(authorData):
    fName = ''
    lName = ''
    if ( (authorData[i].get('wp:author_first_name') is None) and (authorData[i].get('wp:author_last_name') is None)):
        name = util.charMorph(authorData[i].get('wp:author_display_name'))
        newName = util.parseName(name)
        fName = newName[0]
        lName = newName[1]
    else:
        fName = util.charMorph(authorData[i].get('wp:author_first_name'))
        lName = util.charMorph(authorData[i].get('wp:author_last_name'))
        email = util.charMorph(authorData[i].get('wp:author_email'))
        obj = c.wpAuthor(fName, lName, email)
    time.sleep(0.00001)

    pb.printProgressBar(i, len(authorData), length = 20)
print('Author List Generated')

# c.wpAuthor.printAuthors()
# with open(file3_loc, "w") as file:
#     file.write(c.wpAuthor.authorTemp)
#     file.close()



print("\n")






print(articleData[268].get('dc:creator'))
print(articleData[268].get('title')) # title = title
print(util.GMT_to_EST(articleData[268].get('wp:post_date_gmt'))) # pubDate = pubDate
print(util.GMT_to_EST(articleData[268].get('wp:post_modified_gmt'))) # modDate = modDate 
print(articleData[268].get('description')) # description = description
print(articleData[268].get('wp:comment_status')) # commentStatus = commentStatus
print(f'''{util.processArticleTags(articleData[268].get('category'))}''')
print(articleData[268].get('content:encoded')) # text = text







# for i, item in enumerate(articleData):
    # id = id
    # title = title
    # pubDate = pubDate
    # modDate = modDate 
    # description = description
    # commentStatus = commentStatus
    # tags = tags
    # text = text





# TODO: merge in guest authors......
 



