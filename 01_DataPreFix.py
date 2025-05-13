import csv
import re
import pandas as pd
from datetime import datetime, timedelta
from ckiptagger import data_utils, WS
import logging

logging.basicConfig(level=logging.INFO, filename='01_DataPreFix.log', filemode='a', format='%(asctime)s %(levelname)s: %(message)s')

logging.info("Program Start !!!")

# 初始化 CKIP 分詞器
ws = WS("./data")

# 讀取停用詞
with open("stopwords.txt", "r", encoding="utf-8") as f:
    stopwords = [line.strip() for line in f.readlines()]

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

# 資料前處理
def preprocess_review(review):
    logging.info(f"評論處理前: {review}")
    review = remove_emoji_and_special_chars(review)
    logging.info(f"移除emoji跟特殊符號後: {review}")
    words = ws([review], sentence_segmentation=True, segment_delimiter_set={'?', '？', '!', '！', '。', ',','，', ';', ':', '、'})
    words = [word for word in words[0] if word not in stopwords]
    finaltext = " ".join(words)
    logging.info(f"最終評論: {finaltext}")
    return " ".join(words)

# 標記為 5 顆星的標記成誘導評論
def score_based_label(row):
    if row['ReviewRating'] == 5 and row['IsPromotional'] == 1:
        return 1
    return 0

# 促銷活動特徵
patterns = [
    r"五星\S*送\S*",
    r"5星\S*送\S*",
    r"打卡\S*送\S*",
    r"加入\S*活動\S*送\S*",
    r"加入\S*line\S*會員\S*送\S*"
]

def is_promotional_review(review, patterns):
    for pattern in patterns:
        if re.search(pattern, review):
            logging.info(f"符合促銷活動特徵的言論: {review}")
            return True
    return False

def promotional_based_label(row):
    return 1 if is_promotional_review(row['ReviewDescription'], patterns) else 0

# 讀取 CSV 資料集
data = pd.read_csv("GoogleReviewsScraper_new.csv")

logging.info("讀取資料完成")

# 將 "ReviewDate" 欄位的時間格式轉換成 "%Y/%m/%d %H:%M"
data["ReviewActualDate"] = data["ReviewDate"].apply(time_converter)

logging.info("時間轉換完成")

# 過濾掉 ReviewDescription 沒有內容的評論
data = data[data["ReviewDescription"].notnull()]

logging.info("過濾空評論完成")

# 過濾掉包含 "由 Google 提供翻譯" 的資料
data = data[~data["ReviewDescription"].str.contains("由 Google 提供翻譯")]

logging.info("過濾空由 Google 提供翻譯評論完成")

# 在「評論內容前處理」之前，加入標記促銷特徵
data['IsPromotional'] = data.apply(promotional_based_label, axis=1)

logging.info("加入標記促銷特徵完成")

# 應用基於評分的標記方法
data['IsInducing'] = data.apply(score_based_label, axis=1)

logging.info("加入基於評分的標記完成")

# 應用基於促銷特徵的標記方法
# data['IsInducing'] += data['IsPromotional']

# 將標記總數轉換為 0 或 1
# data['IsInducing'] = data['IsInducing'].apply(lambda x: 1 if x > 0 else 0)

logging.info("綜合特徵結果完成")

# 評論內容前處理
data["ProcessedReview"] = data["ReviewDescription"].apply(preprocess_review)

logging.info("資料前處理完成")

# 移除多餘的「IsPromotional」欄位
data.drop(columns=['IsPromotional'], inplace=True)

# 過濾掉 ProcessedReview 沒有內容的評論
data = data[data["ProcessedReview"].notnull()]
logging.info("過濾ProcessedReview空的評論完成")

# 選擇要保存的欄位
data_prefix = data[["ReviewActualDate", "Reviewer", "ReviewRating", "ProcessedReview", "IsInducing"]]

# 保存成 CSV 檔案
data_prefix.to_csv("01_DataPreFix.csv", index=False, encoding="utf-8")

logging.info("Program Finish !!!")

