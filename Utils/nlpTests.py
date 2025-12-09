import NLP

string = "Josh Einbinder-Schatz"

print(NLP.cleanDocument(string, "author_single"))

multiple_string = "Melody Wu &amp; Maddie Pelchat"

print(NLP.cleanDocument(multiple_string, "author_multiple"))

