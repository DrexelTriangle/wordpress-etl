
# Summary
TASK: construct a maintainable script to handle the transfer of WordPress data into the SQL database on PRISM




```
As stated in the summary above, the task at hand is to take our WP database and manipulate all of its data to fit this schema. Now, we won't have to deal with all of this data at first. Our main mission is to import over the Authors, Articles, and images. This is enough data to get everything else working.

# General Idea
Here is rough diagram we have set up:

```mermaid
flowchart LR
    db[(Wordpress Data)] 
    db --> g1
    g1 --> ma[Main]
    ma --> g2
    ma --> g4
    g4 --> cmd@{ shape: docs, label: "SQL_Commands.txt"}

subgraph g1[1]
    ex[Extractor]
end

subgraph g2[2]
direction LR
    tr[Translator]
    tr --> au[Authors]
    tr --> ga[Guest Authors]
    tr --> ar[Articles]
end

g2 --> g3

subgraph g3[3]
    sa[Sanitizer]
end

sa --> ma

subgraph g4[4]
    fm[SQL Formatter]
end

```
1. The Extractor brings in .xml files into a Python dictionaries.
2. The Translator parses the dictionaries into objects for easier editing.
3. The Sanitizer parses all of our data and unifies all of our data.
4. The Formatter formats our data to fit into SQL tables.
5. The Exporter generates the SQL commands and exports them as `.txt` files

Potential improvements to this design could involve adding a "Retriever" that fetches the .xml files from WordPress automatically(step 0) and adding an "Injector" that automatically updates the SQL database(step 6).

This concept is very manageable, the tricky part is handling all of the data uniforming. Making sure all of the data looks the same is the interesting task. However, with this design, we will cross that bridge when we get there.
