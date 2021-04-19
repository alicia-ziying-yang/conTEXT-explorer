---
title: 'ConTEXT Explorer: a web-based text analysis tool for exploring and visualizing concepts across time'
tags:
  - Python
  - Dash
  - Data Analysis
  - Data Visulization
authors:
  - name: Ziying Yang
    orcid: 0000-0001-7705-3280
    affiliation: 1
  - name: Gosia Mikolajczak
    orcid: 0000-0002-7386-4155
    affiliation: 1
  - name: Andrew Turpin
    affiliation: 1
affiliations:
 - name: University of Melbourne
   index: 1

date: 19 April 2021
bibliography: paper.bib

---



# 1. Summary

**ConTEXT Explorer** is an open Web-based system for exploring and visualizing concepts (combinations of co-occurring words and phrases) over time in the text documents. It provides a user-friendly interface to the analysis of user-provided text data and integrates functionalities of the Whoosh search engine, and Spacy, Gensim and Plotly Python libraries. By providing suggestions for query expansion and producing interactive plots, `ConTEXT Explorer` facilitates exploratory data analysis, which can serve as the basis for text classification.

# 2. Statement of Need

With the explosion of digital sources of data, automated text analysis is becoming increasingly popular in humanities and social sciences. However, most computational approaches require at least working knowledge of relevant methods and programming languages (such as R/Python). `ConTEXT Explorer` is designed to lower these barriers to entry, by allowing an application of information retrieval and machine learning in text analysis without programming knowledge. 

`ConTEXT Explorer` is developed using **Dash** [@plotly] in Python, and integrates the following packages:
- **Spacy** pipeline [@spacy] - for pre-processing the text corpora uploaded by users;
- **Whoosh** [@whoosh] - for building a search engine, which allows to rank sentences relevant to the given query terms, and find word frequencies at the sentence and document level;
- **Gensim** [@gensim] - for training a word2vec [@word2vec] model for the uploaded corpus, which allows the user to find words related to the base term when expanding the query;
- **Plotly** [@plotly] - for visualizing results in interactive graphs, which can be customized and saved as PNG files.

Current text analysis tools require either previous knowledge of programming (e.g., R, Python), or are commercial products (e.g., **RapidMiner** [@rapidminer], **Google Cloud Natural Language API** [@googlenlp]). One exception that we are aware of is **Voyant Tools** [@voyant], which is an open-source web-based text analysis tool built in Java. It allows the users to explore their data using some basic text analysis techniques such as word frequencies (at the document level), word cloud, and word context (words appearing around a chosen term). `ConTEXT Explorer` provides several functionalities that give a user a deeper understanding of the text, which are currently not available in Voyant Tools, such as: query suggestions, sentence ranking and query grouping. It includes models allowing to discover similar terms, and a search engine allowing to retrieve sentences relevant to the query terms, which can be used for query expansion. Users can also form multiple query groups (concepts) and compare them visually across time.

Compared to most heavy-weighted commercial text analysis systems such as **RapidMiner** [@rapidminer], which include more complex analysis techniques, `ConTEXT Explorer` is open-sourced (free) and easy to install. It enables researchers to discover concept groups (or classes) in their corpus before mining the text in machine learning driven systems.

`ConTEXT Explorer` is designed to help users interested in defining concepts (groups of query terms), and explore their trends over time. This could be a particularly helpful as an input for some popular text analysis systems such as **MonkeyLearn** [@monkeylearn], which enable text classification, tagging, and training AI machine learning models, but require prior knowledge of the data. 

`ConTEXT Explorer` allows for an easy integration of other Python packages into the analysis process. It can be easily combined with other Python APIs (such as MonkeyLearn), once the concept groups are defined.

`ConTEXT Explorer` has been used as an exploratory tool in the Australian Research Council Discovery Project (DP180101711) "Understanding Political Debate and Policy Decisions Using Big Data". 

# 3. Key Features

`ConTEXT Explorer` could be hosted on a local computer for personal use, or on an ubuntu server for general use.

## 3.1 Build a corpus

Users are asked to format their text documents as a CSV file (with each document saved in a separate row), before uploading it into `ConTEXT Explorer`. At minimum, users are asked to provide document text and publication year. Users can also upload columns with additional document information (such as document author, title, and so on).

`ConTEXT Explorer` processes the submitted file in the following steps:

1. sentencize and tokenize English text using Spacy [@spacy]. This allows to rank the documents and speed up the document search;
2. index the documents, and build a search engine for the corpus using Whoosh [@whoosh], which employs the Okapi BM25F [@BM25F] ranking function;
3. remove stop words, lemmatize remaining words, and generate a word2vec [@word2vec] model for the corpus using Gensim [@gensim]. 

For each uploaded corpus, users can create a new analysis, or load a pre-saved analysis to the dashboard. 

## 3.2 Dashboard
![Figure 3.1 The Overview tab of the dashboard.](https://paper-attachments.dropbox.com/s_BF58715651395C8B59D508B9A7AFBDF87128C0D6732F3C5CB80FFC81F0067860_1618206868822_overview.png)

As shown in Figure 3.1, the dashboard interface has two panes. On the left-hand side, users can 
- select the year range of documents to be displayed in search results;
- add or delete query terms (single words or phrases) from the analysis;
- save the current query as a new analysis, and download the subset of the corpus filtered by the query terms;

**Overview** The overview tab summarizes the corpus information such as the total number of documents, year range, document length, most frequent words in the corpus, and most frequent values for selected metadata

![Figure 3.2 The sentences tab of the dashboard, with some query terms shown in the left pane.](https://paper-attachments.dropbox.com/s_BF58715651395C8B59D508B9A7AFBDF87128C0D6732F3C5CB80FFC81F0067860_1618211302082_sentences.png)

**Sentences** This tab shows the ranking of relevant sentences based on query terms defined in the left pane. Sentences are ranked by the Okapi BM25F ranking function, and the computed similarity score for each sentence is shown in the "SCORE" column. The table can be sorted and filtered by column values. Users can click on each sentence to see its full content in a pop-up window, which also allows to check the frequency of individual terms, and to add them to the query.

![Figure 3.3 The grouping tab of the dashboard, showing the term frequency of the added terms across time (top), and some examples of query groups (bottom).](https://paper-attachments.dropbox.com/s_BF58715651395C8B59D508B9A7AFBDF87128C0D6732F3C5CB80FFC81F0067860_1618281338713_grouping.png)

**Grouping** The top part of this tab shows the number of sentences containing each query term within the user-defined year range. In the bottom part, users can group the query terms using "Any" or "All" operators. Groups can be further combined into more complex groups.

![Figure 3.4 ‘Graphs’ tab, showing the aggregated graph for all groups (top) and individual graph for each group (bottom)](https://paper-attachments.dropbox.com/s_BF58715651395C8B59D508B9A7AFBDF87128C0D6732F3C5CB80FFC81F0067860_1618282796027_graphs.png)

**Graphs** Based on the query groups generated in the previous tab, this page displays aggregated and individual plots, which allow to compare groups (top) and individual terms within each group (bottom). Users can choose the number of relevant documents, number of sentences, or proportion of document as the y-axis of the graphs. All graphs are plotted by Plotly [@plotly] which allows users to interact with every trace in the graphs.

## 3.3 Save and reload an analysis

As mentioned in Section 3.2, users are able to save the details of their analysis (including added terms and generated groups), and reload it to view all of the ranking, groups and graphs from the index page.


# Acknowledgements


# Reference
