
# Summary
TASK: construct a maintainable script to handle the transfer of WordPress data into the SQL database on PRISM
___
# SQL Database Schema
Here is the database structure that lives on PRISM:
columns
id: kjRksejKCecRQLxGB8DLo
===
## ARTICLES
---
- id: int
- title: varchar
- pub_date: datetime
- mod_date: datetime
- description: varchar
- comment_status: varchar
- priority: bool
- breaking_news: bool
- tags: varchar
- text: string

## SECTIONS
---
- id: int
- parent_id: int
- name: varchar

## ARTICLES_SECTIONS
---
- id: int
- articles_id: int
- sections_id: int


===
## AUTHORS
---
- id: int
- first_name: varchar
- last_name: varchar
- email: varchar
- role: int

## ROLES
---
- id: int
- name: varchar
- \[action\]: bool

## MEDIA
---
- id: int
- file_path: varchar
- source: varchar
- description: varchar
- photographer: int
  
## VIEWS
---
- id: int
- slug: varchar
- views: int
- dt: date

===
## ARTICLES_AUTHORS
---
- id: int
- authors_id: int
- articles_id: int

## ARTICLES_MEDIA
---
- id: int
- articles_id: int
- media_id: int

## ADS
---
- id: int
- file_path: varchar
- link: string
- location: varchar

## COMMENTS
---
- id: int
- article_id: int
- text: varchar
- author: int

===
## POLLS 
---
- id: int
- name: varchar

## POLL_OPTIONS
---
- id: int
- name: varchar
- picks: int
- poll_id

## CROSSWORD
---
- id: int
- solved: varchar
- date: datename
- name: varcher

## CROSSWORD_HINTS
---
- id: int
- crossword_id: int
- type: varchar
- numner: int
- hint: varchar




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
    ex[Exporter]
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
5. The Exporter generates the texts into easy to parse `.txt` files

The concept is very manageable, the tricky part is handling all of the data uniforming. Making sure all of the data looks the same is the interesting task. However, with this design, we will cross that bridge when we get there.
