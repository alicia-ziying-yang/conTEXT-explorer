from dash.testing.application_runners import import_app
import time

# This first test case will test the main functionality of the app.
# It will use the pre-install sample corpus.
def test_main(dash_duo):
	app = import_app("app")
	dash_duo.start_server(app)
	dash_duo.wait_for_text_to_equal("#corpus-select-title", "Use an existing corpus", timeout=4)
	
	#---test to choose the pre-installed sample data---
	# choose corpus "sample_data"
	corpus = dash_duo.driver.find_element_by_id('index-choose_corpus')
	dash_duo.multiple_click(corpus, 1)
	opt = dash_duo.driver.find_element_by_id('react-select-2--list')
	dash_duo.multiple_click(opt, 1)
	dash_duo.wait_for_text_to_equal("#react-select-2--value-item", "sample_data", timeout=3)

	# choose to create a new analysis
	saved_analysis = dash_duo.driver.find_element_by_id('index-choose-save')
	dash_duo.wait_for_text_to_equal("#react-select-3--value-item", "create new", timeout=3)

	#---start---
	start = dash_duo.driver.find_element_by_id("start-exp")
	dash_duo.multiple_click(start, 1)

	# leave some time to load
	time.sleep(2)

	#---test year range---
	year_from = dash_duo.find_element("#year-from > Div > span > input")
	year_to = dash_duo.find_element("#year-to > Div > span > input")
	# default values
	assert '2012' == year_from.get_attribute('value')
	assert '2018' == year_to.get_attribute('value')

	# test to change value
	dash_duo.clear_input(year_from)
	year_from.send_keys('2013')
	assert '2013' == year_from.get_attribute('value')

	
	#---test to type base term---
	base_term = dash_duo.driver.find_element_by_id("base-term")
	base_term.send_keys('marriage')
	time.sleep(1)
	assert 'marriage' == base_term.get_attribute('value')


	#---test "Add Related Words"---
	
	# The word2vec in the app should find a list of 
	# related words for the base term.
	# In our test example, it should be the word "sex".
	first_candidate = dash_duo.find_element("#candidates > div > div > label")
	assert "sex" == first_candidate.text
	dash_duo.multiple_click(first_candidate, 1)

	# add it to the query
	add_single = dash_duo.driver.find_element_by_id("add-single")
	dash_duo.multiple_click(add_single, 1)

	# delete it from the quey
	added = dash_duo.find_element("#added-terms-fromside > div > div > label")
	assert "sex" == added.text

	dash_duo.multiple_click(added, 1)

	# mannually add
	manu_add = dash_duo.driver.find_element_by_id("manu-add")
	manu_input = dash_duo.driver.find_element_by_id("manu-term")
	manu_input.send_keys('equality') # single term
	dash_duo.multiple_click(manu_add, 1)
	dash_duo.clear_input(manu_input)
	manu_input.send_keys('same sex') # phrase
	dash_duo.multiple_click(manu_add, 1)


	#---test "Sentence" tab---
	sent_tab = dash_duo.driver.find_element_by_id("Specs-tab")
	dash_duo.multiple_click(sent_tab, 1)
	time.sleep(1)

	# check the query for the ranking
	current_query = dash_duo.driver.find_element_by_id("current_query")
	assert "equality | same sex | marriage" == current_query.text

	# check the number of relevant sentences (i.e. the length of the ranking table)
	assert "107" == dash_duo.find_element("#rel_sent > div > div > div").text

	# open the pop up of the first result in the ranking table
	r1 = dash_duo.find_element("tr > td")
	dash_duo.multiple_click(r1, 1)

	# choose the term "couples", check term frequency, and add to the query
	term = dash_duo.find_element("#pop-up-sent div:nth-child(19) > div > label")
	dash_duo.multiple_click(term, 1)
	dash_duo.multiple_click(dash_duo.driver.find_element_by_id("check_sf"), 1)
	dash_duo.multiple_click(dash_duo.driver.find_element_by_id("add-to-query"), 1)

	# close the pop
	clost_btn = dash_duo.driver.find_element_by_id("markdown_close")
	dash_duo.multiple_click(clost_btn, 1)
	time.sleep(1)

	# current query should update
	current_query = dash_duo.driver.find_element_by_id("current_query")
	assert "equality | same sex | couples | marriage" == current_query.text

	# check the ranking has been updated
	assert "112" == dash_duo.find_element("#rel_sent > div > div > div").text


	#---test "Grouping" tab---
	group_tab = dash_duo.driver.find_element_by_id("Group-tab")
	dash_duo.multiple_click(group_tab, 1)
	time.sleep(1)

	# make a group
	group0_name = dash_duo.find_element("#make-groups > div > input")
	dash_duo.clear_input(group0_name)
	group0_name.send_keys('test group') # rename the group
	time.sleep(1)
	assert "test group" == dash_duo.find_element("#make-groups > div > input").get_attribute('value')

	# choose terms for the group
	# add "marriage"
	dropdown = dash_duo.find_element("#make-groups > div > div")
	dash_duo.multiple_click(dropdown, 1)
	t1 = dash_duo.find_element('#make-groups > div > div > div div:nth-child(1) > div > div > div > div:nth-child(1)')
	dash_duo.multiple_click(t1, 1)
	# add "equality"
	dash_duo.multiple_click(dropdown, 1)
	t2 = dash_duo.find_element('#make-groups > div > div > div div:nth-child(1) > div > div > div > div:nth-child(1)')
	dash_duo.multiple_click(t2, 1)

	# create a new group
	add_group_btn = dash_duo.driver.find_element_by_id("add_group")
	dash_duo.multiple_click(add_group_btn, 1)
	
	# add "same sex"
	dropdown = dash_duo.find_element("#make-groups > div:nth-child(2) > div")
	dash_duo.multiple_click(dropdown, 1)
	t3 = dash_duo.find_element('#make-groups > div:nth-child(2) > div > div div:nth-child(1) > div > div > div > div:nth-child(3)')
	dash_duo.multiple_click(t3, 1)


	# compound group
	comp_group_btn = dash_duo.driver.find_element_by_id("comp_group")
	dash_duo.multiple_click(comp_group_btn, 1)

	# include two groups into one
	dropdown = dash_duo.find_element("#make-groups > div:nth-child(3) > div")
	dash_duo.multiple_click(dropdown, 1)
	g1 = dash_duo.find_element('#make-groups > div:nth-child(3) > div > div div:nth-child(1) > div > div > div > div:nth-child(1)')
	dash_duo.multiple_click(g1, 1)
	dash_duo.multiple_click(dropdown, 1)
	g2 = dash_duo.find_element('#make-groups > div:nth-child(3) > div > div div:nth-child(1) > div > div > div > div:nth-child(1)')
	dash_duo.multiple_click(g2, 1)

	# test toggle of "ANY or ALL", set to "ANY"
	toggle = dash_duo.find_element("#make-groups > div:nth-child(3) div:nth-child(3) > div > div > div:nth-child(2)")
	dash_duo.multiple_click(toggle, 1)

	# delete group
	add_group_btn = dash_duo.driver.find_element_by_id("add_group") #add a new group
	dash_duo.multiple_click(add_group_btn, 1)
	delete_btn = dash_duo.find_element("#make-groups > div:nth-child(4) div:nth-child(4) > button")
	dash_duo.multiple_click(delete_btn, 1) #delete
	
	#---test "Graph" tab---
	graph_tab = dash_duo.driver.find_element_by_id("Graph-tab")
	dash_duo.multiple_click(graph_tab, 1)
	time.sleep(1)
	
	dropdown = dash_duo.find_element("#count_prop-dropdown > div > div")
	dash_duo.multiple_click(dropdown, 1)

	# choose to show the proportion
	prop_opt = dash_duo.find_element('#count_prop-dropdown > div > div:nth-child(2) > div > div > div > div > div:nth-child(3)')
	dash_duo.multiple_click(prop_opt, 1)
	time.sleep(2)
	

	#---test saving---
	save_btn = dash_duo.driver.find_element_by_id("save-analysis") #add a new group
	dash_duo.multiple_click(save_btn, 1)
	
	save_name = dash_duo.driver.find_element_by_id("save-name")
	save_name.send_keys('test save')
	time.sleep(1)
	assert 'test save' == save_name.get_attribute('value')

	save_btn = dash_duo.driver.find_element_by_id("save-add")
	dash_duo.multiple_click(save_btn, 1)

	
