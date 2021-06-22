import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_uploader as du
import uuid
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State,MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_table
import plotly.graph_objs as go
import dash_daq as daq
import plotly.express as px

from wordcloud import WordCloud, STOPWORDS
import pandas as pd
import re
import json
from os import listdir
from os.path import isfile, join

from whoosh_search import preprocess_corpus
from topic_model import word2vec
from topic_model import generate_models_fromapp

import base64
import io
import time
import urllib


UPLOAD_FOLDER_ROOT="./uploads"
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
server = app.server
app.config["suppress_callback_exceptions"] = True

du.configure_upload(app, UPLOAD_FOLDER_ROOT)

# read uploaded corpus names
corpus = pd.read_pickle("./corpus_save").to_dict()
if (len(corpus)>0): #not empty
    corpus = corpus[0]



# --- build left banner ---

def build_banner(corpus_element,saves_element,loaded):

    added_option=[]
    if len(loaded["added"])>0:
        i=0
        for add in loaded["added"]:
            added_option.append(html.Div([dcc.Checklist(id={'type':'selected','index':i},
                                            options=[{'label': add, 'value': add}],
                                            labelClassName="selected-term2" )]    
                                        ))
            i+=1

    # find number of document in each year
    doc_num_year=preprocess_corpus.get_num_doc_year(corpus[corpus_element['props']['value']])
    year_list=[int(y) for y in sorted(list(doc_num_year.keys()))]
    
    # generate layout
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[],
            ),
            html.Div(style={"visibility": "hidden","height": "0px"},
                    id="corpus-select-menu",                
                    children=[
                        html.Label(id="corpus-select-title", children="Corpus"),
                        corpus_element,
                    ],
                ),
            html.Div(
                    id="save-select-menu",
                    className='saves-select-menu',
                    children=[
                        html.Label(id="save-select-title", children="Analysis"),
                        html.Div(id="save-with-button",className="side-by-side",children=[saves_element,
                                           html.Button("SAVE",id="save-analysis", n_clicks=0)]),
                        html.Div(id="save-pop-up",children=[])
                    ],
                ),
            html.Div(id="year-range",className="side-by-side",style={"margin-top":"5%","max-width":"96%"},
                children=[
                    html.Label("From"),
                    daq.NumericInput(
                        id="year-from",
                        style={"color":"#e85e56"},
                        className="year-selector",
                        min=min(year_list),
                        max=max(year_list),
                        value= loaded["year"][0] if "year" in loaded else min(year_list)
                    ),html.Label("To"),
                    daq.NumericInput(
                        id="year-to",
                        style={"color":"#e85e56"},
                        className="year-selector",
                        min=min(year_list),
                        max=max(year_list),
                        value=loaded["year"][1] if "year" in loaded else max(year_list)
                    ),
                ]
                ),
            html.Div(
                id="query-select-menu-id",
                className="query-select-menu",
                children=[
                        html.Label(id="query-select-title", children="Query"),
                        html.Div(
                            className="side-by-side",style={"max-width":"95%"},
                            children=[
                                html.Label("Base Term"),
                                dcc.Input(id="base-term", className="dash-input", type="text", placeholder="input text...",
                                    value=loaded["base"])
                        
                            ],
                        ),
                        html.Label(id="add-terms", children="Add Related Words",style={"padding-top":"12px"}),
                        html.Div(
                            id="candidates",
                            className="side-side-side",
                            children=[
                                    html.Div(
                                    dcc.Checklist(
                                            id={'type':'term','index':1},
                                            options=[{"label": "[Not found]", "value": "[Not found]"}],
                                            labelClassName="unselected-term",           
                                        ),    
                                    ),
                            ]
                        ),
                        html.Button("FORM A PHRASE",id="form-phrase"         
                        ),
                        html.Button("ADD A WORD",id="add-single"   
                        ),
                        html.Label(id="add-terms2", children="Words Added",style={"padding-top":"12px"}),
                        html.Div(id="added-terms", className="side-side-side2", children=[
                                html.Div(id="added-terms-fromside",children=added_option)
                            ]
                        ),
                        html.Label(children="Add Manually"),
                        html.Div(
                            className="side-by-side",
                            children=[
                                dcc.Input(id="manu-term", className="dash-input", type="text"),
                                html.Button("ADD",id="manu-add",style={"margin-left":"10px","width":"20%",
                                                                        "line-height": "300%"}),
                            ],
                        ),
                        # hidden divs, record the selected terms
                        html.Div(id='added-terms-global', style={'display': 'none'},children=loaded["added"]
                        ), 
                        html.Div(id='added-terms-global-frompop', style={'display': 'none'},children=[]
                        )
                ]
                        
            )
        ],
    )

# load saved selected analysis
def load_analysis(corpus_name,analysis_name):
    if analysis_name == "create new":
        return dict({"base":"","added":[],"groups":[]})
    else:
        with open(corpus[corpus_name]+"groups/"+analysis_name[2:-2], 'r') as file:
            return json.loads(file.read())

# --- build saving menu ---
@app.callback(Output("save-pop-up", "children"),
              [Input("save-analysis", 'n_clicks')],
              [State("base-term", 'value'),
              State("added-terms-global", "children"),
              State("group-stored-data","data"),
              State("year-from","value"),State("year-to","value")]
              )
def generate_modal_for_save(n,base,added,groups,y_from,y_to):
    if n>0:
        group_divs=[]
        if groups:            
            for g in range(0,len(groups[1])):        
                group_name = groups[1][g]
                group_words = groups[0][g]

                group_div=[]
                for w in group_words:
                    group_div.append(html.Div(className="box-content2",children="_".join(w.split())))
                

                group_all=groups[2][g]
                if group_all == True:
                    box_class = "small-box-AND"
                else:
                    box_class = "small-box-OR"
                group_divs.append(html.Div(className=box_class,children=[
                    html.Div(className="box-title2",children=group_name),
                    html.Div(children=group_div)

                ]))
        if len(added)>0:
            word_add=added[0]
            for q in added[1:]:
                word_add+=", "
                word_add+="_".join(q.split())
        else:
            word_add=[]

        display_boxes = html.Div(className="box",children=[
            html.Div(children=[
                html.Div(className="box-title",children="Year Range"),
                html.Div(className="box-content",children=html.Div(str(y_from)+" - "+str(y_to)))
            ]),
            html.Div(children=[
                html.Div(className="box-title",children="Base Term"),
                html.Div(className="box-content",children=base)
            ]),
            html.Div(children=[
                html.Div(className="box-title",children="Words Added"),
                html.Div(className="box-content",children=word_add)
            ]),
            dcc.Loading(id='dowload-output',color="#e85e56",
                children=[html.Div(style={"text-align":"right"},children=[html.Button("DOWNLOAD CORPUS",id="export-btn",style={
                                        "width":"200px","margin-top":"30px","margin-bottom":"20px"})])]),
            

            html.Div(children=[
                html.Div(className="box-title",children="Groups"),
                html.Div(className="box-group",children=group_divs)
            ])
        ])
        return [html.Div(
            id="markdown2",
            style={"display": "block"},
            className="modal",
            children=(
                html.Div(
                    id="markdown-container2",
                    className="markdown-container",
                    children=[
                        html.Div(
                            className="close-container",
                            children=html.Button(
                                "Close",
                                style={"width":"90px"},
                                id="markdown_close2",
                                n_clicks=0,
                                className="closeButton",
                            ),
                        ),display_boxes,
                        html.Div(
                            className="markdown-text-save",
                            children=[html.Div(id="saving",
                            className="side-by-side",
                                children=[
                                    dcc.ConfirmDialog(id='confirm-replace',
                                        message='Analysis name exists! Are you sure you want to replace it?',
                                    ),
                                    html.Div(children="Analysis Name",style={"padding-top": "15px",
                                                        "padding-left": "25px","font-size": "9pt"}),
                                    dcc.Input(id="save-name", className="dash-input", type="text"),

                                ],
                            ),
                            html.Div(style={"text-align":"right","margin-right":"30px"},children=[html.Button("SAVE THIS ANALYSIS",id="save-add",style={"width":"200px"})])]
                        ),
                        ]
                    ))
                )]

# save analysis
@app.callback(
    [Output("confirm-replace","displayed"),Output("markdown2", "style"),Output("save-select-dropdown","options"),Output("save-select-dropdown","value")],
    [Input("markdown_close2", "n_clicks"),Input("save-add", "n_clicks"),Input('confirm-replace', 'submit_n_clicks')],
    [State("base-term", 'value'),State("added-terms-global", "children"),State("group-stored-data","data"),
    State("save-name",'value'),State("corpus-select-dropdown","value"),
    State("save-select-dropdown","options"),
    State("save-select-dropdown","value"), State("year-from","value"),State("year-to","value")])
def update_click_output2(close_click,save_click,replace_click,base,added,
                        groups,name,corpus_name,options,save_name,y_from,y_to):
    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if (prop_id == "markdown_close2") & (close_click>0):
            return [False,{"display": "none"},options,save_name]
        if ((prop_id == "save-add") | (prop_id == "confirm-replace")):
            saved={"base":base, "added":added, "groups":groups, "year":[y_from,y_to]}
            
            saves_path=corpus[corpus_name]+"groups/"
            savefiles = [f for f in listdir(saves_path) if isfile(join(saves_path, f))]
            if name in savefiles:
                if not replace_click:
                    return [True, {"display": "block"}, options,save_name]
            
            options = save_analysis_write(corpus_name, name, saved, options)

            return [False,{"display": "none"},options,"[ "+name+" ]"]
        
    return [False,{"display": "block"},options,save_name]
            
def save_analysis_write(corpus_name, name, content, options):
    with open(corpus[corpus_name]+"groups/"+name, 'w') as file:
        file.write(json.dumps(content))
        options.append({"label": "[ "+name+" ]", "value": "[ "+name+" ]"})
    file.close()
    return options

@app.callback(Output("dowload-output","children"),
              [Input("export-btn","n_clicks")],
              [State("corpus-select-dropdown","value"),State("base-term", 'value'),
              State("added-terms-global", "children"),
              State("year-from","value"),State("year-to","value")])
