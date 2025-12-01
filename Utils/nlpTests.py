import NLP

string = "Josh Einbinder-Schatz"

print(NLP.cleanDocument(string, "author_single"))

multiple_string = "By Shreeya Gounder,  Arielle Madeam and Lena Tran"

print(NLP.cleanDocument(multiple_string, "author_multiple"))

sim_string = "Sac\vh#in    Avut12u_ "

print(NLP.cleanDocument(sim_string, "similarity"))