# This second test case will test if the analysis saved in previous test case can be reloaded.
def test_reload(dash_duo):
	app = import_app("app")
	dash_duo.start_server(app)
	dash_duo.wait_for_text_to_equal("#corpus-select-title", "Use an existing corpus", timeout=4)
	
	#---test to choose the pre-installed sample data---
	# choose corpus "sample_data"
	corpus = dash_duo.driver.find_element_by_id('index-choose_corpus')
	dash_duo.multiple_click(corpus, 1)
	opt = dash_duo.driver.find_element_by_id('react-select-2--list')
	dash_duo.multiple_click(opt, 1)
	dash_duo.wait_for_text_to_equal("#react-select-2--value-item", "sample_data", timeout=3)

	# choose the analysis saved in previous test case
	analysis_dropdown = dash_duo.find_element('#save-select-dropdown')
	dash_duo.multiple_click(analysis_dropdown, 1)
	pre_saved = dash_duo.find_element('#save-select-dropdown > div > div:nth-child(2) > div > div > div > div > div:nth-child(2)')
	dash_duo.multiple_click(pre_saved, 1)

	# its name should be "test save"
	saved_analysis = dash_duo.driver.find_element_by_id('index-choose-save')
	dash_duo.wait_for_text_to_equal("#react-select-3--value-item", "[ test save ]", timeout=3)

	#start
	start = dash_duo.driver.find_element_by_id("start-exp")
	dash_duo.multiple_click(start, 1)

	time.sleep(1)

	# test year range
	year_from = dash_duo.find_element("#year-from > Div > span > input")
	year_to = dash_duo.find_element("#year-to > Div > span > input")
	assert '2013' == year_from.get_attribute('value')
	assert '2018' == year_to.get_attribute('value')

	#test base term
	base_term = dash_duo.driver.find_element_by_id("base-term")
	assert 'marriage' == base_term.get_attribute('value')

	#test if query terms are saved
	sent_tab = dash_duo.driver.find_element_by_id("Specs-tab")
	dash_duo.multiple_click(sent_tab, 1)
	time.sleep(1)
	current_query = dash_duo.driver.find_element_by_id("current_query")
	assert "equality | same sex | couples | marriage" == current_query.text

 	#test if groups are saved (here just test the first one)
	group_tab = dash_duo.driver.find_element_by_id("Group-tab")
	dash_duo.multiple_click(group_tab, 1)
	time.sleep(1)
	assert "test group" == dash_duo.find_element("#make-groups > div > input").get_attribute('value')