def export_corpus(n_clicks,corpus_name,t,added,y_from,y_to):
    if n_clicks>0:
        corpus_ind=corpus[corpus_name]
        added.append(t)
        for term in added: #handle phrases
            if "_" in term:
                added.append(term.replace("_"," "))
                added.remove(term)

        csv_string = preprocess_corpus.filter_corpus(corpus_ind, added, y_from, y_to)
        csv_string = "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(csv_string)

        ele=html.Div(style={"text-align":"right"},children=[html.A(
                html.Button("Click to Download",style={
                                        "width":"200px","margin-top":"30px","margin-bottom":"20px"}),
                download="filtered_corpus.csv",href=csv_string,target="_blank"
            )])
        return [ele]
    return [html.Div(style={"text-align":"right"},children=[html.Button("DOWNLOAD CORPUS",id="export-btn",style={
                                        "width":"200px","margin-top":"30px","margin-bottom":"20px"})])]
    

# --- build "adding terms" menu ---

#find related terms
@app.callback(Output("candidates", "children"),
              [Input("base-term", 'value'),Input("corpus-select-dropdown","value")],
              [State("base-term", 'value')]
              )
def displayClick(value, corpus_name,v):
    if v:
        term_list=[v]
        if corpus_name:
            # find top50 similar terms from word2vec
            top_terms = word2vec.find_similar(corpus_name, term_list, 50)
            
            i=0
            option_list=[]
            for term in top_terms:
                i+=1
                option_list.append(html.Div(dcc.Checklist(id={'type':'term','index':i},
                                   options=[{"label": term[0], "value": term[0]}],
                                   labelClassName="unselected-term",)   
                                ))
            return option_list
        

@app.callback(Output({'type':'term', 'index':MATCH}, 'labelClassName'),
              [Input({'type':'term', 'index':MATCH}, 'value')],
              [State({'type':'term', 'index':MATCH}, 'labelClassName')])
def displayClick(value, labelClassName):
    if not value:
        return "unselected-term"
    if labelClassName == "unselected-term":
        return "selected-term"
    else:
        return "unselected-term"


# functions for adding terms (single and phrases)
@app.callback([Output("added-terms-fromside", "children"),
              Output({'type':'term', 'index':ALL}, "value"),
              Output("added-terms-global", "children"),
              Output("manu-term","value")
              ],
              [Input("add-single", 'n_clicks'), 
               Input("form-phrase", 'n_clicks'),
               Input({'type':'selected', 'index':ALL}, 'value'),
               Input("added-terms-global-frompop", "children"),
               Input("manu-add", "n_clicks")
               ],
              [State({'type':'term', 'index':ALL}, 'value'), 
               State("added-terms-fromside", "children"),           
               State("added-terms-global", "children"),
               State("manu-term", "value"),
               ]
            )

def add_terms(single_click,phrase_click,removes,add_from_pop,manu_click,
            values,added_value, added_value_global,manu_term):
    options=added_value;
    empty_list=[]

    for (i, value) in enumerate(removes):
        if value:
            for x in range(0,len(values)):          
                empty_list.append([])
            if value[0] in added_value_global:
                added_value_global.remove(value[0])
            
            for selected_i in options:
                if selected_i['props']['children'][0]['props']['options'][0]['value']==value[0]:
                    options.remove(selected_i)
                    
            return [options, empty_list, added_value_global,""]

    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'add-single' # default
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
  
    
    if ((button_id == "add-single") | (button_id== "added-terms-global-frompop") | (button_id == "manu-add")):
        for (i, value) in enumerate(values):
            if value:
                if ((len(value)>=1)&(button_id == "add-single")):
                    if not value[0] in added_value_global: #check repeated adding
                        options.append(html.Div([dcc.Checklist(
                                            id={'type':'selected','index':i},
                                            options=[{'label': value[0], 'value': value[0]}],
                                            labelClassName="selected-term2" 
                                        )]    
                                    )),

                        added_value_global.append(" ".join(value[0].split('_'))) #update term list
            empty_list.append([]) #reset term style to "unchecked"
        if (button_id== "added-terms-global-frompop"):
            i=0
            for value in add_from_pop:
                if value:
                    if not value in added_value_global: #check repeated adding
                        options.append(html.Div([dcc.Checklist(
                                            id={'type':'selected','index':'new_'+str(i)},
                                            options=[{'label': "_".join(value.split()), 'value': value}],
                                            labelClassName="selected-term2" 
                                        )]    
                                    ))

                    added_value_global.append(value) #update term list
            i+=1

        if (button_id == "manu-add"):
            manu_term=re.sub(r'[^a-zA-Z0-9 ]', ' ', manu_term)    
            if not manu_term in added_value_global: #check repeated adding
                options.append(html.Div([dcc.Checklist(
                                         id={'type':'selected','index':"manu_"+str(len(added_value_global))},
                                            options=[{'label': "_".join(manu_term.split()), 'value': manu_term}],
                                            labelClassName="selected-term2" 
                                          )]    
                                        )),

                added_value_global.append(manu_term)


    elif button_id == "form-phrase":
        phrase=""
        for (i, value) in enumerate(values):
            if value:
                if len(value)>=1:
                    phrase+=value[0]
                    phrase+=" "
            empty_list.append([]) #reset term style to "unchecked"

        phrase=phrase[:-1]
        phrase_len=len(phrase.split())
        if phrase_len>=2:
            if not phrase in added_value_global: #check repeated adding
                options.append(html.Div([dcc.Checklist(
                                            id={'type':'selected','index':i*10},
                                            options=[{'label': "_".join(phrase.split()), 'value': phrase}],
                                            labelClassName="selected-term2" 
                                        )]    
                                    ))


                added_value_global.append(phrase) #update term list

    return [options, empty_list, added_value_global,""]


# --- build tabs (right window) ---

