from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from os import getcwd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import time
import datetime
import pandas as pd
import logging
import unicodedata
import os

#全域變數
AllRestList = []
SpcecialRestList = ['米樂', '香草微風 花園廚房', '鹿森林', '剛好Cucina義式料理', '茉莉小鎮', '壹號館']
ExcludeList = ['新竹巨城', '原味燉品屋','瓦城泰國料理', '芙洛麗大飯店']
_RestName = ""
RestListInCSV = []

# 紀錄每則評論爬取的時間
ScrapeTime = []
# 紀錄每則評論的餐廳名稱
RestName = []
# 紀錄每則評論的是否有附圖
PicAttached = []
# 紀錄每則評論的評論者
ReviewerName = []
# 紀錄每則評論的評論時間
ReviewDate = []
# 紀錄每則評論的星級
ReviewRating =[]
# 紀錄每則評論的星級
ReviewDescription = []
# 紀錄每則評論的身分(在地嚮導，或是總共留了多少則評論)
TotalReviewsByUser = []

webdriver_obj = []
thisreview = []
last_len = 0
# 紀錄評論爬取的筆數
iLoopIdx = 1
# 設定每一個餐廳最大爬取評論數量 (此數量還要*10才是最大評論數量，因為一塊評論就會有10個)
iMaxRvsCnt = 6


#Log設定

FORMAT = '%(asctime)s %(levelname)s: %(message)s'

logging.basicConfig(level=logging.INFO, filename='GoogleReviewsScraper.log', filemode='a', format=FORMAT)

logging.info("Program Start !!!")

def write_to_csv(csv_file, data):
    global ScrapeTime, RestName, PicAttached, ReviewerName, ReviewDate, ReviewRating, ReviewDescription, TotalReviewsByUser
    try:
        # 讀取 csv 檔案
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # 如果csv不存在，則創建新的DataFrame
        df = pd.DataFrame(columns=data.columns)

    # 把資料追加到DataFrame的末尾
    new_data = pd.DataFrame(data, columns=df.columns)
    df = df.append(new_data, ignore_index=True)

    # 把DataFrame寫入csv檔案後
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')

    # 寫入成功後初始化資料
    ScrapeTime = []
    RestName = []
    PicAttached = []
    ReviewerName = []
    TotalReviewsByUser = []
    ReviewRating =[]
    ReviewDate = []
    ReviewDescription = []

def distinct_csv_rest(csv_file):
    global RestListInCSV
    try:
        # 讀取 csv 檔案
        df = pd.read_csv(csv_file, usecols=['RestName'], encoding='utf-8-sig')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # 如果csv不存在，則創建新的DataFrame
        return

    # 將該欄位的值去重，並存入一個 list 中
    try:
        # 讀取 csv 檔案
        RestListInCSV = df['RestName'].unique().tolist()
    except KeyError:
        # 表示沒有這個檔案
        return

