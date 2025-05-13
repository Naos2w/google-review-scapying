import csv
import re
import pandas as pd
from datetime import datetime, timedelta
from ckiptagger import data_utils, WS
from gensim.models import Word2Vec
from gensim.models.phrases import Phrases, Phraser
from itertools import chain
import logging

logging.basicConfig(level=logging.INFO, filename='01_DataPreFix_Labeled.log', filemode='a', format='%(asctime)s %(levelname)s: %(message)s')

logging.info("Program Start !!!")
# 下載 CKIP 分詞器
# data_utils.download_data_gdown("./")

# 初始化 CKIP 分詞器
ws = WS("./data")

# 轉換評論時間
def time_converter(time_str):
    now = datetime.now()
    if '年前' in time_str:
        years = int(re.findall(r'\d+', time_str)[0])
        return (now - timedelta(days=365 * years)).strftime("%Y/%m/%d %H:%M")
    elif '個月前' in time_str:
        months = int(re.findall(r'\d+', time_str)[0])
        return (now - timedelta(days=30 * months)).strftime("%Y/%m/%d %H:%M")
    elif '週前' in time_str:
        weeks = int(re.findall(r'\d+', time_str)[0])
        return (now - timedelta(days=7 * weeks)).strftime("%Y/%m/%d %H:%M")
    elif '天前' in time_str:
        days = int(re.findall(r'\d+', time_str)[0])
        return (now - timedelta(days=days)).strftime("%Y/%m/%d %H:%M")
    elif '小時前' in time_str:
        hours = int(re.findall(r'\d+', time_str)[0])
        return (now - timedelta(hours=hours)).strftime("%Y/%m/%d %H:%M")
    elif '分鐘前' in time_str:
        minutes = int(re.findall(r'\d+', time_str)[0])
        return (now - timedelta(minutes=minutes)).strftime("%Y/%m/%d %H:%M")
    else:
        return time_str

# 移除Emoji跟特殊符號
def remove_emoji_and_special_chars(text):
    # 去除emoji
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001f926-\U0001f937"  # 各種手勢和人物表情符號
        u"\U00010000-\U0010ffff"  # 更廣泛的 Unicode 範圍
        u"\u200d"                 # 連接符號
        u"\u2640-\u2642"          # 女性和男性符號
        u"\u2600-\u2B55"          # 各種符號
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats 重音符號
        u"\u3030"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub(r"", text)

    # 去除非繁體中文字符
    text = re.sub(r"[^\u4e00-\u9fa5]", "", text)
    return text

# 標記為 5 顆星的標記成誘導評論
def score_based_label(row):
    if row['ReviewRating'] == 5 and row['IsPromotional'] == 1:
        return 1
    return 0

# # 讀取停用詞
# with open("./stopwords.txt", "r", encoding="utf-8") as f:
#     stopwords = [line.strip() for line in f.readlines()]
# logging.info("讀取停用詞 完成")

# # 讀取 CSV 資料集
# data = pd.read_csv("./GoogleReviewsScraper_new.csv")
# logging.info("讀取資料 完成")

# # 將 "ReviewDate" 欄位的時間格式轉換成 "%Y/%m/%d %H:%M"
# data["ReviewActualDate"] = data["ReviewDate"].apply(time_converter)
# logging.info("時間轉換 完成")

# # 過濾掉 ReviewDescription 沒有內容的評論
# data = data[data["ProcessedReview"]!=""]
# logging.info("過濾空評論 完成")

# # 過濾掉包含 "由 Google 提供翻譯" 的資料
# data = data[~data["ReviewDescription"].str.contains("由 Google 提供翻譯")]
# logging.info("過濾空由 Google 提供翻譯評論 完成")

# 資料前處理
# def preprocess_review(review):
#     logging.info(f"評論處理前: {review}")
#     review = remove_emoji_and_special_chars(review)
#     logging.info(f"移除emoji跟特殊符號後: {review}")
#     words = ws([review], sentence_segmentation=True, segment_delimiter_set={'?', '？', '!', '！', '。', ',','，', ';', ':', '、'})
#     words = [word for word in words[0] if word not in stopwords]
#     finaltext = " ".join(words)
#     logging.info(f"最終評論: {finaltext}")
#     return " ".join(words)

# data["ProcessedReview"] = data["ReviewDescription"].apply(preprocess_review)
# logging.info("資料前處理 完成")

# # 過濾掉 ProcessedReview 欄位中包含 "更多" 的資料
# data = data[data["ProcessedReview"] != "更多"]
# logging.info("過濾掉 ProcessedReview 欄位中為 \"更多\" 的資料 完成")

# # 先保存成 資料前處理完的 檔案
# data.to_csv("./01_DataPreFix_CKIP.csv", index=False, encoding="utf-8")

# 讀取 CSV 資料集
data = pd.read_csv("./01_DataPreFix_CKIP.csv")

# 使用 CKIPtagger 將評論分詞
tokenized_reviews = data['ProcessedReview'].apply(lambda x: ws([x])[0])
logging.info("將評論分詞 完成")

# 訓練word2vec模型
model = Word2Vec(tokenized_reviews, vector_size=100, window=5, min_count=5, workers=4, epochs=50)
logging.info("訓練word2vec模型 完成")

# 輸入的特徵詞彙
feature_phrases = ["打卡 送", "評論 送", "五星 送", "加入會員 送", "活動 送", "line 送"]

# 找到與特徵詞彙相似的詞彙
similar_features = []
for phrase in feature_phrases:
    words = phrase.split()
    for word in words:
        if word in model.wv.key_to_index:
            similar_words = model.wv.most_similar(positive=[word], topn=5)
            similar_features.extend(similar_words)
logging.info("找到與特徵詞彙相似的詞彙 完成")

# 去除重複的詞彙
similar_features = list(set(similar_features))
logging.info("去除重複的詞彙 完成")

# 打印相似特徵詞彙
logging.info("找到與特徵詞彙相似的詞彙：")

# 根據相似度由高到低排序
sorted_similar_features = sorted(similar_features, key=lambda x: x[1], reverse=True)
for feature, similarity in sorted_similar_features:
    logging.info(f"{feature} (相似度: {similarity})")

# 將找到的相似詞彙添加到特徵集
feature_phrases.extend([word for word, _ in similar_features])
logging.info("將找到的相似詞彙添加到特徵集 完成")

# 修改此函數以標記評分為5且包含這些特徵的評論
def has_feature(row):
    text = row["ProcessedReview"]
    rating = row["ReviewRating"]
    for feature in feature_phrases:
        if feature in text and rating == 5:
            return 1
    return 0

data['IsInducing'] = data.apply(has_feature, axis=1)
logging.info("加入基於評分的標記 完成")

# 過濾掉 ProcessedReview 沒有內容的評論
data = data[data["ProcessedReview"]!=""]
logging.info("過濾 ProcessedReview 空的評論 完成")

# 選擇要保存的欄位
data_prefix = data[["RestName", "ReviewActualDate", "Reviewer", "ReviewRating", "ProcessedReview", "IsInducing"]]

# 保存成 CSV 檔案
data_prefix.to_csv("./01_DataPreFix_Labeled.csv", index=False, encoding="utf-8")
logging.info("Program Finish !!!")

