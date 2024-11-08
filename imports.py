from xmltodict import *
from progressBar import *
from utility import *
from classes.wpArticle import *
from classes.wpAuthor import *
from testing import *

wp_postsExportFile = ".\\rawdata\\tri-wpdump_4-1-24.xml"
wp_guestAuthorsExportFile = ".\\rawdata\\thetriangle.WordPress.2024-07-10.xml"

file2_loc = ".\\dumps\\test_dump.txt"
file3_loc = ".\\dumps\\articleDump.txt"
file4_loc = ".\\output\\wpSQL-authors.txt"
file5_loc = ".\\output\\wpGuestAuthors.txt"
file6_loc = ".\\dumps\\guestAuthorDump.txt"
file7_loc = ".\\dumps\\authorDump.txt"
file8_loc = ".\\output\\wpSQL-articles.txt"
file9_loc = ".\\output\\wpSQL-articles-authors.txt"