def get_reviews(thisreview, rest_Name):
    global last_len, iLoopIdx
    # 取得所有評論
    try:
        iAllReviewCnt = None

        WebDriverWait(webdriver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "z5jxId"))
        )
        ayAllRvCnt = webdriver.find_elements(By.CLASS_NAME, "z5jxId")

        if ayAllRvCnt != None:
            for AllRvCnt in ayAllRvCnt:
                if AllRvCnt.text != "":
                    iAllReviewCnt = int(AllRvCnt.text.replace(",","").replace(" 則評論", ""))
        # 超過最大爬取評論數量則以最大值為主
        if iAllReviewCnt>iMaxRvsCnt*10:
            iAllReviewCnt=iMaxRvsCnt*10
    except NoSuchElementException:
        print(rest_Name.text + " 取不到所有評論數量")
    
    for webdriver_obj in thisreview.find_elements(By.CLASS_NAME, "WMbnJf.vY6njf"):
        #餐廳名稱
        RestName.append(rest_Name.text)
        #爬取時間
        loc_dt = datetime.datetime.today()
        loc_dt_format = loc_dt.strftime("%Y/%m/%d %H:%M:%S")
        ScrapeTime.append(loc_dt_format)
        logging.info("第" + str(iLoopIdx) + "筆加入爬取時間")
        #評論者
        Name = webdriver_obj.find_element(By.CLASS_NAME, "TSUbDb")
        ReviewerName.append(Name.text)
        logging.info("第" + str(iLoopIdx) + "筆加入評論者")
        try:
            ReviewByuser = webdriver_obj.find_element(By.CLASS_NAME, "A503be")
            TotalReviewsByUser.append(ReviewByuser.text)
            logging.info("第" + str(iLoopIdx) + "筆加入評論種類")
        except NoSuchElementException:
            TotalReviewsByUser.append("")
        #評分
        WebDriverWait(webdriver_obj, 3).until(
            #EC.presence_of_element_located((By.CLASS_NAME, "Fam1ne.EBe2gf"))
            EC.presence_of_element_located((By.CLASS_NAME, "lTi8oc.z3HNkc"))
        )
        #star = webdriver_obj.find_element(By.CLASS_NAME, "Fam1ne.EBe2gf")
        star = webdriver_obj.find_element(By.CLASS_NAME, "lTi8oc.z3HNkc")
        ReviewStar =star.get_attribute("aria-label")
        RvStartTxt = ReviewStar.replace("評等：","").replace(" (最高：5)，","")
        ReviewRating.append(RvStartTxt)
        logging.info("第" + str(iLoopIdx) + "筆加入星數評級")
        #評分時間
        Date = webdriver_obj.find_element(By.CLASS_NAME, "PuaHbe")
        ReviewDate.append(Date.text.replace("\n最新", ""))
        logging.info("第" + str(iLoopIdx) + "筆加入評分時間")
        #附圖與否
        try:
            Pic = webdriver_obj.find_element(By.CLASS_NAME, "DQBZx")
            PicAttached.append("Y")
            logging.info("第" + str(iLoopIdx) + "筆加入附圖與否")
        except NoSuchElementException:
            PicAttached.append("N")
        #評分內容
        WebDriverWait(webdriver_obj, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Jtu6Td"))
        )
        Body = webdriver_obj.find_element(By.CLASS_NAME, 'Jtu6Td')
        try:
            webdriver_obj.find_element(By.CLASS_NAME, 'review-snippet').click()
            s_32B = webdriver_obj.find_element(By.CLASS_NAME, 'review-full-text')
            ReviewDescription.append(s_32B.text)
            logging.info("第" + str(iLoopIdx) + "筆加入評論內容")
        except NoSuchElementException:
            ReviewDescription.append(Body.text)
        iLoopIdx += 1
    
    # 定位最下面那顆 Loading 的球
    WebDriverWait(webdriver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'loris') or contains(@class,'wH2kcb')]"))
    )
    e = webdriver.find_element(By.XPATH, "//div[contains(@class,'loris') or contains(@class,'wH2kcb')]")
    try:
        webdriver.execute_script("arguments[0].scrollIntoView();", e)
        logging.info("滾動成功")
    except:
        logging.info("滾動失敗")
    
    time.sleep(3)

    WebDriverWait(webdriver, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, "gws-localreviews__general-reviews-block"))
    )
    reviews = webdriver.find_elements(By.CLASS_NAME, "gws-localreviews__general-reviews-block")

    r_len = len(reviews)
    logging.info("下滾後總共有 " + str(r_len) + " 區評論")
    logging.info("目前已爬 " + str(last_len) + " 區評論")
    
    if r_len > last_len and last_len < iMaxRvsCnt*10:
        last_len = r_len
        get_reviews(reviews[r_len-1], rest_Name)
    elif iLoopIdx < iAllReviewCnt:
        logging.info("e 的 html " + e.get_attribute("outerHTML"))
        logging.info("" + rest_Name.text + "總共有 " + str(iAllReviewCnt*10) + " 則評論，但只有爬 " + str(iLoopIdx) + " 則評論")
        CloseReviews(webdriver)
        raise Exception
    else:
        CloseReviews(webdriver)
        #webdriver.back()

def CloseReviews(wbd):
    try:
        WebDriverWait(wbd, 3).until(
            EC.presence_of_element_located((By.XPATH, "//div[(contains(@style, 'outline: none; z-index: 1000; filter: none;'))]//div[@class='Xvesr']"))
        )
        BtnCloseReviews = wbd.find_element(By.XPATH, "//div[(contains(@style, 'outline: none; z-index: 1000; filter: none;'))]//div[@class='Xvesr']")
        BtnCloseReviews.click()
    except TimeoutException:
        # 會找不到是因為有兩個以上結果
        return