def build_tabs():
    return html.Div(
        id="tabs",
        className="tabs",
        children=[
            dcc.Tabs(
                id="app-tabs",
                value="tab00",
                className="custom-tabs",
                children=[
                    dcc.Tab(
                        id="Overview-tab",
                        label="Overview",
                        value="tab00",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="Specs-tab",
                        label="Sentences",
                        value="tab1",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="Group-tab",
                        label="Grouping",
                        value="tab22",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                        ),
                    dcc.Tab(
                        id="Graph-tab",
                        label="Graphs",
                        value="tab3",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                ],
            )
        ],
    )

# --- build "sentences" tab ---
# search, and show ranking

def build_tab_1(corpus_name):
    corpus_ind_dir=corpus[corpus_name]
    display_fileds = preprocess_corpus.get_table_fieldnames(corpus_ind_dir)
    display_fileds.append("score")
    opt=[{'label': f.upper(), 'value': f} for f in display_fileds]
    
    return [
        dcc.Store(id='memory-output'),
        dcc.Loading(color="rgba(240, 218, 209,0.8)",type="cube",style={"padding-top":"25%"},children=[
            html.Div(style={"margin-left": "30px","margin-top": "1.5%", "font-variant": "all-small-caps","color": "#e85e56"},
                children="QUERY"),
            html.Div(id="current_query",style={"margin-left": "50px", "color": "#f4e9dc","width": "42%"},
                children=""),
            html.Div(style={"display":"flex"},children=[
                html.Div(style={"width": "430px"},
                    children=[html.Div(style={"margin-left": "30px", "font-variant": "all-small-caps","color": "#e85e56"},
                                            children="DISPLAYED COLUMNS"),
                                    dcc.Dropdown(id="r_table_paras",className="table-dropdown",style={"margin-left":"10%"},
                                                options=opt,value=display_fileds,multi=True)]
                        ),
                html.Div(children=[html.Div(style={"font-variant": "all-small-caps","color": "#e85e56"},
                                            children="SENTS PER PAGE"),
                                    daq.NumericInput(id="n_pp",style={"margin-top": "4px","margin-left": "10%","color":"#f4e9dc","width": "40%"},
                                            className="year-selector sent-pp",min=10,max=1000,value=16)]
                        )
                ]),
            
            
            html.Div(
                id="rel_sent",style={"position": "absolute","right": "1.5%","top": "90px","font-variant": "all-small-caps"},className="side-by-side",
                children=[""]
            ),
            html.Div(
                id="ranking-table",style={"margin-top":"1%"},
                className="output-datatable"
            ),
            ]),
        html.Div(
            id="full-sentence-pop-up",
            children=[
            ]
        )
    ]


@app.callback([Output("ranking-table", "children"),Output('memory-output', 'data'),
                Output("rel_sent","children"),Output("current_query","children")],
              [Input("base-term", 'value'),Input("corpus-select-dropdown","value"),
              Input("added-terms-global", "children"),Input("year-from","value"),Input("year-to","value"),
              Input("r_table_paras",'value'),Input("n_pp","value")],
              [State("base-term", 'value'),
               State('memory-output', 'data'),State("rel_sent","children"),State("current_query","children")]
              )
def show_ranking(base_term,corpus_name,added,y_from,y_to,cols,npp,t, mo_result,rs,cq):

    if corpus_name:
        corpus_ind = corpus[corpus_name]
        if base_term:
            added.append(t) #add base term
            if y_from > y_to:
                return [html.Div("Please correct the year range."),"","",""]
            for term in added: #handle phrases
                if "_" in term:
                    added.append(term.replace("_"," "))
                    added.remove(term)
            
            ctx = dash.callback_context
            if not ctx.triggered:
                button_id = '' # default
            else:
                button_id = ctx.triggered[0]['prop_id'].split('.')[0]


            if ((button_id == "r_table_paras")|(button_id == "n_pp")): # no need to search index again, just change layout
                result = mo_result[0]
                tooltip = mo_result[1]
                if len(result)>0:
                    result_df = pd.DataFrame.from_records(result)
                    columns_d = [{"id": "id", "name": "id"}]
                    columns_d.append({"id": "sentence", "name": "sentence"})
                    for c in result_df.columns:
                        if ((c != "id")&(c != "sentence")&(c in cols)):
                            columns_d.append({"id": c, "name": c})

                    return [build_ranking_table(result,columns_d,tooltip,npp),
                            mo_result,rs,cq]
                else:
                    return [html.Div("No result"),mo_result,rs,cq]


            else: # need to search the index
                
                result, tooltip, rel_sent_no, sent_no, rel_article_no, article_no=preprocess_corpus.search_corpus(corpus_ind, added, y_from, y_to)
                
                result_df = pd.DataFrame.from_records(result)
                del result_df["document"]
                

                rel_sent_div=[  html.Div(className="number-card-1",children=[
                                    html.Div(className="number-back",children=[
                                        html.Div(className="number-dis",children=[rel_sent_no]),
                                        html.Div(className="number-label",children=[html.Div("RELEVANT SENTENCES")]),
                                    ]),html.Div("|",className="saperator"),
                                    html.Div(className="number-back",children=[
                                        html.Div(className="number-dis2",children=[sent_no]),
                                        html.Div(className="number-label2",children=[html.Div("TOTAL SENTENCES")]),  
                                    ])
                                ]),
                                html.Div(className="number-card-2",children=[
                                    html.Div(className="number-back",children=[
                                        html.Div(className="number-dis",children=[rel_article_no]),
                                        html.Div(className="number-label",children=[html.Div("RELEVANT DOCUMENTS")]),                 
                                    ]),html.Div("|",className="saperator"),
                                    html.Div(className="number-back",children=[
                                        html.Div(className="number-dis2",children=[article_no]),
                                        html.Div(className="number-label2",children=[html.Div("TOTAL DOCUMENTS")]),    
                                    ])
                                ])
                            ]
                if len(result)>0:
                    columns_d = [{"id": "id", "name": "id"}]
                    columns_d.append({"id": "sentence", "name": "sentence"})
                    for c in result_df.columns:
                        if ((c != "id")&(c != "sentence")&(c in cols)):
                            columns_d.append({"id": c, "name": c})       
                    
                    return [build_ranking_table(result,columns_d,tooltip,npp), [result,tooltip], rel_sent_div," | ".join(added)]
                else:
                    return [html.Div("No result"),"",""," | ".join(added)]
        else:
            return [html.Div("Please type in the base term in the left pane"),"","",""]
    else:
        return [html.Div("Start by selecting a corpus"),"","",""]

def build_ranking_table(result,columns_d,tooltip,npp):
    return dash_table.DataTable(
                            id="ranking_table",
                            sort_action='native',
                            sort_mode='multi',
                            filter_action="native",
                            style_header={"fontWeight": "bold", "color": "inherit","border-bottom":"1px dashed"},
                            style_as_list_view=True,
                            fill_width=True,
                            page_size=npp,
                            style_cell_conditional=[
                                {"if": {"column_id": "sentence"}, 'width': '500px',"maxWidth":'500px'},
                                {"if": {"column_id": "title"}, "padding-left":"15px","maxWidth":'300px'},
                                {'if': {'column_id': 'author'},'maxWidth': '150px'},
                                {'if': {'row_index': 'odd'},"backgroundColor":"#49494966"}
                            ],
                            style_cell={
                                "backgroundColor": "transparent",
                                "fontFamily": "Open Sans",
                                "padding": "0 0.2rem",
                                "color": "#f4e9dc",
                                "border": "none",
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                                'width': '55px',
                                'minWidth': '55px',
                                'maxWidth': '200px',
                                "padding-left":"10px",
                                "textAlign": "left"
                            },
                            
                            css=[
                                #{"selector": ".dash-cell.focused","rule": "background-color: #f4e9dc !important; border:none;"},
                                {"selector": "table", "rule": "--accent: #e85e56;"},
                                {"selector": "tr:hover td", "rule": "color: #e85e56 !important; background-color:transparent !important; cursor:pointer;height:10px;"},
                                {"selector": "td:hover", "rule": "border-bottom: dashed 0px !important;"},
                                {"selector": ".dash-spreadsheet-container table", 
                                    "rule": '--text-color: #e85e56 !important'},
                                {"selector":".previous-next-container","rule":"float: left;"},
                                {"selector": "tr", "rule": "background-color: transparent;"},
                                {"selector": ".current-page", "rule": "background-color: transparent;"},
                                {"selector":".current-page::placeholder","rule":"color:#e85e56;"},
                                {"selector": ".column-header--sort","rule":"color: #e85e56; padding-right:3px;"}
                            ],
                            style_data_conditional=[
                            {"if": {"state": "active"},  # 'active' | 'selected'
                                "border": "0px solid"}]+
                            data_bars(result, 'score'),
                            data=result,
                            columns=columns_d,
                            tooltip_data=tooltip,
                            tooltip_delay=1000, #1s
                            tooltip_duration=None,
                            selected_rows=[]
                        )

def data_bars(df, column):
    Scores=[]
    for r in df:
        Scores.append(r[column])

    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((max(Scores) - min(Scores)) * i) + min(Scores)
        for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        styles.append({
            'if': {
                'filter_query': (
                    '{{{column}}} >= {min_bound}' +
                    (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                'column_id': column
            },
            'background': (
                """
                    linear-gradient(90deg,
                    #f4e9dc 0%,
                    #f4e9dc {max_bound_percentage}%,
                    #1E1C24 {max_bound_percentage}%,
                    #1E1C24 100%)
                """.format(max_bound_percentage=max_bound_percentage)
            ),
            'paddingBottom': 2,
            'paddingTop': 2,
            'border-bottom': "1px dashed #1e1c24",
            'color':'#494949'
        })
    return styles

# pop-up window
@app.callback(
    [Output("full-sentence-pop-up", "children")],
    [Input('ranking_table', 'active_cell')],
    [State('memory-output', 'data')])
def update_graphs(active_cell,data):
    if active_cell:
        for i in data[0]:
            if i['id'] == active_cell['row_id']:
                return generate_modal(i['document'])

    raise PreventUpdate 

# term selection in the sentence pop up window
@app.callback(
    Output("markdown", "style"),[Input("markdown_close", "n_clicks")])
def update_click_output(close_click):
    ctx = dash.callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "markdown_close":
            return {"display": "none"}

    return {"display": "block"}

@app.callback(Output({'type':'sent_term', 'index':MATCH}, 'labelClassName'),
              [Input({'type':'sent_term', 'index':MATCH}, 'value')],
              [State({'type':'sent_term', 'index':MATCH}, 'labelClassName')])
def displayClick(value, labelClassName):
    if not value:
        return "unselected-sent-term"
    if labelClassName == "unselected-sent-term":
        return "selected-sent-term"
    else:
        return "unselected-sent-term"


# build modal (pop up window)
def generate_modal(text=""):
    word_list = text.split()
    option_list=[]
    i=0
    for term in word_list:
        option_list.append(html.Div(dcc.Checklist(id={'type':'sent_term','index':i},
                                   options=[{"label": term, "value": term}],
                                   labelClassName="unselected-sent-term",)
                                ))
        i+=1
            
    return [html.Div(
        id="markdown",
        style={"display": "block"},
        className="modal",
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="markdown-text",id="pop-up-sent",
                        children=option_list
                    ),html.Br(),
                    html.Button("Check Frequency",
                            id="check_sf",n_clicks=0
                    ),html.Button("ADD TO THE QUERY",style={"margin-left":"20px"},
                            id="add-to-query",n_clicks=0       
                    ),
                    html.Br(),html.Br(),
                    html.Div(
                        id="sf_result_container",
                        children=[dash_table.DataTable(
                        id='sf_result11',
                        sort_action='native',
                        sort_mode='multi',
                        columns=[{"id": c, "name": c} for c in ["Term","Frequency"]],
                        style_cell_conditional=[
                            {"if": {"column_id": "Term"}, "textAlign": "left"},
                            {"if": {"state": "active"}, "border": "0px solid"}
                        ],

                        
                        style_cell={
                            "backgroundColor": "#494949","fontFamily": "Open Sans","padding": "0 2rem",
                            "color": "f4e9dc","border": "none",'overflow': 'hidden','textOverflow': 'ellipsis',
                        },
                        css=[
                            {"selector": "tr:hover td", "rule": "color: #e85e56 !important;"},
                            {"selector": "td", "rule": "border-bottom: dashed 1px !important;"},
                            {"selector": ".dash-cell.focused",
                                "rule": "background-color: #494949 !important;"},
                            {"selector": ".dash-spreadsheet-container table", 
                                "rule": '--text-color: #f4e9dc !important'},
                            {"selector": "table", "rule": "--accent: #f4e9dc;"},
                            {"selector": "tr", "rule": "background-color: transparent"},
                            {"selector": ".column-header--sort","rule":"color: #e85e56; padding-right:3px;"}
                        ],
                        data=[{"Term":"Please select...","Frequency":""}])]                 
               
                    )
                ],
            )
        ),
    )]


# add terms from the pop up window
@app.callback([Output({'type':'sent_term', 'index':ALL}, "value"),
              Output("added-terms-global-frompop", "children")
              ],
              [Input("add-to-query", 'n_clicks')],
              [State({'type':'sent_term', 'index':ALL}, 'value'),               
               State("added-terms-global", "children")]
            )
def add_from_pop(n_clicks,values,added_value_global):

    empty_list=[]
    new_add=[]

    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'add-to-query' # default
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "add-to-query":
        phrase=""
        for (i, value) in enumerate(values):
            if value:
                if len(value)>=1:
                    phrase+=re.sub(r'[^a-zA-Z0-9_]', '', value[0])
                    phrase+=" "
            empty_list.append([]) #reset term style to "unchecked"

        phrase=phrase[:-1]
        phrase_len=len(phrase.split())
        if phrase_len>=1:
            if not phrase in added_value_global:
                new_add.append(phrase)

    if n_clicks>0:
        return [empty_list,new_add]
    else:
        raise PreventUpdate


# function for checking sentence frequency
@app.callback([Output("sf_result_container", "children")],
              [Input("check_sf", 'n_clicks')],
              [State({'type':'sent_term', 'index':ALL}, 'value'),
               State("corpus-select-dropdown","value"),State("sf_result11","data")]
            )
