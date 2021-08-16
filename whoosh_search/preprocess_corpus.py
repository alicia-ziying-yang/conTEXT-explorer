
import io
import sys
import os
import shutil
from backports import csv

from whoosh import index
from whoosh import fields
from whoosh.fields import Schema, ID, TEXT, NGRAMWORDS
from whoosh.analysis import StemmingAnalyzer
from whoosh.analysis import StandardAnalyzer
from whoosh.analysis import NgramWordAnalyzer

from whoosh.qparser import QueryParser
from whoosh.query import spans
from whoosh import query

from whoosh.reading import IndexReader
from whoosh.matching import Matcher

from spacy.lang.en import English

import re

import pandas as pd

nlp = English()
sentencizer = nlp.create_pipe("sentencizer")
nlp.add_pipe(sentencizer)


tokenizer = nlp.Defaults.create_tokenizer(nlp)
    
def get_schema():
    ana = StandardAnalyzer()
    return Schema(content=TEXT(stored = True, phrase=True, analyzer=ana), 
    			  id=ID(unique=True, stored=True),
    			  title=TEXT(stored = True, phrase=True, analyzer=ana),
    			  year=TEXT(stored=True),
    			  author=TEXT(stored=True)) #

#index all documents of a new corpus
def add_new_corpus(index_dir,corpus,id_col=-1,text_col=4,title_col=2,year_col=19): 

	doc_no_year={}
	doc_len_dict={}
	
	ix = index.create_in(index_dir, schema=get_schema())
	writer = ix.writer()

	# read relevant documents to whoosh
	with io.open(corpus, encoding='latin1') as f:
		r = csv.reader(f)
		header = next(r)
		line_no=0	
		
		for line in r:
			
			if id_col==(-1):
				articleID=str(line_no)
			else:
				articleID=str(line[id_col])

			article_text = u''+line[text_col]+''
			doc = nlp(article_text)
			sen_no = 0
			doc_len = 0

			for s in list(doc.sents):
				sent_text=str(s)
				sentID = articleID+"_"+str(sen_no)
				title = u''+line[title_col]+''
				year = u''+line[year_col]+''
				writer.add_document(content=u""+sent_text, id=u""+sentID, title=u""+title, year=u""+year)
				
				sen_no+=1

				doc_len+=len(sent_text.split())
			
			if doc_len in doc_len_dict:
				doc_len_dict[doc_len]+=1
			else:
				doc_len_dict[doc_len]=1

			if year in doc_no_year:
				doc_no_year[year]+=1
			else:
				doc_no_year[year]=1

			line_no+=1
		
	f.close()

	writer.commit()

	f2 = open(index_dir+"doc_num", "w")
	f2.write(str(line_no)+"\n")
	for year in doc_no_year:
		text=year+" "+str(doc_no_year[year])+"\n"
		f2.write(text)
	f2.close()

	f3 = open(index_dir+"doc_len", "w")
	for length in sorted(doc_len_dict):
		text=length+" "+str(doc_len_dict[length])+"\n"
		f3.write(text)
	f3.close()


	print("[ Indexing Finished. In total "+str(line_no)+" documents. ]")

def delete_corpus_from_app(index_dir):
	shutil.rmtree(index_dir)

def add_new_corpus_from_app(index_dir,corpus_dict,id_col,text_col,title_col,year_col,author_col,add_cols): 

	doc_no_year={}
	sent_no_year={}
	doc_len_dict={}
	
	path = os.path.join("./whoosh_search", index_dir)
	try:
		os.mkdir(path)
		os.mkdir(path+"groups/")
	except OSError as error:  
		return str(error)
	
	print(path + " created.")

	ix = index.create_in(path, schema=get_schema())

	for col_name in add_cols:
		ix.add_field(col_name, fields.TEXT(stored=True))

	writer = ix.writer()
	# read relevant documents to whoosh
	line_no=0
	
	for line in corpus_dict:
			
		if id_col=="use row number":
			articleID=str(line_no)
		else:
			articleID=str(line[id_col])

		article_text = u''+str(line[text_col])+''
		doc = nlp(article_text)
		sen_no = 0
		doc_len = 0

		for s in list(doc.sents):
			sent_text=str(s)
			sentID = articleID+"_"+str(sen_no)
			title = u''+str(line[title_col])+''
			year = u''+str(line[year_col])+''
			author = u''+str(line[author_col])+''
			args={"content":u""+sent_text,"id":u""+sentID,"title":u""+title,"year":u""+year,"author":u""+author}
			for col_name in add_cols:
				args[col_name]=u''+str(line[col_name])+''
			
			
			writer.add_document(**args)

			sen_no+=1

			doc_len+=len(sent_text.split())
			
		if doc_len in doc_len_dict:
			doc_len_dict[doc_len]+=1
		else:
			doc_len_dict[doc_len]=1
		
		if year in sent_no_year:
			sent_no_year[year]+=sen_no
		else:
			sent_no_year[year]=sen_no

		if year in doc_no_year:
			doc_no_year[year]+=1
		else:
			doc_no_year[year]=1

		line_no+=1

	writer.commit()

	f2 = open(path+"doc_num", "w")
	f2.write(str(line_no)+"\n")
	for year in doc_no_year:
		text=year+" "+str(doc_no_year[year])+"\n"
		f2.write(text)
	f2.close()

	f3 = open(path+"doc_len", "w")
	for length in sorted(doc_len_dict):
		text=str(length)+" "+str(doc_len_dict[length])+"\n"
		f3.write(text)
	f3.close()

	f4 = open(path+"sent_num", "w")
	for year in sent_no_year:
		text=year+" "+str(sent_no_year[year])+"\n"
		f4.write(text)
	f4.close()

	print("[ Indexing Finished. In total "+str(line_no)+" documents. ]")
	return True