def get_ReviewsBlockAndRestName(wbd, rstName = ""):
    global last_len, _RestName

    try:
        #按下所有評論
        WebDriverWait(wbd, 3).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='hqzQac']"))
        )
        BtnAllRvs = wbd.find_element(By.XPATH, "//span[@class='hqzQac']")
        BtnAllRvs.click()
    
        time.sleep(3)
        #抓取當下餐廳名稱
        WebDriverWait(wbd, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "P5Bobd"))
        )

        _RestName = wbd.find_element(By.CLASS_NAME, "P5Bobd")
        #Debug logging.info(_RestName.text)
        WebDriverWait(wbd, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "gws-localreviews__general-reviews-block"))
        )
        reviews = wbd.find_elements(By.CLASS_NAME, "gws-localreviews__general-reviews-block")
        last_len = len(reviews)

        logging.info("找到第一個評論區塊，共有 " + str(last_len) + " 則評論")
        return reviews
    except TimeoutException:
        # Timeout 有可能是沒有評論，也有可能是有搜尋到兩個以上的結果
        logging.info("" + rstName + " 有兩個以上的結果")
        try:
            MoreSearchResult(wbd)
        except NoSuchElementException:
            logging.info("" + rstName + " 沒有評論")
            return None

        time.sleep(3)
        #抓取當下餐廳名稱
        WebDriverWait(wbd, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "SPZz6b"))
        )

        _RestName = wbd.find_element(By.CLASS_NAME, "SPZz6b")
        
        WebDriverWait(wbd, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "gws-localreviews__general-reviews-block"))
        )
        reviews = wbd.find_elements(By.CLASS_NAME, "gws-localreviews__general-reviews-block")
        last_len = len(reviews)

        logging.info("找到第一個評論區塊，共有 " + str(last_len) + " 則評論")
        return reviews
    
        # ReturnGoogleSearch(wbd)
        # GoogleSearch(wbd, rstName + " 新竹市")
        # reviews = get_ReviewsBlockAndRestName(wbd, rstName + " 新竹市")
        # return reviews

# 搜尋出兩個以上的話要用這個去找
def MoreSearchResult(wbd):
    # 多個結果
    # 定位餐廳名稱
    try:
        WebDriverWait(wbd, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dbg0pd"))
        )
        RestBlock = wbd.find_elements(By.CLASS_NAME, "dbg0pd")
        # 只按下第一個
        if len(RestBlock)>0:
            RestBlock[0].click()
        
        RestBlock = None
    except TimeoutException:
        # 如果沒定位到餐廳名稱表示是搜尋到正確的結果
        try:
            # 再次定位所有評論
            BtnAllRvs = wbd.find_element(By.XPATH, "//span[@class='hqzQac']")
        except NoSuchElementException:
            # 沒有找到表示沒有評論
            raise NoSuchElementException

    time.sleep(5)

    # 按下評論頁籤
    WebDriverWait(wbd, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "SVWlSe.t35a5d"))
    )
    ReviewCategory = wbd.find_elements(By.CLASS_NAME, "SVWlSe.t35a5d")
    for rvBtn in ReviewCategory:
        if rvBtn.text == "評論":
            rvBtn.click()
            break
    
    # 往下滾動
    element = wbd.find_element(By.CLASS_NAME, 'tg6pY.ZwRhJd')
    wbd.execute_script("arguments[0].scrollIntoView();", element)
    
def OpenGoogle(wbd):
    #options = Options()
    options = webdriver.ChromeOptions()
    #opt = wbd.ChromeOptions()
    # 指定瀏覽器解析度
    options.add_argument('--window-size=1440,900')
    # 避免BUG
    options.add_argument('--disable-gpu')
    # 隱藏捲軸
    options.add_argument('--hide-scrollbars')
    # 使用Chrome擴充元件
    #options.add_extension(getcwd() + "\AdBlock.crx")
    # 禁止彈出視窗
    prefs = {
        'profile.default_content_setting_values' :  {
            'notifications' : 2
        }
    }
    options.add_experimental_option('prefs', prefs)
    #wbd = webdriver.Chrome(executable_path=getcwd() + "\chromedriver.exe", options=options)
    wbd = webdriver.Chrome(getcwd() + "\chromedriver.exe", options=options)
    #chrome = wbd.Chrome(options=opt)
    #wbd = chrome
    #因為AdBlock會打開新分頁，需等待數秒
    #time.sleep(10)
    #分頁數量 > 1
    #if(len(wbd.window_handles)>1):
    #    #切換到第二個分頁
    #    wbd.switch_to.window(wbd.window_handles[1])
    #    #關閉AdBlock分頁
    #    if(wbd.title.find('AdBlock')>=0):
    #        wbd.close()
    #        wbd.switch_to.window(wbd.window_handles[0])
    #打開 Google 網站
    wbd.get('https://www.google.com/')
    return wbd

