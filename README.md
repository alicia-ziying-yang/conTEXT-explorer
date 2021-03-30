# ConTEXT-Explorer

**ConTEXT Explorer** is an open Web-based system for exploring and visualizing concepts (combinations of co-occuring words and phrases) over time in the text documents. **ConTEXT Explorer** is designed to lower the barriers to applying information retrieval and machine learning for text analysis, including... (list functionalities here). It is designed to be user-friendly, enabling researchers to make sense of their data without technical knowledge.

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

![alt text](https://github.com/alicia-ziying-yang/conTEXT-explorer/blob/1e8a031a1e87fae51e1c671aafbcd662a5a1c774/sample_data/context_explorer_instruction_vert2.png?raw=true)