def filter_corpus(corpus_ind_dir, query_list,year_from, year_to):
	ix = index.open_dir(corpus_ind_dir) #load index
	
	with ix.searcher() as searcher:

		parser = QueryParser("content", ix.schema)
		term_list_T=[]
		term_list_Y=[]

		for t in query_list:
			t=re.sub(r'[^a-zA-Z0-9_ ]', '', t).lower()
			splitted=t.split()
			if len(splitted)>1:
				term_list_T.append(query.Phrase("content", splitted))
			else:
				term_list_T.append(query.Term("content", t))

		for y in range(year_from, year_to+1):
			term_list_Y.append(query.Term("year", str(y)))
	        
		q1 = query.Or(term_list_T)
		q2 = query.Or(term_list_Y)

		q_f = query.And([q1,q2]) 

		results = searcher.search(q_f,limit=None)
		
		result_list=[]
		relevant_article_ids=[]
		i=0

		for r in results:
			i+=1
			article_id=r["id"].split('_')[0]
			if not article_id in relevant_article_ids:
				relevant_article_ids.append(article_id)

		new_corpus=[]
		for r_article_id in sorted(relevant_article_ids):
			article_id = r_article_id+"_"
			q=query.Prefix("id", article_id)
			x=0
			row_data={}
			for r in searcher.search(q,limit=None):
				if x==0:
					for key in r:
						if key == "content":
							row_data["sentences"]=r['content']
							x+=1
						elif key == "id":
							row_data["id"]=article_id[:-1]
						else:
							row_data[key] = r[key]
							
				else:
					sent = " "+r['content']
					row_data["sentences"]+=sent
			new_corpus.append(row_data)
		
		pd_save = pd.DataFrame.from_records(new_corpus)
		cols = ['id']  + [col for col in pd_save if col != 'id']
		pd_save = pd_save[cols]
		return pd_save.to_csv(encoding='utf-8')		


# search by query
def search_corpus(corpus_ind_dir, query_list,year_from, year_to,top_n=1000): #the query term in the list will be connected by OR
	
	import time

	start = time.time()

	ix = index.open_dir(corpus_ind_dir) #load index
	
	with ix.searcher() as searcher:

		parser = QueryParser("content", ix.schema)
		term_list_T=[]
		term_list_Y=[]

		for t in query_list:
			t=re.sub(r'[^a-zA-Z0-9_ ]', '', t).lower()
			splitted=t.split()
			if len(splitted)>1:
				term_list_T.append(query.Phrase("content", splitted))
			else:
				term_list_T.append(query.Term("content", t))

		for y in range(year_from, year_to+1):
			term_list_Y.append(query.Term("year", str(y)))
	        
		q1 = query.Or(term_list_T)
		q2 = query.Or(term_list_Y)

		q_f = query.And([q1,q2]) 
		
		# search the index
		results = searcher.search(q_f,limit=None)
		
		
		result_list=[]
		full_sents =[] 
		relevant_article_ids=[]
		i=0

		for r in results:
			i+=1
			article_id=r["id"].split('_')[0]
			if not article_id in relevant_article_ids:
				relevant_article_ids.append(article_id)

			if i<=top_n:
				row_data = {}
				
				row_data["id"] = r["id"]
				row_data["year"] = r["year"]
				row_data["sentence"] = r["content"].lower()#snipet
				row_data["title"] = r["title"].lower()
				row_data["author"] = r["author"]
				row_data["document"] = r["content"].lower()

				for key in r:
					if key in ["content", "id", "title", "year", "author"]:
						continue
					else:
						row_data[key]=r[key]

				row_data["score"] = round(r.score,3)

				result_list.append(row_data)
				full_sents.append({"sentence":row_data["document"]})
			else:
				break

		with open(corpus_ind_dir+"/doc_num") as f:
			total_doc_no = 0
			lines = f.readlines()

			for line in lines:
				doc_num=line.strip().split()
				if len(doc_num)>=2:
					if ((int(doc_num[0])>=year_from) & (int(doc_num[0])<=year_to)):
						total_doc_no+=int(doc_num[1])

		f.close()

		with open(corpus_ind_dir+"/sent_num") as f:
			total_sent_no = 0
			lines = f.readlines()

			for line in lines:
				sent_num=line.strip().split()
				if ((int(sent_num[0])>=year_from) & (int(sent_num[0])<=year_to)):
						total_sent_no+=int(sent_num[1])

		f.close()
		
		print("Results returned:", time.time() - start)
		return [result_list, full_sents, len(results), total_sent_no, len(relevant_article_ids),total_doc_no]

