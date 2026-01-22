from Utils import NLP as nlp
import re
from Translator.Author import Author
from Sanitizer.Sanitizer import Sanitizer
from Sanitizer.PolicyDict import PolicyDict

class TempArticleSanitizer(Sanitizer):
    def __init__(self, data, policies: PolicyDict, logDir: str = "./log"):
        super().__init__(data, policies, logDir)
        self.lastIDd = len(data) - 1
        self.data = data
        self.policies = policies
        self.logDir = logDir
        self.changes = []
        self.conflicts = []

    def _checkForImgTags(self):
        hasPhoto = []
        count = 0
        for article in self.data.values():
            matchObj = re.search(r"https\:\/\/www\.thetriangle.org\/wp-content\/uploads\/(.*?)\\.{0,400}", article.data["text"])
            if matchObj:
                hasPhoto.append(matchObj.group(0))
                count += 1
                with open('TEMP.txt', "a", encoding='utf-8') as file:
                    file.write(matchObj.group(0))
                    file.write('\n')
                    file.close()
        
        # Check for
        for item in hasPhoto:
            lowered = str.lower(item)
            # if not('courtes' in lowered or 'by' in lowered or 'photo:' in lowered or 'credit' in lowered):
            #     with open('TEMP.txt', "a", encoding='utf-8') as file:
            #         file.write(item)
            #         file.write('\n\n')
            #         file.close()

            # 1065 --> <figcaption(.+?)<\/figcaption>
            # 




        print(count/len(self.data))
        exit(7)


    def _normalizeData(self):
        ...

    def _autoResolve(self):
        ...

    def _manualResolve(self):
        ...

    def sanitize(self):
        ...