def return_sf(n_clicks,values,corpus_name,tabledata):
    if n_clicks>0:
        query=""
        for (i, value) in enumerate(values):
            if value:
                if len(value)>=1:
                    if len(query)>0:
                        query+=" "
                    query+=value[0]
        
        corpus_ind = corpus[corpus_name]          
        (query, sf)=preprocess_corpus.check_sf(corpus_ind, [query])
        if n_clicks>1:
            tabledata.append({"Term":query[0],"Frequency":str(sf[0])})
        else:
            tabledata=[{"Term":query[0],"Frequency":str(sf[0])}]
        
        return [dash_table.DataTable(
                        id='sf_result11',
                        sort_action='native',
                        sort_mode='multi',
                        row_deletable=True,
                        columns=[{"id": c, "name": c} for c in ["Term","Frequency"]],
                        style_cell_conditional=[
                            {"if": {"column_id": "Term"}, "textAlign": "left"},
                            {"if": {"state": "active"}, "border": "0px solid"}
                        ],
                        style_cell={
                            "backgroundColor": "#494949",
                            "fontFamily": "Open Sans",
                            "padding": "0 2rem",
                            "color": "#f4e9dc",
                            "border": "none",
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        },
                        css=[
                            {"selector": "tr:hover td", "rule": "color: #e85e56 !important;"},
                            {"selector": "td", "rule": "border-bottom: dashed 1px !important;"},
                            {"selector": ".dash-cell.focused",
                                "rule": "background-color: #494949 !important;"},
                            {"selector": ".dash-spreadsheet-container table", 
                                "rule": '--text-color: #91dfd2 !important'},
                            {"selector": "table", "rule": "--accent: #f4e9dc;"},
                            {"selector": "tr", "rule": "background-color: transparent"},
                            {"selector": ".column-header--sort","rule":"color: #e85e56; padding-right:3px;"}
                        ],
                        data=tabledata
                        )]
    else:

        return [dash_table.DataTable(
                        id='sf_result11',
                        sort_action='native',
                        sort_mode='multi',
                        columns=[{"id": c, "name": c} for c in ["Term","Frequency"]],
                        style_cell_conditional=[
                            {"if": {"column_id": "Term"}, "textAlign": "left"},
                            {"if": {"state": "active"}, "border": "0px solid"}
                        ],
                        style_cell={
                            "backgroundColor": "#494949",
                            "fontFamily": "Open Sans",
                            "padding": "0 2rem",
                            "color": "#f4e9dc",
                            "border": "none",
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        },
                        css=[
                            {"selector": "tr:hover td", "rule": "color: #e85e56 !important;"},
                            {"selector": "td", "rule": "border-bottom: dashed 1px !important;"},
                            {"selector": ".dash-cell.focused",
                                "rule": "background-color: #494949 !important;"},
                            {"selector": ".dash-spreadsheet-container table", 
                                "rule": '--text-color: #e85e56 !important'},
                            {"selector": "table", "rule": "--accent: #f4e9dc;"},
                            {"selector": "tr", "rule": "background-color: transparent"},
                            {"selector": ".column-header--sort","rule":"color: #e85e56; padding-right:3px;"}
                        ],
                        data=[{"Term":"Please select...","Frequency":""}])]



# --- build "grouping" tab ---

def build_tab_group():
    return [html.Div(id="group-tab-container",children=[])]

@app.callback([Output("group-tab-container","children"),
                Output("word-card-data","data")],
              [ Input("base-term", 'value'),
                Input("corpus-select-dropdown","value"),
                Input("added-terms-global", 'children'),
                Input("year-from","value"),
                Input("year-to","value")
                ],
              [ State("base-term", 'value'),
                State("group-stored-data","data"),
                State("word-card-data","data")]
            )
def build_tab_group_content(base_term,corpus_name,added,y_from, y_to, t, stored,stored_wordcards):
    if corpus_name:
        corpus_ind = corpus[corpus_name]
        if base_term:
            added.insert(0,t) #add base term

            sf,rel_article_no,df=preprocess_corpus.check_df_year(corpus_ind,added,y_from,y_to)
            
            opt_list=[]
            for term in added: #handle phrases
                opt_list.append({'label': term, 'value': term})

            colors=['rgba(228,111,86,0.85)',#red
            'rgba(130,157,175,0.85)',#purple
            'rgba(141,211,182,0.85)',#green
            'rgba(76,143,168,0.85)',#blue
            'rgba(238,202,59,0.85)',#yellow 
            'rgba(164,201,69,0.85)',#yellowgreen         
            ]

            tf = preprocess_corpus.check_tf_year(corpus_ind,added)

            cards=[]
            for j in range(0,len(added)):
                if len(added[j].split())>1:
                    added[j]="_".join(added[j].split())
                term_graph, term_total = build_single_line_graph(sf,added[j],j)
                cards.append(
                        html.Div(className="word-card",children=[
                        html.Div(added[j],className="term-title"),
                        html.Div(className="side-by-side",children=[
                            html.Div(children=[
                                html.Div(className="card-display-label2",children=[
                                    html.Div("Sentence Frequency By Year")]),
                                html.Div(term_graph)]
                            ),
                            html.Div(style={"width":"60px","margin-left":"15px","position":"relative"},children=[
                                html.Div(style={"bottom":"110px"},className="card-display-label",children=[
                                    html.Div("No. of Relevant Sentences"),
                                    html.Div(term_total,className="term-frequency",style={"color":colors[j%6]}), 
                                ]),
                                html.Div(style={"bottom":"55px"},className="card-display-label",children=[
                                    html.Div("Total Word Frequency"),
                                    html.Div(tf[added[j]],className="term-frequency",style={"color":colors[j%6]}), 
                                ]),
                                html.Div(style={"bottom":"0px"},className="card-display-label",children=[
                                    html.Div("No. of Relevant Documents"),
                                    html.Div(rel_article_no[added[j]],className="term-frequency",style={"color":colors[j%6]}), 
                                ])
                            ])
                            ]
                        )] 
                        )
                    )
            if stored: # but len(added) != len(stored_wordcards):
                return[
                    [html.Div(id="display-cards",children=cards),
                    html.Div(id="make-groups",children=load_store(stored, opt_list)),html.Br(),         
                    html.Div(className="side-by-side",children=[
                        html.Div(id="add_group_bt",children=html.Button("ADD A GROUP",id="add_group",
                                    n_clicks=0)),
                        html.Div(id="comp_group_bt",children=html.Button("COMPOUND GROUPS",id="comp_group",
                                    n_clicks=0))])
                    ],
                    cards
                ]

            return [
                [html.Div(id="display-cards",children=cards),
                html.Div(id="make-groups",children=[
                    html.Div(children=[
                        dcc.Input(id={'type':'group_label', 'index':0},value="Group 0", className="group-label"),
                        dcc.Dropdown(
                            id={'type':'group', 'index':0},
                            options=opt_list,
                            value=[],
                            multi=True
                        ),daq.ToggleSwitch(id={'type':'group_toggle', 'index':0},
                                    className="query-toggle",
                                     label=[ "Any","All"],
                                     color="#e85e56",size=40,
                                     value=True),
                        html.Div(style={"display":"none"},id={'type':'comp_group',"index":0},children="")
                    ],  style={"padding-left":20},
                        className="group-dropdown")  
                ]),html.Br(),
                    html.Div(className="side-by-side",children=[
                        html.Div(id="add_group_bt",children=html.Button("ADD A GROUP",id="add_group",
                                    n_clicks=0)),
                        html.Div(id="comp_group_bt",children=html.Button("COMPOUND GROUPS",id="comp_group",
                                    n_clicks=0))])
                    ],
                cards
            ]
        else:
            return [html.Div(className="warning-text",children="Please enter base term."),""]
    else:
        return [html.Div(className="warning-text",children="Please select a corpus."),""]

# when back to the grouping tab, reload groups if any generated before
def load_store(store,opt_list):
    groups=[]
    group_words=store[0] # group words
    group_names=store[1] # group names
    group_anyall=store[2]# group any/all selection
    group_compund=store[3] # compund groups


    for i in range(0,len(group_names)):
        if group_compund[i]=="":
            opt=opt_list
        else:
            group_list=[]
            for y in range(0,len(group_names)): 
                if i != y:
                    if group_anyall[y]:
                        group_list.append({'label': group_names[y], 'value': "+".join(group_words[y])})            
                    else:
                        group_list.append({'label': group_names[y], 'value': "/".join(group_words[y])})

            opt=group_list

        child=[dcc.Input(id={'type':'group_label', 'index':i},value=group_names[i], className="group-label"),
                dcc.Dropdown(id={'type':'group', 'index':i},
                            options=opt,value=group_words[i],multi=True),
                
                daq.ToggleSwitch(id={'type':'group_toggle', 'index':i},
                            className="query-toggle",label=[ "Any","All"],color="#e85e56",size=40,
                            value=group_anyall[i])]
        if i >0:
            child.append(html.Div(className="delete-container",
                                        children=html.Button("X Delete",
                                        id={'type':'delete_group', 'index':i},
                                        n_clicks=0,className="closeButton",
                                )))
        
        if group_compund[i]=="":
            child.append(html.Div(id={'type':'comp_group',"index":i},children=""))
            groups.append(html.Div(children=child, style={"padding-left":20},className="group-dropdown"))
        else:
            child.append(html.Div(style={"display":"none"},id={'type':'comp_group',"index":i},children="True"))
            groups.append(html.Div(children=child, style={"padding-left":20},className="c-group-dropdown"))
    return groups                         


# functions for create / change / delete groups
@app.callback(Output("group-stored-data","data"),
             [Input({'type':'group', 'index':ALL}, 'value'),
              Input({'type':'group_label', 'index':ALL},'value'),
              Input({'type':'group_toggle', 'index':ALL},'value'),
              Input({'type':'delete_group', 'index':ALL},'n_clicks'),
              Input({'type':'comp_group',"index":ALL},'children')],
             [State("make-groups","children")]
    )
def update_group(changed,changed_l,changed_t,delete, comp_group, children):   
    if len(changed_l)>1:
        for i in range(1,len(changed_l)):
            if delete[i-1]>0:
                del changed[i]
                del changed_l[i]
                del changed_t[i]

    return [changed,changed_l,changed_t,comp_group]