def check_sf(corpus_ind_dir,query_list):
	query_l=[]
	sf=[]
	ix = index.open_dir(corpus_ind_dir) #load index
	with ix.searcher() as searcher:
		for t in query_list:
			t=re.sub(r'[^a-zA-Z0-9_ ]', '', t).lower()
			splitted=t.split()
			if len(splitted)>1:
				docfreq=len(searcher.search(query.Phrase("content", splitted),limit=None))
				t='_'.join(splitted)
			else:
				docfreq = searcher.doc_frequency("content", t)
			
			query_l.append(t)
			sf.append(docfreq)
	return (query_l, sf)

def check_df_year(corpus_ind_dir,query_list,year_from,year_to):
	sf={}
	df={}
	rel_article_no={}
	term_list_Y=[]
	ix = index.open_dir(corpus_ind_dir) #load index

	for y in range(year_from, year_to+1):
		term_list_Y.append(query.Term("year", str(y)))
	        
	q2 = query.Or(term_list_Y)

	with ix.searcher() as searcher:
		for t in query_list:
			relevant_article_ids=[]
			if "+" in t: #AND
				t_list=t.split("+")
				term_list_T_AND=[]
				for tx in t_list:
					tx=re.sub(r'[^a-zA-Z0-9 ]', ' ', tx).lower()
					splitted=tx.split()
					if len(splitted)>1:
						term_list_T_AND.append(query.Phrase("content", splitted))
					else:
						term_list_T_AND.append(query.Term("content", tx))
					q1=query.And(term_list_T_AND)
			elif "/" in t: #AND
				t_list=t.split("/")
				term_list_T_OR=[]
				for tx in t_list:
					tx=re.sub(r'[^a-zA-Z0-9 ]', ' ', tx).lower()
					splitted=tx.split()
					if len(splitted)>1:
						term_list_T_OR.append(query.Phrase("content", splitted))
					else:
						term_list_T_OR.append(query.Term("content", tx))
					q1=query.Or(term_list_T_OR)
			
			else: # single term
				tx = t 
				tx=re.sub(r'[^a-zA-Z0-9_ ]', '', tx).lower()
				splitted=tx.split()
				if len(splitted)>1:
					q1=query.Phrase("content", splitted)			
					tx='_'.join(splitted)
				else:
					q1=query.Term("content", tx)

			
			q_f = query.And([q1,q2]) 
			results=searcher.search(q_f,limit=None)
			t=t.replace(" ","_")

			sf[t]={}
			df[t]={}		
			for r in results:
				y=int(r["year"])
				if y in df[t]:
					sf[t][y]+=1					
				else:
					sf[t][y]=1
				
				article_id=r["id"].split('_')[0]

				if not y in df[t]:
					df[t][y]=[article_id]
				else:
					if not article_id in df[t][y]:
						df[t][y].append(article_id)

				if not article_id in relevant_article_ids:
					relevant_article_ids.append(article_id)

			df_f={}
			for t in df:
				df_f[t]={}
				for y in df[t]:
					df_f[t][y]=len(df[t][y])

			rel_article_no[t]=len(relevant_article_ids)

	
	return [sf,rel_article_no,df_f]


