# ConTEXT-Explorer
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://travis-ci.com/alicia-ziying-yang/conTEXT-explorer.svg?branch=main)](https://travis-ci.com/alicia-ziying-yang/conTEXT-explorer)

**ConTEXT Explorer** is an open Web-based system for exploring and visualizing concepts (combinations of co-occurring words and phrases) over time in the text documents. **ConTEXT Explorer** is designed to lower the barriers to applying information retrieval and machine learning for text analysis, including:
- preprocessing text with sentencizer and tokenizer in a **Spacy pipline**;
- building **Gensim** word2vec model for discovering similar terms, which can be used to expand queries;
- indexing the cleaned text, and creating a search engine using **Whoosh**, which allows to rank sentences using the Okapi BM25F function;
- visualizing results across time in interactive plots using **Plotly**.

It is designed to be user-friendly, enabling researchers to make sense of their data without technical knowledge. Users may:

- upload (and save) a text corpus, and customize search fields;
- add terms to the query using input from the word2vec model, sentence ranking, or manually;
- check term frequencies across time;
- group terms with "ALL" or "ANY" operator, and compound the groups to form more complex queries;
- view results across time for each query (using raw counts or proportion of relevant documents);
- save and reload results for further analysis; 
- download a subset of a corpus filtered by user-defined terms.

More details can be found in the user manual below.

## How to install
### Get the app
Clone this repo to your local environment:

    git clone https://github.com/alicia-ziying-yang/conTEXT-explorer.git

## Set up environment
ConTEXT Explorer is developed using Plotly Dash in **Python**. We are using `Python 3.7.5` and all required packages listed in `requirement.txt`. To help you install this application correctly, we provide conda environment file `ce-env.yml` for you to set up a virtual environment. Simply enter the folder:

    cd conTEXT-explorer
    
and run:

    conda env create -f ce-env.yml
    
To activate this environment, use:

    conda activate ce-env

### Install the application
Then, ConTEXT Explorer can be easily installed by:

    pip install . 
    
### Run the app
- If you want to run ConTEXT Explorer on your **local computer**, comment the code for ubuntu server, and uncomment the last line in `app.py`:

       # app.run_server(debug=False, host="0.0.0.0") # ubuntu server    
       app.run_server(debug=False, port="8010") # local test           

  To start the application, use:

      start-ce
        
  or

      python app.py
    
  The IP address with app access will be displayed in the output.
      
- If you want to run ConTEXT Explorer on an **ubuntu server**, use:

      nohup python app.py &
  


## How to use
A [sample corpus](https://github.com/alicia-ziying-yang/conTEXT-explorer/blob/main/doc/sample_data.csv) with a saved analysis is preset in this app. Feel free to explore the app features using this example. Please check more details in the manual below.

[Click here to view the paged PDF version](https://github.com/alicia-ziying-yang/conTEXT-explorer/blob/main/doc/conTEXT_explorer_ui_manual.pdf)

![alt text](https://github.com/alicia-ziying-yang/conTEXT-explorer/blob/6b1e79e2068eb284a132493815f35e57b3fec409/doc/conTEXT_explorer_ui_manual.png?raw=true)

## Contact and Contribution
This application is designed and developed by Ziying (Alicia) Yang, Gosia Mikolajczak, and Andrew Turpin from the [University of Melbourne](https://www.unimelb.edu.au/) in Australia.

If you encounter any errors while using the app, have suggestions for improvement, or want to contribute to this project by adding new functions or features, please [submit an issue here](https://github.com/alicia-ziying-yang/conTEXT-explorer/issues/new) and pull requests.
