from newUtility import *
from Author import *

class Article:
  articleCount = 0
  articleDict = {}
  articleTemp = ''
  artifacts = []
  map = []

  def __init__(self, id, title, pubDate, modDate, description, commentStatus, tags, authors, text):
    Article.articleCount += 1
    self.priotity = False
    self.breakingNews = False
    self.id = Article.articleCount
    self.title = title
    self.pubDate = pubDate
    self.modDate = modDate 
    self.description = description
    self.commentStatus = commentStatus
    self.tags = tags
    self.authors = authors
    self.text = text

    Article.articleDict.update({self.id : self})
    
  def __str__(self):
    result = ''
    result += f'id: {self.id}\n'
    result += f'\ttitle: {self.title}\n'
    result += f'\tpubDate: {self.pubDate}\n'
    result += f'\tmodDate: {self.modDate}\n'
    result += f'\tdescription: {self.description}\n'
    result += f'\tcommentStatus: {self.commentStatus}\n'
    result += f'\ttags: {self.tags}\n'
    result += f'\tauthors: {self.authors}\n'
    result += f'\ttext: \n\n{self.text}\n\n'
    
    return result 
    
  def getArticle(index):
    return Article.articleDict[index + 1]
    
  def visualize():
    print('> [article.visualize] visualizing articles')
    with open('.\\visualizations\\visualized-articles.txt', 'w+', encoding='utf-8') as file:
      result = ''
      for i in range(len(Article.articleDict)):
        file.write(str(Article.getArticle(i)))
      file.close()

  def processTags(myLst):
    startColorCode = f"\033[38;2;255;234;0m"
    endColorCode = f"\033[0m"
    # print(f"{startColorCode}Error, no tags given{endColorCode}")
    result = []
    tags = []
    articleAuthors = []
    artifacts = []
    try:
      for i in range(len(myLst)):
        temp = myLst[i]
        if (temp.get('@domain') == 'post_tag'):  
          tags.append(temp.get("#text"))
          ...
        if (temp.get('@domain') == 'author'):  
          aA = temp.get("#text").replace('.', '').replace('-', '').replace('_', '').replace(' ', '').lower()
          articleAuthors.append(temp.get("#text"))
          Article.map.append(aA)
          try:
            artifact = re.search(r"[^a-zA-Z\d\s:]", temp.get("#text")).group(0)
            if not(artifact in Article.artifacts):
              Article.artifacts.append(artifact)
          except AttributeError:
            continue
            ...
        # print(temp)
    except KeyError:
      tags.append('NO_TAGS')
        
    tags.sort(reverse=True)
    result.append(tags)
    result.append(articleAuthors)
    

    return result
      # print(tags)



    # for item in myLst:
    #     temp = [item.get("#text") if (item.get('@domain') == 'post_tag') else '' for item in myLst]
    #     temp.sort(reverse=True)
    #     return list(filter(lambda x: x != '', temp))   
    # ['.', '-', '_']

  def processArticles(articleData):
    print('> [article.process-article] processing articles...')
    # Insertion
    # Visualize

    title = '' #can never be none
    pubDate = '' #can never be none
    modDate = '' #can never be none. Can be in gmt / est
    description = '' #can be none
    comment_status = '' #can never be none
    priority = False
    breaking_news = False 
    metaTags = []
    tags = []
    authors = []
    text = '' 


    for i, item in enumerate(articleData):
      articlePost = articleData[i]

      title = charMorph(articlePost.get('title'))
      pubDate = articlePost.get('wp:post_date_gmt')
      modDate = articlePost.get('wp:post_modified_gmt')
      description = charMorph(articlePost.get('description'))
      comment_status = articlePost.get('wp:comment_status')
      metaTags =  Article.processTags(articlePost.get('category'))
      tags = metaTags[0]
      authors = metaTags[1]
      # text = str(charMorph(articlePost.get('content:encoded')))
      obj = Article(i, title,pubDate,modDate,description,comment_status, tags, authors, text)
    
    Article.visualize()
    print('> [article.process-article] done.')
  
  def manualMapping(myLst):
    print("\033c", end="")
    mappings = []
    newAuthors = []
    running = True
    while(running):
      
      for i in range(len(myLst)):
        print("\033c", end="")
        print('[article-mapping-tool]\n')
        print(f'> is author {myLst[i]} an existing author?\n')
        print(f'  1. Yes, this is an existing author.')
        print(f'  2. No, this is not an existing author.')
        print(f'  3. This author is actually multiple authors.')
        print(f'  4. Skip for now.')
        print()
        choice = input('> ')
        if (choice == ''):
          choice = '4'

        try:
          match(int(choice.strip())):
            case 1:
              singleAuthor = int(input('> Enter author number: ').strip())
              temp = Author.getAuthor(singleAuthor - 1)
              print(f'> Map {myLst[i]} to the Author {temp.firstName} {temp.lastName}?\n')
              print(f'  1. Yes')
              print(f'  2. No')
              print()
              confirmation = input('> ')
              match(int(confirmation.strip())):
                case 1:
                  print('result: yes')
                  mappings.append(f'{myLst[i]}, {temp}')
                case 2:
                  print('result: no')
            
            case 2:
              firstName = ''
              lastName = ''
              email = ''

              firstName = input('Enter first name: ').strip()
              lastName = input('Enter last name: ').strip()
              email = input('Enter email:').strip()

              print(f"id.{len(Author.authorDict)} -> {firstName} {lastName}, {email}")

              confirmation = input('> ')
              match(int(confirmation.strip())):
                case 0:
                  print('result: yes')
                  newAuthors.append(f'{firstName}, {lastName}, {email}')
                case 1:
                  print('result: no')

            case 3:  
              multipleAuthors = input('> Enter author numbers, separated by dashes: ').strip()
              tempLst = multipleAuthors.strip().split('-')
              for j in tempLst:
                itm = Author.getAuthor(int(j) - 1)
                print(f'{j} - {itm.firstName} {itm.lastName}')
              
              confirmation = input('> ')
              match(int(confirmation.strip())):
                case 0:
                  print('result: yes')
                  mappings.append(f'{myLst[i]}, {tempLst}')
                case 1:
                  print('result: no')
            
            case 4:
              continue
            
            case 5:
              running = False
              break

            case _:
              print('invalid')
              exit(7)
        except ValueError:
          break

    choice = input('> overwrite mapping files?')
    if (choice.strip() == '1'):
      with open('.\\output\\oldMappings.txt', 'w+', encoding='utf-8') as file:
        for i in mappings:
          file.write(i)
      with open('.\\output\\newAuthorMappings.txt', 'w+', encoding='utf-8') as file:
        for i in newAuthors:
          file.write(i)



      