@app.callback(Output("make-groups","children"),
              [ Input("add_group", 'n_clicks'),
                Input({'type':'delete_group', 'index':ALL},'n_clicks'),
                Input("comp_group", 'n_clicks'),
              ],
              [ State("added-terms-global", 'children'),
                State("base-term", 'value'), 
                State("make-groups","children")]
            )
def add_delete_group(n_clicks,delete,comp_click, added,t,children):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = '' # default
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "add_group":
        if n_clicks>0:
            added.insert(0,t) #add base term
            opt_list=[]
            for term in added: #handle phrases
                opt_list.append({'label': term, 'value': term})
            group_no=str(int(children[-1]['props']['children'][0]['props']['id']['index'])+1)
            new_element=html.Div(children=[
                                dcc.Input(id={'type':'group_label', 'index':group_no},value="Group "+group_no, className="group-label"),
                                dcc.Dropdown(
                                    id={'type':'group', 'index':group_no},
                                    options=opt_list,
                                    value=[],
                                    multi=True
                                ),daq.ToggleSwitch(id={'type':'group_toggle', 'index':int(group_no)},
                                        className="query-toggle",
                                         label=["Any","All"],
                                         color="#e85e56",size=40,
                                         value=True),
                                html.Div(className="delete-container",
                                         children=html.Button(
                                            "X Delete",
                                            id={'type':'delete_group', 'index':group_no},
                                            n_clicks=0,
                                            className="closeButton",
                                        ),
                                    ),
                                html.Div(style={"display":"none"},id={'type':'comp_group',"index":group_no},children="")
                                ],
                                style={"padding-left":20},
                                className="group-dropdown"
                            )       
            children.append(new_element)
        return children
    elif button_id == "comp_group":
        if comp_click>0:
            group_names=[]
            group_values=[]
            group_anyalls=[]
            for x in range(0, len(children)):
                group_names.append(children[x]['props']['children'][0]['props']['value'])
                group_values.append(children[x]['props']['children'][1]['props']['value'])
                group_anyalls.append(children[x]['props']['children'][2]['props']['value'])

            opt_list=[]
            for y in range(0,len(group_names)): 
                if group_anyalls[y]:
                    opt_list.append({'label': group_names[y], 'value': "+".join(group_values[y])})
                else:
                    opt_list.append({'label': group_names[y], 'value': "/".join(group_values[y])})

            group_no=str(int(children[-1]['props']['children'][0]['props']['id']['index'])+1)
            new_element=html.Div(children=[
                                dcc.Input(id={'type':'group_label', 'index':group_no},value="Compound "+group_no, className="group-label"),
                                dcc.Dropdown(
                                    id={'type':'group', 'index':group_no},
                                    options=opt_list,
                                    value=[],
                                    multi=True
                                ),daq.ToggleSwitch(id={'type':'group_toggle', 'index':int(group_no)},
                                        className="query-toggle",
                                         label=["Any","All"],
                                         color="#e85e56",size=40,
                                         value=True),
                                html.Div(className="delete-container",
                                         children=html.Button(
                                            "X Delete",
                                            id={'type':'delete_group', 'index':group_no},
                                            n_clicks=0,
                                            className="closeButton",
                                        ),
                                    ),
                                html.Div(style={"display":"none"},id={'type':'comp_group',"index":group_no},children="True")
                                ],
                                style={"padding-left":20},
                                className="c-group-dropdown"
                            )       
            children.append(new_element)
        return children

    else:
        for i in range(0, len(delete)):
            if delete[i]>0:
                del children[i+1]
        return children


# --- build "graphs" tab --- 

def build_tab_3():
    return [html.Div(id="graphs-tab-container",children=[
            dcc.Dropdown(id="count_prop-dropdown",className="mode-select-dropdown",
                            options=[{"label": "No. of Relevant Sentences", "value": "count_sent"},
                                     {"label": "No. of Relevant Documents", "value": "count_doc"},
                                     {"label": "Prop. of Relevant Documents", "value": "prop_doc"}],
                            value="count_sent", 
                            clearable=False,         
                            ),html.Br(),
        ])]

@app.callback(Output("graphs-tab-container","children"),
              [ Input("base-term", 'value'),
                Input("corpus-select-dropdown","value"),
                Input("added-terms-global", "children"), # does not have AAA+BBB
                Input("count_prop-dropdown","value"),
                Input("year-from","value"),Input("year-to",'value')],
              [State("base-term", 'value'),State("group-stored-data","data"),
              State("graphs-tab-container","children")]
            )        
def build_tab_graphs_content(base_term,corpus_name,added,mode,y_from,y_to,t,groups,children):
    if not groups[0][0]:
        children.append(html.Div(className="warning-text",children="Please create a group."))
        return children
    if corpus_name:
        corpus_ind = corpus[corpus_name]
        if base_term:
            
            all_terms=[]
            for group_terms in groups[0]:
                for t in group_terms:
                    if "_" in t:
                        t = t.replace("_"," ")
                    if not t in all_terms:
                        all_terms.append(t)
            
            if y_from>y_to:
                children.append(html.Div(className="warning-text",children="Please correct the year range."))
                return children

            tf_sent,relno,tf_doc=preprocess_corpus.check_df_year(corpus_ind,all_terms,y_from,y_to)
            doc_num_year=preprocess_corpus.get_num_doc_year(corpus_ind)

            graph_list=[]
            group_sf_dict={}
            for g in range(0,len(groups[1])):
                
                group_name = groups[1][g]
                group_words = groups[0][g]
                group_all=groups[2][g]
                
                if len(group_words)>0:
                    group_term_sf,group_term_df=preprocess_corpus.check_group_sf_year(corpus_ind,group_words,group_all)

                    graph_l, group_sf = build_line_graph(tf_sent,tf_doc,group_term_sf,group_term_df,doc_num_year,group_name,group_words,mode,y_from,y_to)
                    graph_list.append(graph_l)
                    group_sf_dict[group_name]=group_sf
            
            return [children[0],html.Div(children=build_big_graph(group_sf_dict,doc_num_year,y_from,y_to)),html.Div(id="display-group-graph",children=graph_list)]

        else:
            children.append(html.Div(className="warning-text",children="Please enter base term."))
            return children
    else:
        children.append(html.Div(className="warning-text",children="Please select a corpus."))
        return children

def build_single_line_graph(tf,t,i):
    x=[]
    y=[]
    total=0
    data_list=[]
    colors=['rgba(228,111,86,0.85)',#red
            'rgba(130,157,175,0.85)',#purple
            'rgba(141,211,182,0.85)',#green
            'rgba(76,143,168,0.85)',#blue
            'rgba(238,202,59,0.85)',#yellow 
            'rgba(164,201,69,0.85)',#yellowgreen         
    ]
    colorfill=['rgba(228,111,86,0.02)',#red
            'rgba(130,157,175,0.02)',#purple
            'rgba(141,211,182,0.02)',#green
            'rgba(76,143,168,0.02)',#blue
            'rgba(238,202,59,0.02)',#yellow 
            'rgba(164,201,69,0.02)',#yellowgreen         
    ]
    if len(t.split())>1:
        t="_".join(t.split())
        
    for year in sorted (tf[t].keys()):
        x.append(year)
        y.append(tf[t][year])
        total+=tf[t][year]

    data_list.append({
            "x":x,
            "y":y,
            "mode": "lines",
            "name": t,
            "marker_size":6,
            "line": {                
                "width": 2.5,
                "shape":"spline",
            },
            "fill":"tozeroy",
            "fillcolor":colorfill[i%6]

        })
    return [dcc.Graph(
                id="line-graph-"+t,
                figure=go.Figure(
                    {
                        "data": data_list,
                        "layout": {
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                            "xaxis": dict(
                                showline=False, showgrid=False, zeroline=False,color="#494949"
                            ),
                            "yaxis": dict(
                                showgrid=False, showline=False, zeroline=False,color="#494949"
                            ),
                            "autosize":False,
                            "colorway": [colors[i%6]],
                            "template":"plotly_dark",
                            "width":260,
                            "height":180,
                            "margin":dict(l=1,r=1,b=1,t=0,pad=0)
                        },
                    }
                ),
            ),total]

def build_line_graph(tf,tf_doc,sf,df,doc_num_year,group_name,group_terms,mode,year_from,year_to):
    data_list=[] 
    tf_bar_list=[]
    doc_num=[]
    year_list=[]
    year_list2=[]
    group_sf=[]

    colors=['rgba(228,111,86,0.85)',#red
            'rgba(130,157,175,0.85)',#purple
            'rgba(141,211,182,0.85)',#green
            'rgba(76,143,168,0.85)',#blue
            'rgba(238,202,59,0.85)',#yellow 
            'rgba(164,201,69,0.85)',#yellowgreen         
    ]
    color_used=[]


    for year in doc_num_year:
        if ((int(year)<year_from)|(int(year)>year_to)): #out of year range
            continue
        year_list.append(int(year))
        doc_num.append(doc_num_year[year])

        if int(year) in sf:
            if mode=="count_sent":
                group_sf.append(sf[int(year)])
            elif mode=="count_doc":
                group_sf.append(df[int(year)])
            elif mode=="prop_doc":
                group_sf.append(df[int(year)]*1.0/float(doc_num_year[year]))
        else:
            group_sf.append(0)

    if ((mode == "count_sent")|(mode == "count_doc")):
        data_list.append({
                "name":"No. of Documents (total)",
                "x":year_list,
                "y":doc_num,
                "type":"bar",
                "marker":{"line":{"width":0},"color":"#494949","opacity":0.3},
                "base":0
            })

    if mode == "count_sent":
        f_label = "Relevant Sentences"
    else:
        f_label = "Relevant Documents"
    data_list.append({
            "name":f_label,
            "x":year_list,
            "y":group_sf,
            "mode":"lines",
            "line": {
                "color": '#F7cbc7',
                "width": 1,
                "shape":"spline",
                "dash":"dot"
            },
            "fill":"tozeroy",
            "fillcolor":"rgba(247, 203, 199, 0.07)"
        })

    for t in group_terms:
        x=[]
        y=[]
        total=0

        if len(t.split())>1:
            t="_".join(t.split())

        j=0
        for k in tf:
            if k==t:
                color_used=colors[j%len(colors)]

            j+=1
     
        for year in doc_num_year:
            if ((int(year)<year_from)|(int(year)>year_to)): #out of year range
                continue
            year=int(year)
            x.append(year)
            if year in tf[t]:
                if mode == "count_sent":
                    y.append(tf[t][year])
                elif mode == "count_doc":
                    y.append(tf_doc[t][year])
                elif mode == "prop_doc":
                    y.append(tf_doc[t][year]*1.0/float(doc_num_year[str(year)]))
            else:
                y.append(0)
        
        
        data_list.append({
            "x":x,
            "y":y,
            "mode": "lines+markers",
            "name": t,
            "marker_size":8,
            "line":{
                "shape":'spline',
                "color":color_used
            },
        })
    
    
    return [html.Div(
        id="line-graph-container",
        className="figure-side-by-side",
        children=[
            dcc.Graph(
                id="line-graph",
                figure=go.Figure(
                    {
                        "data": data_list,
                        "layout": {
                            'title': {"text":group_name, "font":{"family":"Droid Serif","size":20,"color":"rgba(244,233,220,0.5)"}},
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                            "xaxis": dict(
                                showline=False, showgrid=False, zeroline=False,color="#494949"
                            ),
                            "yaxis": dict(
                                showgrid=False, showline=False, zeroline=False,color="#494949"
                            ),
                            "autosize":False,
                            "margin":dict(l=15,r=15,b=10,t=40,pad=4),
                            "legend":dict(font=dict(color="#f4e9dc")),
                            "template":"plotly_dark",
                            "width":500,
                            "height":270,
                            "legend":dict(yanchor="top",y=0.99,xanchor="left",x=0.01),
                            "barmode":'stack'
                        },
                    }
                ),
            ),
        ],
    ), group_sf]

