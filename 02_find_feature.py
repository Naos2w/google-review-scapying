import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import gensim
from gensim.models import Word2Vec
import torch
from transformers import BertTokenizer, BertModel
import logging

logging.basicConfig(level=logging.INFO, filename='02_find_feature.log', filemode='a', format='%(asctime)s %(levelname)s: %(message)s')

logging.info("Program Start !!!")

data = pd.read_csv('01_DataPreFix.csv')
reviews = data['ProcessedReview']

# 將 NaN 值替換為空字符串
data["ProcessedReview"].fillna("", inplace=True)

# BoW
vectorizer = CountVectorizer()
X_bag_of_words = vectorizer.fit_transform(reviews)

# BoW 特徵的詞彙
bow_feature_names = vectorizer.get_feature_names_out()

# 儲存詞袋模型稀疏矩陣
pd.DataFrame.sparse.from_spmatrix(X_bag_of_words, columns=bow_feature_names).to_csv("02_BoW.csv", index=False, encoding="utf-8-sig")
logging.info("BoW 結束")

# TF-IDF
vectorizer = TfidfVectorizer()
X_tfidf = vectorizer.fit_transform(reviews)

# TF-IDF 特徵的詞彙
tfidf_feature_names = vectorizer.get_feature_names_out()
pd.DataFrame.sparse.from_spmatrix(X_tfidf, columns=tfidf_feature_names).to_csv("02_TF-IDF.csv", index=False, encoding="utf-8-sig")
logging.info("TF-IDF 結束")

# Word2Vec
sentences = [review.split() for review in reviews]
model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)
word_vectors = model.wv
logging.info("Word2Vec 特徵 - 嵌入結果:", word_vectors)

# BERT
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
model = BertModel.from_pretrained('bert-base-chinese')

def bert_embedding(text):
    input_ids = tokenizer.encode(text, add_special_tokens=True)
    tokens_tensor = torch.tensor([input_ids])
    with torch.no_grad():
        outputs = model(tokens_tensor)
        embeddings = outputs[0][0, 1:-1].mean(0).numpy()
    return embeddings

X_bert = []
for review in reviews:
    embedding = bert_embedding(review)
    X_bert.append(embedding)
    logging.info("BERT 特徵 - 嵌入結果:", embedding)
