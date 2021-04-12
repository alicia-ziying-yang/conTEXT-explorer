import gensim
from gensim.models.phrases import Phrases, Phraser
import pandas as pd
from gensim.test.utils import datapath
from gensim.models import Word2Vec
import sys
def train_model(corpus_name):

	processed_file_name = "./topic_model/"+corpus_name+"/processed_content_" + corpus_name + '.pkl'
	sentences=pd.read_pickle(processed_file_name).body.values.tolist()[0]
	
	phrases = Phrases(sentences, min_count=10, progress_per=10000)
	bigram = Phraser(phrases)
	sentences = bigram[sentences]

	model = gensim.models.Word2Vec(
        sentences,
        size=200,   # the size of the dense vector to represent each token
        window=50,   # +/- "window" number of words are counted as neighbors
        min_count=1, # minimium frequency count of words
        workers=10,  # the number of threads to use behind the scenes
        iter=20	 # number of iterations over the corpus
        )
	
	model.save("./topic_model/"+corpus_name+"/"+corpus_name+".model")

	return True

def find_similar(corpus_name, term_list,top_n=50):
	model = Word2Vec.load("./topic_model/"+corpus_name+"/"+corpus_name+".model")
	top_term_list=[]
	for term in term_list:
		if len(term.split())>1:#a phrase
			term_list.append("_".join(term.split()))
			term_list.remove(term)
	# print(term_list)
	for i in model.wv.most_similar(positive=term_list, topn=top_n):
	 	top_term_list.append(i)
	# print(top_term_list)
	return top_term_list

	