# build the top big graph
def build_big_graph(group_sf_dict,doc_num_year,year_from,year_to):
    color_used=['#4c78a8',#blue
            '#f58518',#orange
            '#e45756',#red
            'rgb(141,211,199)',#green
            'rgb(153,201,69)',#yellowgreen
            '#eeca3b',#yellow            
    ]
    x=[]
    data_list=[]
    
    for year in doc_num_year:
        if ((int(year)<year_from)|(int(year)>year_to)): #out of year range
            continue
        x.append(year)

    for group_name in group_sf_dict:

        data_list.append({
            "x":x,
            "y":group_sf_dict[group_name],
            "mode": "lines+markers",
            "name": group_name,
            "marker_size":8,
            "line": {
                "width": 1,
                "shape":"spline",
                "dash":"dot"
            },
        })

    return html.Div(
        id="group-line-graph-container",
        className="figure-side-by-side",
        children=[
            dcc.Graph(
                id="group-line-graph",
                figure=go.Figure(
                    {
                        "data": data_list,
                        "layout": {
                            'title': {"text":"All Groups", "font":{"family":"Droid Serif","size":20,"color":"rgba(244,233,220,0.5)"}},
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                            "xaxis": dict(
                                showline=False, showgrid=False, zeroline=False,color="#494949"
                            ),
                            "yaxis": dict(
                                showgrid=False, showline=False, zeroline=True,color="#494949",
                                zerolinecolor="#494949",zerolinewidth=0.5
                            ),
                            "autosize":False,
                            "colorway": color_used,#px.colors.qualitative.Prism,
                            "margin":dict(l=55,r=15,b=40,t=40,pad=4),
                            "legend":dict(font=dict(color="#f4e9dc")),
                            "template":"plotly_dark",
                            "width":1100,
                            "height":330,
                            "legend":dict(yanchor="top",y=0.99,xanchor="left",x=0.01),
                        },
                    }
                ),
            )
            ]
            )


# --- build "overview" tab ---

def plotly_wordcloud(word_frequency):
    
    word_cloud = WordCloud(stopwords=set(STOPWORDS), max_words=100, max_font_size=90)
    word_cloud.generate_from_frequencies(word_frequency)

    word_list = []
    freq_list = []
    
    i=0

    for (word, freq), fontsize, position, orientation, color in word_cloud.layout_:
        word_list.append(word)
        freq_list.append(freq)
        
        i+=1


    # get the relative occurence frequencies
    new_freq_list = []
    for i in freq_list:
        new_freq_list.append(i * 50)


    word_list_top = word_list[:30]
    word_list_top.reverse()
    
    freq_list_top = []
    for w in word_list_top:
        freq_list_top.append(word_frequency[w])
    

    frequency_figure_data = {
        "data": [
            {
                "y": word_list_top,
                "x": freq_list_top,
                "type": "bar",
                "name": "",
                "orientation": "h",
            }
        ],
        "layout": {
                    "height":800,
                    "width":400, 
                    "margin": dict(t=20, b=20, l=100, r=20, pad=4),
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "xaxis": dict(
                                 showline=False, showgrid=False, zeroline=False,
                                 tickfont=dict(color="#f4e9dc"),side="top"
                             ),
                    "yaxis": dict(
                                 showline=False, showgrid=False, zeroline=False,
                                 tickfont=dict(color="#f4e9dc")
                             ),
                    "autosize":False,
                    "colorway": ["#494949"],
                    "template":"plotly_dark",
        },
    }
    treemap_trace = go.Treemap(
        labels=word_list_top, parents=[""] * len(word_list_top), values=freq_list_top
    )
    treemap_layout = go.Layout({"margin": dict(t=10, b=10, l=5, r=5, pad=4)})
    treemap_figure = {"data": [treemap_trace], "layout": treemap_layout}
    
    return frequency_figure_data, treemap_figure

# build the ranking bar of the top 50 terms on the right side
def build_top_panel(corpus_name):

    corpus_ind_dir=corpus[corpus_name]
    doc_num_year=preprocess_corpus.get_num_doc_year(corpus_ind_dir)
    top_terms = preprocess_corpus.top_terms(corpus_ind_dir,50)
    bar_graph, treemap = plotly_wordcloud(top_terms)
    doc_len_dict = preprocess_corpus.get_doc_len_freq(corpus_ind_dir)
    searchable_fileds = preprocess_corpus.get_fieldnames(corpus_ind_dir)

    x=[]
    y=[]
    x_len=[]
    y_len=[]
    total=0
    len_total=0

    for year in sorted (doc_num_year.keys()):
        x.append(year)
        y.append(doc_num_year[year])
        total+=int(doc_num_year[year])

    min_len=sorted(doc_len_dict.keys())[0]
    max_len=sorted(doc_len_dict.keys())[-1]
    for length in range(min_len-1,max_len+1):
        x_len.append(length)
        if length in doc_len_dict:
            y_len.append(doc_len_dict[length])
            len_total+=doc_len_dict[length]*length
        else:
            y_len.append(0)
        

    ave_len=round(len_total/sum(y_len))

    plotdata={
            "x":x,
            "y":y,
            "mode": "lines",
            "line": {                
                "width": 3,
                "shape":"spline",
            },
            "text": x,

        }
    graph_line=dcc.Graph(
                id="doc-num-year",
                figure=go.Figure(
                    {
                        "data": plotdata,
                        "layout": {
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "plot_bgcolor": "rgba(0,0,0,0)",
                            "xaxis": dict(
                                showline=False, showgrid=False, zeroline=False,color="rgba(0,0,0,0)"
                            ),
                            "yaxis": dict(
                                showgrid=False, showline=False, zeroline=False,color="rgba(0,0,0,0)"
                            ),
                            "autosize":False,
                            "colorway": ["rgba(244,233,220,0.7)"],
                            "width":400,
                            "height":140,
                            "margin":dict(l=1,r=1,b=30,t=5,pad=0)
                        },
                    }
                )
            )


    graph_bar_data= {
        "data": [
            {
                "y": y_len,
                "x": x_len,
                "type": "lines",
                "name": "",
                "line": {                
                    "width": 2,
                },
                "text":x_len
                
            }
        ],
        "layout": {
                    "height": "180",
                    "width":"400", 
                    "margin":dict(l=1,r=1,b=30,t=5,pad=0),
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "xaxis": dict(
                                 showline=False, showgrid=False, zeroline=False,
                                 tickfont=dict(color="#f4e9dc"),showticklabels=False
                             ),
                    "yaxis": dict(
                                 showline=False, showgrid=False, zeroline=False,
                                 tickfont=dict(color="#f4e9dc")
                             ),
                    "autosize":False,
                    "colorway": ["rgba(244,233,220,0.7)"],
                    "template":"plotly_dark",

        }
    }

    return html.Div(
        id="top-section-container",
        className="row",
        children=[
            # Metrics summary
            html.Div(
                id="metric-summary-session",
                className="side-by-side",
                children=[
                    html.Div(className="front-pad",children=[
                            html.Div(corpus_name,className="title"),
                            html.Div(className="pad",children=[
                                    html.Div(className="title-number",children=[
                                        html.Div(className="title-number-label",children=[html.Div("ABOUT THIS CORPUS")]),
                                        html.Div(className="side-by-side", style={"margin-top":"2px"},
                                            children=[html.Div(style={"margin-top": "10pt","margin-right": "10pt","color":"#f4e9dc"},children="TIME RANGE"),
                                                      html.Div(className="title-number-dis",children=str(min(x))+" - "+str(max(x)))
                                            ]),
                                        
                                        html.Div(className="side-by-side",
                                            children=[html.Div(style={"margin-top": "10pt","margin-right": "4pt","color":"#f4e9dc"},children="NUMBER OF DOCUMENTS"),
                                                      html.Div(className="title-number-dis",children=str(total))
                                            ]),
                                                         
                                    ]),
                                    html.Div(style={"margin-left":"40%","position":"absolute","bottom":"0%"},
                                            children=[graph_line])
                                ]),
                            html.Br(),
                            
                            html.Div(className="pad2",children=[
                                    html.Div(className="title-number",children=[
                                        html.Div(className="title-number-label",children=[html.Div("DOCUMENT LENGTH (words)")]),
                                        html.Div(className="side-by-side",
                                            children=[html.Div(style={"margin-top": "10pt","margin-right": "6pt","color":"#f4e9dc"},children="AVG"),
                                                      html.Div(className="title-number-dis",children=str(ave_len))]),
                                        html.Div(className="side-by-side",
                                            children=[html.Div(style={"margin-top": "10pt","margin-right": "5pt","color":"#f4e9dc"},children="MIN"),
                                                      html.Div(className="title-number-dis",children=str(min_len))]),
                                        html.Div(className="side-by-side",
                                            children=[html.Div(style={"margin-top": "10pt","margin-right": "3pt","color":"#f4e9dc"},children="MAX"),
                                                      html.Div(className="title-number-dis",children=str(max_len))]),
                                                         
                                    ]),
                                    html.Div(style={"margin-left":"40%","position":"absolute","bottom":"0%"},
                                            children=[dcc.Graph(id="doc-len-figure",figure=graph_bar_data)])
                                ]),
                            html.Br(),
                            html.Div(className="pad3",children=[
                                    html.Div(className="side-by-side",children=[
                                        html.Div(style={"border-bottom": "1px solid","font-size":"15pt",
                                                    "margin-left":"37px","margin-top":"5pt", "color":"#f4e9dc"}, children="TOP 20"),
                                        dcc.Dropdown(
                                        id="search-top-dropdown",
                                        options=list(
                                            {"label": param, "value": param} for param in searchable_fileds
                                        )
                                        )]),
                                    html.Div(className="side-by-side",style={"max-height":"70%"},children=[
                                        html.Div(id="search-top-result",className="pad3-result",children=""),
                                        html.Div(style={"margin-top":"-3%"},id="search-top-graph")
                                    ])
                                    
                                ]),
                        ]),
                    html.Div(children=[
                            html.Div("Top 30 Words",style={"color": "#f4e9dc","margin-top": "10px",
                                                           "margin-left": "5px","font-size": "20pt",
                                                           "font-variant": "all-small-caps"}),
                            dcc.Loading(id="word-frequencies",type="default",
                                    children=[html.Div(dcc.Graph(id="frequency-figure",figure=bar_graph,style={"height":"80vh"}),style={"max-height":"90%","overflow-y":"scroll"},id="top-30-graph")],     
                            )
                    ])
                    
                ],
            ),
        ],
    )


