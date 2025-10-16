from Translator.Author import *
from Translator.GuestAuthor import *

class Translator:

    def __init__(self, source):
        self.source = source
        self.source = {}
        self.objCount = 0
        self.objDataDict = {}

    def translate(self):
        translation = []
        return translation

class AuthorTranslator(Translator):

    def __init__(self, source):
        super().__init__(source)
    
    def translate(self):
        authors = []
        for author in self.source:
            authorObject = Author(int(author['wp:author_id']), 
                                  author['wp:author_login'], 
                                  author['wp:author_email'],
                                  author['wp:author_display_name'], 
                                  author['wp:author_first_name'], 
                                  author['wp:author_last_name'])
            authors.append(authorObject)
        return authors

class GuestAuthorTranslator(Translator):

    def __init__(self, source):
        super().__init__(source)
    
    def translate(self):
        guestAuthors = []
        for guestAuthor in self.source:
            guestAuthorObject = GuestAuthor(
                                guestAuthor['title'],
                                guestAuthor['title'].split(' ')[0],
                                guestAuthor['title'].split(' ')[1]
                                )
            guestAuthors.append(guestAuthorObject)
        return guestAuthors

class ArticleTranslator(Translator):
    # Nguyen - it might be a very bad idea to store every single article cause they have like 18K articles
    def __init__(self, source):
        super().__init__(source)
    
    # Nguyen - commenting out for now
    # def translate(self):
    #     authors = []
    #     for author in self.source:
    #         authorObject = Author(int(author['wp:author_id']), 
    #                               author['wp:author_login'], 
    #                               author['wp:author_email'],
    #                               author['wp:author_display_name'], 
    #                               author['wp:author_first_name'], 
    #                               author['wp:author_last_name'])
    #         authors.append(authorObject)
    #     return authors

    # guestAuthor['title'], 
    #                               guestAuthor['dc:creator'], 
    #                               guestAuthor['link'],
    #                               guestAuthor['pub_date'], 
    #                               guestAuthor['guid'], 
    #                               guestAuthor['description'],
    #                               guestAuthor['content:encoded'],
    #                               guestAuthor['excerpt:encoded'],
    #                               guestAuthor['wp:post_id'],
    #                               guestAuthor['wp:post_date'],
    #                               guestAuthor['wp:post_date_gmt'],
    #                               guestAuthor['wp:post_modified'], 
    #                               guestAuthor['wp:post_modified_gmt'], 
    #                               guestAuthor['wp:comment_status'], 
    #                               guestAuthor['wp:ping_status'], 
    #                               guestAuthor['wp:post_name'], 
    #                               guestAuthor['wp:status'],
    #                               guestAuthor['wp:post_parent'],
    #                               guestAuthor['wp:menu_order'], 
    #                               guestAuthor['wp:post_type'],
    #                               guestAuthor['wp:post_password'],
    #                               guestAuthor['wp:is_sticky'],
    #                               guestAuthor['wp:category'],
    #                               guestAuthor['wp:postmeta']
                                  
    
    def translate(self):
        articles = []
        for article in self.source: 
            articleObject = Article(
                title = article['title'],
                pubDate=article['wp:post_date'],
                modDate=article['wp:post_modified'],
                description= article['description'],
                commentStatus=article['wp:comment_status'],
                tags = article['category'],
                authors= article['dc:creator'], # for later: maybe link with Author object
                text= article['content:encoded'], # sth's wrong with the article extractor it couldn't extract text
            )
            articles.append(articleObject)
        return articles
            