def GoogleSearch(wbd, keyword=""):
    WebDriverWait(wbd, 3).until(
        EC.presence_of_element_located((By.XPATH, "//textarea[@name='q'] | //input[@name='q']"))
    )
    GoogleSearch = wbd.find_element(By.XPATH, "//textarea[@name='q'] | //input[@name='q']")
    # 檢查是否有非 BMP 字元集
    if all(ord(c) < 0x10000 for c in keyword):
        keyword = keyword
    else:
        keyword = unicodedata.normalize('NFKD', keyword).encode('ascii', 'ignore').decode()
    # 搜尋關鍵字
    GoogleSearch.send_keys(keyword)
    GoogleSearch.submit()

def ReturnGoogleSearch(wbd):
    #WebDriverWait(wbd, 5).until(
    #    EC.presence_of_element_located((By.XPATH, "//a[@id='logo' and @title='Google 首頁']"))
    #)
    BtnLogo = wbd.find_element(By.XPATH, "//a[@id='logo' and @title='Google 首頁']")
    #BtnLogo = wbd.find_element(By.XPATH, "//div[@class='logo Ib7Efc']")
    BtnLogo.click()

def GetAllRestList(wbd):
    global RestListInCSV

    WebDriverWait(wbd, 5).until(
        #EC.presence_of_element_located((By.CLASS_NAME, "MXl0lf.tKtwEb.wHYlTd"))
        EC.presence_of_element_located((By.CLASS_NAME, "Z4Cazf.OSrXXb"))
    )
    # 按下所有餐廳
    #btnMoreLoc = wbd.find_element(By.CLASS_NAME, "MXl0lf.tKtwEb.wHYlTd")
    btnMoreLoc = wbd.find_element(By.CLASS_NAME, "Z4Cazf.OSrXXb")
    btnMoreLoc.click()

    # 讓網頁跑一下
    time.sleep(3)

    WebDriverWait(wbd, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "WaZi0e.OSrXXb"))
    )
    RatingFilter = wbd.find_elements(By.CLASS_NAME, "WaZi0e.OSrXXb")
    for Rf in RatingFilter:
        # 按下評分按鈕
        if(Rf.text=="評分"):
            Rf.click()
            break

    WebDriverWait(wbd, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "w3RMhb"))
    )
    FourStarFilter = wbd.find_elements(By.CLASS_NAME, "w3RMhb")
    for FSf in FourStarFilter:
        # 按下4.5顆星以上
        if(FSf.text=="4.5\n顆星以上"):
            FSf.click()
            break
    
    time.sleep(2)
    
    # 按下營業時間
    WebDriverWait(wbd, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "WaZi0e.OSrXXb"))
    )
    OpenFilter = wbd.find_elements(By.CLASS_NAME, "WaZi0e.OSrXXb")
    for Of in OpenFilter:
        # 按下營業時間
        if(Of.text=="營業時間"):
            Of.click()
            break
    
    # 選擇星期六
    WebDriverWait(wbd, 5).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'czHJJ')][not(@style) or not(contains(@style,'display:none'))]"))
    )
    DayofWeekList = wbd.find_element(By.XPATH, "//div[contains(@class,'czHJJ')][not(@style) or not(contains(@style,'display:none'))]")
    print("DayofWeekList html: "+DayofWeekList.get_attribute("outerHTML"))
    for dw in DayofWeekList.find_elements(By.CLASS_NAME, "w3RMhb"):
        print("dw html: "+dw.get_attribute("outerHTML"))
        # 按下星期六
        if(dw.text=="星期六"):
            dw.click()
            break
    
    # 選擇下午12:00
    WebDriverWait(wbd, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "czHJJ.K1JHbd"))
    )
    OpenTimeList = wbd.find_element(By.CLASS_NAME, "czHJJ.K1JHbd")
    for ot in OpenTimeList.find_elements(By.CLASS_NAME, "w3RMhb"):
        # 按下下午12:00
        if(ot.text=="下午12:00"):
            ot.click()
            break
    
    x = 0
    while 1:
        # 指定爬餐廳區域
        WebDriverWait(wbd, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "rlfl__tls.rl_tls"))
        )
        RestBlock = wbd.find_element(By.CLASS_NAME, "rlfl__tls.rl_tls")
        # 指定每一個餐廳
        WebDriverWait(RestBlock, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "rllt__details"))
        )
        EachBlock = RestBlock.find_elements(By.CLASS_NAME, "rllt__details")
        for EcBk in EachBlock:
            # 取餐廳名稱
            WebDriverWait(EcBk, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "OSrXXb"))
            )
            RestNameList = EcBk.find_element(By.CLASS_NAME, "OSrXXb")
            print(RestNameList.text)
            # # 取贊助商字眼
            # Sponsor=""
            # try:
            #     WebDriverWait(EcBk, 5).until(
            #         EC.presence_of_element_located((By.XPATH, "//span[@class='U3A9Ac qV8iec']"))
            #     )
            #     _Sponsor = EcBk.find_element(By.XPATH, "//span[@class='U3A9Ac qV8iec']")
            #     Sponsor = _Sponsor
            # except TimeoutException:
            #     print("沒有廣告就跳過吧")
            
            # 取停業的字串
            try:
                # WebDriverWait(EcBk, 5).until(
                # EC.presence_of_element_located((By.XPATH, ".//span[contains(@style,'color:rgba(242,139,130,1.0)')]"))
                # )
                RestClosed = EcBk.find_element(By.XPATH, ".//span[contains(@style,'color:rgba(242,139,130,1.0)')]")
            except NoSuchElementException:
                RestClosed = None

            # 過濾掉停業的餐廳
            if (RestNameList.text!="" and (RestClosed==None or(RestClosed!=None and RestClosed.text!="暫停營業"))):
                if RestNameList.text not in AllRestList and RestNameList.text not in RestListInCSV:
                    AllRestList.append(RestNameList.text)
        #for Rn in RestNameList:
        #    if(Rn!=""):
        #        AllRestList.append(Rn.text)

        #deubg for i in range(len(AllRestList)):
        #deubg     logging.info("[" + str(i) + "]" + AllRestList[i])

        try:
            BtnNextPage = wbd.find_element(By.XPATH, "//span[contains(@style,'display:block;margin-left:53px')]")
            BtnNextPage.click()
            time.sleep(3)
            x += 1
        except NoSuchElementException:
            break