#This test case will test the data (corpus) uploading.
def test_upload(dash_duo):
	app = import_app("app")
	dash_duo.start_server(app)
	dash_duo.wait_for_text_to_equal("#corpus-select-title", "Use an existing corpus", timeout=4)
	
	upload_btn = dash_duo.driver.find_element_by_id("upload-btn")
	dash_duo.multiple_click(upload_btn, 1)

	uploader = dash_duo.find_element("[name='upload-data-upload']")
	
	import os
	cwd = os.getcwd()
	uploader.send_keys(cwd+"/doc/sample_data.csv")
	
	time.sleep(2)

	#choose year column
	dropdown = dash_duo.find_element("#select-year-dropdown > div > div")
	dash_duo.multiple_click(dropdown, 1)
	
	opt = dash_duo.find_element('#select-year-dropdown > div > div:nth-child(2) > div > div > div > div > div:nth-child(2)')
	dash_duo.multiple_click(opt, 1)
	
	#choose content column
	dropdown = dash_duo.find_element("#select-content-dropdown > div > div")
	dash_duo.multiple_click(dropdown, 1)
	
	opt = dash_duo.find_element('#select-content-dropdown > div > div:nth-child(2) > div > div > div > div > div:nth-child(7)')
	dash_duo.multiple_click(opt, 1)

	corpus_name = dash_duo.driver.find_element_by_id("uploaded-corpus-name")
	corpus_name.send_keys('_test_upload')
	time.sleep(1)
	assert 'sample_data_test_upload' == corpus_name.get_attribute('value')

	submit_btn = dash_duo.driver.find_element_by_id("submit-corpus")
	dash_duo.multiple_click(submit_btn, 1)

	time.sleep(10)

# cotinue, check if the uploading succeeded
def test_upload_following(dash_duo):
	app = import_app("app")
	dash_duo.start_server(app)
	dash_duo.wait_for_text_to_equal("#corpus-select-title", "Use an existing corpus", timeout=4)
	
	corpus = dash_duo.driver.find_element_by_id('index-choose_corpus')
	dash_duo.multiple_click(corpus, 1)
	opt = dash_duo.find_element('#index-choose_corpus > div > div > div:nth-child(2) > div > div > div > div > div:nth-child(2)')
	dash_duo.multiple_click(opt, 1)
	dash_duo.wait_for_text_to_equal("#react-select-2--value-item", "sample_data_test_upload", timeout=3)

# This test case will test the data (corpus) deleting.
def test_delete(dash_duo):
	app = import_app("app")
	dash_duo.start_server(app)
	dash_duo.wait_for_text_to_equal("#corpus-select-title", "Use an existing corpus", timeout=4)
	
	delete_btn = dash_duo.driver.find_element_by_id("delete-btn")
	dash_duo.multiple_click(delete_btn, 1)

	corpus = dash_duo.driver.find_element_by_id('delete-corpus-select-dropdown')
	dash_duo.multiple_click(corpus, 1)
	opt = dash_duo.find_element('#delete-corpus-select-dropdown > div > div:nth-child(2) > div > div > div > div > div:nth-child(2)')
	dash_duo.multiple_click(opt, 1)
	delete_btn = dash_duo.find_element("#confirm-delete > button")
	dash_duo.multiple_click(delete_btn, 1)
