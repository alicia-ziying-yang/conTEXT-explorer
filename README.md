# ConTEXT-Explorer

**ConTEXT Explorer** is an open Web-based system for exploring and visualizing concepts (combinations of co-occuring words and phrases) over time in the text documents. **ConTEXT Explorer** is designed to lower the barriers to applying information retrieval and machine learning for text analysis, including
- processing text in a **Spacy pipline** with sentencizer and tokenizer;
- building **Gensim** word2vec model for discovering similar terms in order to help form queries;
- indexing the cleaned text, and creating a search engine using **Whoosh** which employes the Okapi BM25F function to rank sentences;
- visualizing results across time in interactive graphs using **Plotly**.

It is designed to be user-friendly, enabling researchers to make sense of their data without technical knowledge. Users may

- upload (and save) their own corpus, and costomize search fields;
- add terms to query from word2vec model, sentences in the ranking, and input form;
- check term frequecies over time;
- group terms with "ALL" or "ANY" operator, and compound the formed groups into greater groups;
- view overall and individual graphs of groups in levels of raw count and proportion;
- save and reload results of groups; 
- download a corpus subset filtered by the added terms.

## How to install
### Get the app
Clone this repo to your local environment:

    git clone https://github.com/alicia-ziying-yang/conTEXT-explorer.git

### Install required dependencies    
ConTEXT Explorer is developed using Plotly Dash in **Python**. We are using `Python 3.7.5`, and all required packages are listed in `requirement.txt`. To install the packages in your local environment, you need to upgrade `pip` to the newest version and use:

    pip install -r requirements.txt; fi 

### Run the app
- If you want to run ConTEXT Explorer on an **ubuntu server**, use:

      python app.py

  The IP address with app access will be displayed in the output.
  
  If you have issues with the access, try run the code with `nohup`:

      nohup python app.py &
    
  

- If you want to run ConTEXT Explorer on your **local computer**, comment the code for ubuntu server, and uncomment the last line in `app.py`:

       # app.run_server(debug=False, host="0.0.0.0") # ubuntu server    
       app.run_server(debug=False, port="8010") # local test           

  You can then access the app through your browser: http://127.0.0.1:8010

## How to use

![alt text](https://github.com/alicia-ziying-yang/conTEXT-explorer/blob/1f330277415a54bff35e9dbd00025bb57fe6221d/doc/conTEXT_explorer_ui_manual.png?raw=true)