def check_tf_year(corpus_ind_dir,query_list):

	tf={}
	ix = index.open_dir(corpus_ind_dir) #load index
	with ix.searcher() as searcher:
		for t in query_list:
			t=re.sub(r'[^a-zA-Z0-9_ ]', '', t)
			splitted=t.split()
			if len(splitted)>1:
				splitted_lower =[]
				for st in splitted:
					splitted_lower.append(st.lower())
				results=searcher.search(query.Phrase("content", splitted_lower),limit=None)#this is sentence frequency
				t='_'.join(splitted)
				tf[t]=0
				for r in results:						
					tf[t]+=1					
			else:
				results=searcher.frequency("content", t.lower())

				tf[t]=results		

	return tf

# find sentence frequency for a given list of query with AND: group_all==True, OR: group_all==False
def check_group_sf_year(corpus_ind_dir,query_list,group_all):

	ix = index.open_dir(corpus_ind_dir) #load index
	
	with ix.searcher() as searcher:

		parser = QueryParser("content", ix.schema)
		term_list_T=[]
		term_list_T_AND=[]

		for t in query_list:
			if "+" in t: #AND
				t_list=t.split("+")
				term_list_T_AND=[]
				for tx in t_list:
					tx=re.sub(r'[^a-zA-Z0-9 ]', ' ', tx).lower()
					splitted=tx.split()
					if len(splitted)>1:
						term_list_T_AND.append(query.Phrase("content", splitted))
					else:
						term_list_T_AND.append(query.Term("content", tx))

				term_list_T.append(query.And(term_list_T_AND)) #AND
			
			elif "/" in t: #OR
				t_list=t.split("/")
				term_list_T_OR=[]
				for tx in t_list:
					tx=re.sub(r'[^a-zA-Z0-9 ]', ' ', tx).lower()
					splitted=tx.split()
					if len(splitted)>1:
						term_list_T_OR.append(query.Phrase("content", splitted))
					else:
						term_list_T_OR.append(query.Term("content", tx))

				term_list_T.append(query.Or(term_list_T_OR)) #AND
			
			else: #single term
				t=re.sub(r'[^a-zA-Z0-9 ]', ' ', t)
				splitted=t.split()
				if len(splitted)>1:
					splitted_lower =[]
					for st in splitted:
						splitted_lower.append(st.lower())
					term_list_T.append(query.Phrase("content", splitted_lower()))
				else:
					term_list_T.append(query.Term("content", t.lower()))


		if group_all:
			q = query.And(term_list_T)
		else:
			q = query.Or(term_list_T)

		results = searcher.search(q, limit=None)
		sf={}
		df={}

		for r in results:
			y=int(r['year'])
			article_id=r["id"].split('_')[0]

			if y in sf:
				sf[y]+=1
				if not article_id in df[y]:
					df[y].append(article_id)
			else:
				sf[y]=1
				df[y]=[article_id]

		for y in df:
			df[y]=len(df[y])

		return (sf,df)

def get_num_doc_year(corpus_ind_dir):
	doc_num_year={}
	with open(corpus_ind_dir+"/doc_num") as f:
		
		lines = f.readlines()

		for line in lines:
			doc_num=line.strip().split()
			if len(doc_num)>=2:
				doc_num_year[doc_num[0]]=doc_num[1]

	f.close()
	return doc_num_year

def get_doc_len_freq(corpus_ind_dir):
	doc_len={}
	with open(corpus_ind_dir+"/doc_len") as f:
		
		lines = f.readlines()

		for line in lines:
			doc_len_l=line.strip().split()
			if len(doc_len_l)>=2:
				doc_len[int(doc_len_l[0])]=int(doc_len_l[1])

	f.close()
	return doc_len

def top_terms(corpus_ind_dir,top_n):
	ix = index.open_dir(corpus_ind_dir) #load index
	tops = ix.reader().most_frequent_terms('content', number=top_n)
	top_t = {}
	for t in tops:
		top_t[str(t[1].decode("utf-8"))]=t[0]
	return top_t
	
def field_top_terms(corpus_ind_dir,field,top_n=20):
	ix = index.open_dir(corpus_ind_dir) #load index
	tops = ix.reader().most_frequent_terms(field, number=top_n)
	top_t = {}
	for t in tops:
		top_t[str(t[1].decode("utf-8"))]=t[0]
	return top_t

def get_fieldnames(corpus_ind_dir):
	fileds=index.open_dir(corpus_ind_dir).schema.stored_names()
	fileds.remove('content')
	fileds.remove('id')
	fileds.remove('title')
	return fileds

def get_table_fieldnames(corpus_ind_dir):
	fileds=index.open_dir(corpus_ind_dir).schema.stored_names()
	fileds.remove('content')
	fileds.remove('id')
	return fileds