webdriver = OpenGoogle(webdriver)
distinct_csv_rest("GoogleReviewsScraper_new.csv")
#GoogleSearch(webdriver, "新竹巨城")
#reviews = get_ReviewsBlockAndRestName(webdriver, "新竹巨城")
#GoogleSearch(webdriver, "法諾義式廚房-巨城店-新竹推薦義式料理|人氣義式餐廳|必吃義大利麵|手做比薩推薦|平價義大利麵|平價美食推薦")
#get_ReviewsBlockAndRestName(webdriver, "法諾義式廚房-巨城店-新竹推薦義式料理|人氣義式餐廳|必吃義大利麵|手做比薩推薦|平價義大利麵|平價美食推薦")
#CloseReviews(webdriver)
GoogleSearch(webdriver, "新竹市 美式餐廳")
GetAllRestList(webdriver)
ReturnGoogleSearch(webdriver)
GoogleSearch(webdriver, "新竹市 日式餐廳")
GetAllRestList(webdriver)
ReturnGoogleSearch(webdriver)
# GoogleSearch(webdriver, "新竹市 台式餐廳")
# GetAllRestList(webdriver)
# ReturnGoogleSearch(webdriver)
# GoogleSearch(webdriver, "新竹市 義式餐廳")
# GetAllRestList(webdriver)
# ReturnGoogleSearch(webdriver)
# GoogleSearch(webdriver, "新竹市 法式餐廳")
# GetAllRestList(webdriver)
# ReturnGoogleSearch(webdriver)

for i in range(len(AllRestList)):
    if AllRestList[i] not in ExcludeList:
        if AllRestList[i] in SpcecialRestList:
            keyword = AllRestList[i] + " 新竹市"
        else:
            keyword = AllRestList[i]
        GoogleSearch(webdriver, keyword)
        reviews = get_ReviewsBlockAndRestName(webdriver, AllRestList[i])
        # 如果 reviews 是空的，表示沒有評論
        if reviews == None:
            ReturnGoogleSearch(webdriver)
            continue
        logging.info("現在爬取 " + _RestName.text + " 的評論")
        try:
            get_reviews(reviews[last_len-1], _RestName)
        except Exception:
            continue
        # Reset 爬到的評論數量
        iLoopIdx=1
        data = pd.DataFrame ({
            'ScrapeTime':ScrapeTime,
            'RestName':RestName,
            'PicAttached':PicAttached,
            'ReviewerName':ReviewerName,
            'TotalReviewsByUser':TotalReviewsByUser,
            'ReviewRating':ReviewRating,
            'ReviewDate':ReviewDate,
            'ReviewDescription':ReviewDescription})
        
        write_to_csv("GoogleReviewsScraper_new.csv", data)
        ReturnGoogleSearch(webdriver)

logging.info("Program End !!!")
