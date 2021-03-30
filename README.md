# ConTEXT-Explorer

**ConTEXT Explorer** is an open Web-based system for exploring and visualizing concepts (combinations of co-occuring words and phrases) over time in the text documents. **ConTEXT Explorer** is designed to lower the barriers to applying information retrieval and machine learning for text analysis, including... (list functionalities here). It is designed to be user-friendly, enabling researchers to make sense of their data without technical knowledge.

## How to install
### Get the app
Clone this repo to your local environment:

    git clone https://github.com/alicia-ziying-yang/conTEXT-explorer.git

### Install required dependencies    
ConTEXT Explorer is developed using Plotly Dash in **Python**. We are using `Python 3.7.5`, and all required packages are listed in `requirement.txt`. Please upgrade `pip` to the newest version, and use

    pip install -r requirements.txt; fi 
to install these packages in your local environment.

### Run the app
- If you are going to run this app on a **ubuntu server**, simply just excute:

      python app.py

  The IP address for accessing will be displayed in the output.
  
  You may want to run it with `nohup`:

      nohup python app.py &
    
  

- If you want to run the app in your **local computer**, comment the code for ubuntu server, and uncomment the last line in `app.py`:

       # app.run_server(debug=False,host="0.0.0.0") # ubuntu server    
       app.run_server(debug=False, port="8010") # local test           

  You can then access the app via visiting http://127.0.0.1:8010 in your broswer.

## How to use