# the bottom panel in "overview" tab
# search top items for the given field 

@app.callback([Output("search-top-result","children"),Output("search-top-graph","children")],
                [Input("search-top-dropdown","value"),
                Input("corpus-select-dropdown","value")])
def search_top(field_name, corpus_name):
    
    if field_name:
        corpus_ind_dir=corpus[corpus_name]


        top_t = preprocess_corpus.field_top_terms(corpus_ind_dir, field_name)

        frequency_figure_data = {
            "data": [
                {
                    "y": [top_t[k] for k in top_t],
                    "x": list(top_t.keys()),
                    "type": "bar",
                    "name": "",
                    "text": list(top_t.keys()),
                    
                }
            ],
            "layout": {
                        "height": "180",
                        "width":"420", 
                        "margin": dict(t=0, b=30, l=30, r=0, pad=0),
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)",
                        "xaxis": dict(
                                     showline=False, showgrid=False, zeroline=False,
                                     tickfont=dict(color="#f4e9dc"),showticklabels=False
                                 ),
                        "yaxis": dict(
                                     showline=False, showgrid=False, zeroline=False,
                                     tickfont=dict(color="#f4e9dc"),showticklabels=False
                                 ),
                        "autosize":False,
                        "colorway": ["rgba(244,233,220,0.7)"],
                        "template":"plotly_dark",
            },
        }

        return [", ".join(list(top_t.keys())),dcc.Graph(figure=frequency_figure_data)]
    else:
        return ["Please Select a Field.",[]]


# --- index ---

def loading_layout():
    return [
                dcc.Markdown('''## **C**onTEXT **E**xplorer''', style={"border-bottom": "2px solid #494949",
                                                                        "margin-top":"10%"}),
                html.Div(
                    id="corpus-select-menu",
                    className='side-by-side',
                    children=[html.Div(id="index-choose_corpus",className="index-dropdown",children=[
                        html.Label(id="corpus-select-title", children="Use an existing corpus"),
                        dcc.Dropdown(
                            id="corpus-select-dropdown",
                            options=list(
                                {"label": param, "value": param} for param in corpus
                            )
                        )]
                        )
                    ],
                ),html.Br(),
                html.Button("Upload a new corpus", id="upload-btn",n_clicks=0,className="upload-btn"), html.Br(),  
                html.Button("Delete an existing corpus", id="delete-btn",n_clicks=0,className="upload-btn"), 
            ]

app.layout = html.Div(
    id="big-app-container",
    className="big-app",
    children=[
        
        dcc.Store(id="corpus_now",data=corpus),
        html.Div(
            id="app-loading",
            children=loading_layout(),
        ),          
    ]
)

#load corpus

@app.callback(Output("corpus-select-dropdown", "options"),
    [Input("corpus_now", "data")],[State("corpus-select-dropdown","options")])
def update_corpus(data,options):
    
    global corpus
    corpus = pd.read_pickle("./corpus_save").to_dict()
    if (len(corpus)>0): #not empty
        corpus = corpus[0]
    options = list({"label": param, "value": param} for param in corpus)
    return options


@app.callback(
    [Output("app-content", "children")],
    [Input("app-tabs", "value")],
    [State("corpus_name_store", "data")],
)
def render_tab_content(tab_switch, corpus_name):
    if tab_switch == "tab1":
        return [build_tab_1(corpus_name)] 
    if tab_switch == "tab22":
        return [build_tab_group()]
    if tab_switch == "tab3":
        return [build_tab_3()]
    return (
        html.Div(
            id="status-container",
            children=[
                html.Div(
                    id="graphs-container",
                    style={"width":"100%"},
                    children=[build_top_panel(corpus_name)],
                ),
            ],
        ),

    )


# --- delete corpus ---

@app.callback(Output("app-loading","children"),
            [Input("corpus-select-dropdown","value"),Input("upload-btn","n_clicks"),Input("delete-btn","n_clicks")],
            [State("app-loading","children")])
def show_next(corpus_name,upload_click,delete_click,children):
    if delete_click>0:
        return [html.Div(style={"display":"flex"},children=[
                html.Div("##",className="upload-number"),
                dcc.Markdown('''## **D**elete A **C**orpus''', style={"border-bottom": "4px solid #494949",
                                                                    "width":"600px","margin-top":"20px"}),
                ]),
                html.Div(id="delete-display",style={"margin-left": "110px","margin-top": "30px"},children=[
                    html.Label(id="corpus-select-title", children="Use an existing corpus"),
                        #html.Br(),
                    dcc.Dropdown(id="delete-corpus-select-dropdown",
                                options=list({"label": param, "value": param} for param in corpus)
                        ),
                    dcc.ConfirmDialogProvider(children=
                        html.Button("Delete Corpus",style={"margin-left":"0px"},className="submit-btn"),
                        id="confirm-delete",
                        message='Are you sure you want to delete this corpus?'
                    )
                ])
        ]
    if upload_click>0:       
        return [html.Div(style={"display":"flex"},children=[
                html.Div("01",className="upload-number"),
                dcc.Markdown('''## **U**pload **Y**our **D**ata''', style={"border-bottom": "4px solid #494949",
                                                                    "width":"600px","margin-top":"20px"}),
                ]),
                dcc.Loading(
                id="loading-1",
                type="default",color="#e85e56",
                children=html.Div(id='output-data-upload',children=[
                html.Div(html.P(["Please upload your data as a .csv file with column headers. The headers can be any text; you will be asked about them in the next step.",html.Br(),html.Br(), 
                "Your file needs to include:",html.Br(),
                html.Li("a text column with the content of documents you want to analyse"), 
                html.Li("a column with a unique identifier for each document (if your file does not include IDs column, they will be assigned based on row numbers)"), 
                html.Li("and publication year for each of the documents."),
                html.Br(),"You can also upload additional columns with the document information you want to explore."
                ]),
                className="upload-des"),
                du.Upload(id='upload-data',
                            max_file_size=1800,
                            filetypes=['csv'],
                            upload_id=uuid.uuid1(),  # Unique session id
                            cancel_button=False,
                            default_style={
                                'width': '500px',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin-top': '30px',
                                'margin-left':'110px'
                            },
                        ),
                        ]))
                    ]
    if corpus_name:
        saves_path=corpus[corpus_name]+"groups/"
        savefiles = [f for f in listdir(saves_path) if isfile(join(saves_path, f))]

        saves=["create new"]
        for f in savefiles:
            saves.append("[ "+f+" ]")

        if len(children[1]['props']['children'])>1: #if some corpus is selected before, delete its children
            del children[1]['props']['children'][-1]
            del children[1]['props']['children'][-1]

        children[1]['props']['children'].append(
            html.Div(id="index-choose-save",className="index-dropdown",children=[html.Label(id="save-select-title", children="Saved Analysis"),
                           dcc.Dropdown(id="save-select-dropdown",
                            options=list(
                                {"label": param, "value": param} for param in saves
                            ),value="create new",clearable=False)])
        )
        children[1]['props']['children'].append(html.Button("Start",id="start-exp",n_clicks=0))                                         
                                 
        return children
    else:
        return children[0:6]

@app.callback(Output("delete-display","children"),
              [Input("confirm-delete","submit_n_clicks")],
              [State("delete-corpus-select-dropdown","value"),State("delete-display","children")])
def delete_corpus(delete_click,corpus_del,children):
    if delete_click:
        c = corpus[corpus_del]
        del corpus[corpus_del]
        pd.DataFrame.from_dict(corpus, orient='index').to_pickle("./corpus_save")
        preprocess_corpus.delete_corpus_from_app(c)        
        preprocess_corpus.delete_corpus_from_app("./topic_model/"+str(corpus_del)+"/")
        
        return [html.Div("Your corpus has been deleted. Please refresh to return to the main page.",className="upload-des"),
            ]
    else:
        return children


# --- start main page for the selected corpus ---

@app.callback(Output("big-app-container","children"),
              [Input("start-exp","n_clicks")],
              [State("big-app-container","children"),State("index-choose_corpus","children"),
              State("index-choose-save","children")])

