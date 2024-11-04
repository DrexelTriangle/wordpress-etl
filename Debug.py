def dupAuthors(myLst):
  # grab data about duplicate authors
    with open('.\\stats\\duplicate-authors.csv', 'w+', encoding='utf-8') as file:
      file.write(f"first, last, email,\n")
      for dup in myLst:
        file.write(f"{dup[0]}, {dup[1]}, {dup[2]},\n")
      file.close()
    print("> [author.process-authors] wrote duplicate authors to \\stats\\duplicate-authors.csv")