def start(n_clicks,children,select,analysis):
    if n_clicks>0:
        corpus_name = select[1]['props']['value']
        chosen_analysis = analysis[1]['props']['value']
        select[1]['props']['disabled']="True"
        analysis[1]['props']['disabled']="True"

        loaded = load_analysis(corpus_name,chosen_analysis)

        return [build_banner(select[1], analysis[1],loaded),
                html.Div(id="app-container",
                        children=[
                            build_tabs(),
                            # Main app
                            html.Div(id="app-content"),
                        ],
                ),
                dcc.Interval(
                    id="interval-component",
                    interval=2 * 1000,  # in milliseconds
                    n_intervals=50,  # start at batch 50
                    disabled=True,
                ),
                dcc.Store(id="n-interval-stage", data=50),
                dcc.Store(id="group-stored-data",data=loaded["groups"]),
                dcc.Store(id="word-card-data"),
                dcc.Store(id="corpus_name_store",data=corpus_name)
            ]
    else:
        return children


# --- upload corpus ---

# step 1, parse uploaded csv
def parse_contents(contents, filename):
    try:
        if 'csv' in filename: 
            df = pd.read_csv(contents,engine='python')
        else:
            return html.Div([
                'The file has to be .csv'
            ])

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file: '+str(e)
        ])
    column_names = list(df.columns)

    return html.Div([
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i, 'deletable': True} for i in df.columns],
            style_header={"fontWeight": "bold", "color": "#e85e56","borderRight":"none"},
            page_size=5,
            style_table={"margin-left":"100px","margin-top":"2%","margin-right":"50px","width":"85%"},
            style_cell={
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0,
                "backgroundColor": "#f4e9dc",
                "color":"#494949",
                "borderBottom":"none",
                "borderLeft":"none",
                "borderTop":"none",
                "borderRight":"1px solid #1E1C24",
                "padding-left":"3px"

            },
            css=[   {"selector": "tr:hover td", "rule": "color: #e85e56 !important;"},
                    {"selector": ".dash-cell.focused",
                                "rule": "background-color: #f4e9dc !important; border:none;"},
                    {"selector": ".dash-spreadsheet-container table", 
                                "rule": '--text-color: #91dfd2 !important'},
                    {"selector": "table", "rule": "--accent: #e85e56;"},
                    {"selector": "tr", "rule": "background-color: transparent"},
                    {"selector": ".column-header--sort","rule":"color: #e85e56; padding-right:3px;"}
                ]
        ),
        html.Div(className="upload-select",children=[
            html.Div(style={"display":"flex"},children=[
                html.Div("02",className="upload-number"),
                dcc.Markdown('''## **C**hoose The **C**olumns''', style={"border-bottom": "4px solid #494949",
                                                                    "width":"600px","margin-top":"20px"}),
                ]),
            html.Div(html.P(["Choose the columns for your corpus:",html.Br(),
                        html.Li(" ID – unique identifier for each document. If your file does not include IDs, select 'use row number'."),
                        html.Li(" Year – publication year of each document (use numeric format, e.g. '2020')"),
                        html.Li(" Sentences – document text (use text format; documents will be converted to sentences automatically). "),
                        # html.Li(" Title – the title of the documents to be analysed"),
                        # html.Li(" Author – the author of the documents to be analysed"),
                        html.Br(),
                        html.P(style={"font-size":"10pt"},children=["* Your file has to include 'Year' and 'Sentences' columns in a required format for the corpus to be uploaded.",
                        html.Br(),html.Br(),"You can upload documents titles, authors, and more info by clicking on the 'add field' button below."])
                        ]),
                className="upload-des"),

                
            html.Div(style={"display":"flex","margin-left":"55px"},children=[
                #html.Div(className="upload-select-col"),
                html.Div(className="upload-select-col",children=[
                    html.Label(children="ID"),
                    dcc.Dropdown(id="select-id-dropdown",
                             options=list({"label": param, "value": param} for param in ["use row number"]+column_names
                                    ),value="use row number",clearable=False)]),
                html.Div(className="upload-select-col",children=[
                    html.Label(children="Year*"),
                    dcc.Dropdown(id="select-year-dropdown",
                             options=list({"label": param, "value": param} for param in column_names
                                    ),value=column_names[0],clearable=False)]),
                html.Div(className="upload-select-col",children=[
                    html.Label(children="Sentences*"),
                    dcc.Dropdown(id="select-content-dropdown",
                             options=list({"label": param, "value": param} for param in column_names
                                    ),value=column_names[0],clearable=False)]),
                
                ]
            ),
            html.Div(id="cus-add-columns",style={"display":"flex","flex-wrap":"wrap","width":"70%","margin-left":"55px"},children=[
                dcc.Store(id="full_columns",data=column_names),
                #html.Div(className="upload-select-col"),
                html.Div(className="upload-select-col",children=[
                    html.Label(children="Title"),
                    dcc.Dropdown(id="select-title-dropdown",
                             options=list({"label": param, "value": param} for param in column_names
                                    ),value=column_names[0],clearable=False)]),
                html.Div(className="upload-select-col",children=[
                    html.Label(children="Author"),
                    dcc.Dropdown(id="select-author-dropdown",
                             options=list({"label": param, "value": param} for param in column_names
                                    ),value=column_names[0],clearable=False)]),
            ]),
            html.Button("Add Field",id="add-column",n_clicks=0,style={"margin-left": "130px","margin-top": "50px"})
            ]),
        html.Div(className="upload-select2",children=[
            html.Div(style={"display":"flex"},children=[
                html.Div("03",className="upload-number"),
                dcc.Markdown('''## **U**pload **Y**our **C**orpus''', style={"border-bottom": "4px solid #494949",
                                                                    "width":"600px","margin-top":"20px"}),]),
            html.Div(html.P(["Please name your corpus. You can use any combination of letters and numbers connected by an underscore e.g., “ConTEXT_explorer_123”",html.Br(),html.Br(),
                "Please be patient. It will take a few minutes."]),className="upload-des"),

            html.Div(style={"display":"flex","margin-top":"1%","margin-bottom":"5%"},children=[
                html.Div(className="upload-select-col0",children=[
                    html.Label(children="Corpus Name*",style={"margin-left": "-5%","margin-bottom":"3px"}),
                    dcc.Input(id="uploaded-corpus-name", className="new-corpus-input", type="text",
                                            value=filename.replace(".csv","").strip())]),
                html.Button("Upload Corpus",id="submit-corpus",n_clicks=0,className="submit-btn"),
                dcc.Store(id="upload-dataframe",data=df.to_dict('records')),
                ]),
                
            ]),dcc.Loading(
                    id="loading-2",
                    children=html.Div(id="loading-output-2"),
                    type="circle",fullscreen=True,color="#e85e56"
                    )
    ])

# step 2, add columns
@app.callback(Output('cus-add-columns', 'children'),
                [Input("add-column","n_clicks")],
                [State("full_columns","data"),State("cus-add-columns","children")])
def add_new_column(n_clicks, columns, children):
    if n_clicks>0:
        if len(children)<=len(columns):
            children.append(html.Div(className="upload-select-col",children=[
                            html.Label(children="Add "+str(len(children)-2)),
                            dcc.Dropdown(id={'type':'add_column', 'index':len(children)-2},
                             options=list({"label": param, "value": param} for param in columns
                                    ),value=columns[0],clearable=False)]))
        return children
    else:
        return children    


# step 3, uploading
@app.callback([Output('loading-output-2', 'children'),Output('corpus_now', 'data')],
                [Input("submit-corpus","n_clicks")],
                [State("upload-dataframe","data"), State("select-id-dropdown","value"),
                State("select-year-dropdown","value"),State("select-content-dropdown","value"),
                State("select-author-dropdown","value"),State("select-title-dropdown","value"),
                State({'type':'add_column', 'index':ALL},"value"),
                State("uploaded-corpus-name","value"),State("corpus_now","data")
                ])
def uploading(n_clicks, df,id_col, year_col,content_col,author_col,title_col,add_cols,corpus_name,data):
    if n_clicks>0:
        if not re.match(r'^\w+$', corpus_name):
            return [dcc.ConfirmDialog(
                    id='confirm',
                    message='Invalid corpus name. Please choose another one.',
                    displayed= True
                    ), data]

        if corpus_name in data:#corpus name exists
            return [dcc.ConfirmDialog(
                    id='confirm',
                    message='The corpus name has been taken. Please choose another one.',
                    displayed= True
                    ), data]
        else:
            get = preprocess_corpus.add_new_corpus_from_app(corpus_name+"_index/",df,id_col,content_col,title_col,
                                      year_col,author_col,add_cols)
            get2 = generate_models_fromapp.build_model(df,corpus_name,content_col)
            get3 = word2vec.train_model(corpus_name)
            
            if (get & get2 & get3):
                data[corpus_name]="./whoosh_search/"+corpus_name+"_index/"
                pd.DataFrame.from_dict(data, orient='index').to_pickle("./corpus_save")

                return [dcc.ConfirmDialog(
                        id='confirm',
                        message='The corpus has been uploaded. Please refresh to go back to the main page.',
                        displayed= True
                        ), data]
            else:
                return [dcc.ConfirmDialog(
                        id='confirm',
                        message='Failed.',
                        displayed= True
                        ),data]
    else:
        return [html.Div(),data]


# uploading output
@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'isCompleted')],
              [State('upload-data', 'fileNames'), State('upload-data',"upload_id"),
              State('output-data-upload', 'children')])
def update_output(iscompleted,filenames, upload_id, upload):
    if not iscompleted:
        return upload
    if filenames is not None:
        if upload_id:
           
            root_folder = UPLOAD_FOLDER_ROOT+"/"+upload_id
        else:
            root_folder = UPLOAD_FOLDER_ROOT

        for filename in filenames:
            file = root_folder+"/"+filename
            children = [parse_contents(file,filename)]
            return children
    else:
        return upload


# Running the server
if __name__ == "__main__":
    #app.run_server(debug=False,host="0.0.0.0") # ubuntu server
    app.run_server(debug=False, port="8010") # local test
