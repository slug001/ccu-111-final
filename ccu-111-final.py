from flask import Flask, request,render_template,session,abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import requests
import json
import psycopg2
import math
import configparser
import time
import re

database_url='postgres://zlujzrtgrbvpgb:ba830f737f30a8309677d917becefb9295f1956a8521b478604e3e4e54c76bb1@ec2-54-165-90-230.compute-1.amazonaws.com:5432/d64qh26kv7tm2k'

#啟用config
config = configparser.ConfigParser()
config.read('config.ini')

#設定flask 密碼、金鑰 
app = Flask(__name__)
app.config['SECRET_KEY']='ben9709830018'

#檢查是否登入
def check_login():
    key=session.get('session_password')
    if (key == None):
        login_status='No'
        login_account='小魔女最討厭來路不明的怪叔叔了'
    else:
        login_status='Yes'
        login_account=key
    return login_status,login_account

@app.route('/', methods=['GET','POST'])
def home():
    if request.method =='GET':
        #抓取使用者資料
        session['session_password']='2'
        login_status,login_account=check_login()
        
        
        return render_template("home.html",repeat=login_status+login_account)
    else:
        #user_position=request.values['input']

        #抓取資料
        user_name=request.values['user_name']
        restaurant_name=request.values['restaurant_name']
        rank=request.values['rank']

        #資料庫連線
        conn = psycopg2.connect(database_url,sslmode='require')
        cursor=conn.cursor()
        
        #先新增歷史紀錄，記得抓現在的時間
        localtime=time.localtime(int(time.time())+28800)
        time_text= time.strftime("%Y-%m-%d %H:%M:%S", localtime)
        sql="INSERT INTO history_eat(user_name,restaurant_name,rank,day) VALUES(%s,%s,%s,%s)"
        cursor.execute(sql,(user_name,restaurant_name,rank,time_text))
        conn.commit()
        
        #找出所有的使用者名稱
        sql="SELECT user_name FROM restaurant_data "
        cursor.execute(sql)
        all_user_name=cursor.fetchall()
        
        
        #找出所有餐廳
        sql="SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='restaurant_data'"
        cursor.execute(sql)
        all_restaurant_name=cursor.fetchall()


        #轉化一下
        all_user_name=[i[0] for i in all_user_name]
        all_restaurant_name=[i[0] for i in all_restaurant_name]
       
        #如果使用者和餐廳都存在，更新評價
        
        if (user_name in all_user_name and restaurant_name in all_restaurant_name ):
            sql="UPDATE restaurant_data SET {restaurant_name} = {rank} WHERE user_name='{user_name}'"\
                .format(restaurant_name=restaurant_name,rank=rank,user_name=user_name)
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
            return render_template("home.html",repeat=time_text)
        
        cursor.close()
        conn.close()

        return render_template("home.html",repeat='false')


#歷史紀錄頁面
@app.route("/record",methods=['GET'])
def record():
    #這邊試著把離現在最近的十筆資料抓出來
    conn = psycopg2.connect(database_url,sslmode='require')
    cursor=conn.cursor()
    sql="SELECT * FROM history_eat WHERE user_name='{user_name}' ORDER BY day DESC LIMIT 10 ".format(user_name='2')
    cursor.execute(sql)
    all_data=cursor.fetchall()
    cursor.close()
    conn.close()
    #先在前面加資料數量
    history_data=[len(all_data)]
    
    #再把資料一個一個抓進去，注意時間先轉成字串
    for i in all_data:
        for j in range(1,len(i)):
            if(j<3):
                history_data.append(i[j])
            else:
                tmp=str(i[j])
                history_data.append(tmp)

    #如果無資料則改成''
    for i in range(len(history_data)):
        if(history_data[i]==None):
            history_data[i]=''
            
    #再轉成字串
    history_data_str=''
    for i in history_data:
        history_data_str+=str(i)
    #history_data=str(history_data).strip('[]')    
    #history_data=str(history_data)
    return render_template("record.html",historyData=history_data_str)


#登入頁面
@app.route("/account", methods=['GET','POST'])
def login():
    if (request.method =='GET'):
        return render_template("account.html")
    try:
        user_name=request.values['account']
        user_password=request.values['password']
    except:
        return render_template("account.html")
    #資料庫連線
    conn = psycopg2.connect(database_url,sslmode='require')
    cursor=conn.cursor()
    sql="SELECT user_name FROM user_data"
    cursor.execute(sql)
    all_user_name=cursor.fetchall()
   
    #轉成list
    all_user_name=[i[0] for i in all_user_name]
    if(user_name in all_user_name):
        sql="SELECT user_password FROM user_data WHERE user_name='{user_id}'".format(user_id=user_name)
        cursor.execute(sql)
        password=cursor.fetchall()
        password=[i[0] for i in password]
        cursor.close()
        conn.close()
        return render_template("account.html",test=password)
        if(user_password==password):
            return render_template("home.html",login_status="yes")
        else:
            return render_template("account.html",login_status="error")
    else:
        cursor.close()
        conn.close()
        return render_template("account.html",login_status="error")
        
    
    
    #註冊系統
    """
    if(user_name==None or user_password==None):
        return render_template("home.html",repeat='get_None')
    else:
        return render_template("home.html",repeat='not_None')
    """
    #資料庫連線
    """
    conn = psycopg2.connect(database_url,sslmode='require')
    cursor=conn.cursor()
    
    #抓取已用過的name
    sql="SELECT user_name FROM user_data"
    cursor.execute(sql)
    all_user_name=cursor.fetchall()
   
    #轉成list
    all_user_name=[i[0] for i in all_user_name]
    #如果名稱已存在則更新失敗
    if(user_name in all_user_name):
        cursor.close()
        conn.close()
        return render_template("home.html",repeat='new_user false')
    #新的名稱則把資料記錄在user_data和restaurant_data裡
    sql="INSERT INTO user_data(user_name,user_password) VALUES(%s,%s)"
    val=(user_name,user_password)
    cursor.execute(sql,val)
    conn.commit()
    
    sql="INSERT INTO restaurant_data(user_name) VALUES(%s)"
    cursor.execute(sql,(user_name))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return render_template("home.html",repeat='new_user success')
    """

#登出系統
@app.route("/logout",methods=['GET','POST'])
def logout():
    session.clear()
    return render_template("login.html")

#推薦系統
@app.route("/recommend", methods=['GET','POST'])
def recommend():
    login_status,login_account=check_login()
    #name=request.values['search_name']
    
    #先抓取資料庫的資料
    conn = psycopg2.connect(database_url,sslmode='require')
    cursor=conn.cursor()

    sql="SELECT * FROM restaurant_data "
    cursor.execute(sql)
    all_data=cursor.fetchall()
    
    sql="SELECT * FROM restaurant_data WHERE user_name='{user_name}'".format(user_name=login_account)
    cursor.execute(sql)
    target_data=cursor.fetchall()

    #計算資料長度和轉換格式
    target_len=0
    target_data=[list(i) for i in target_data]
    target_data=target_data[0]
    restaurant_len=int(len(target_data))
    
    for i in range(1,restaurant_len):
        if(target_data[i]!= None):
            target_len+=int(target_data[i])*int(target_data[i])
    
    target_len=round(math.sqrt(target_len),4)
    all_data=[list(i) for i in all_data]
    

    """ 協同過濾
        計算目標資料和其他資料的餘弦相似度
        並找出最相近的五位使用者，在近一步找出共同喜歡的餐廳"""
    
    max_cos=[]
    max_name=[]
    for i in all_data:
        other_len=0;all_cos=0;final_cos=0
        if(i[0]==name):
            continue
        for j in range(1,restaurant_len):
            #計算長度以及cos
            if(i[j]!=None):
                other_len+=int(i[j])*int(i[j])
            if(i[j]==None or target_data[j]==None):
                continue
            all_cos+=int(i[j])*int(target_data[j])
        #如果夾角為零則不用計算
        if(other_len>0 and all_cos>0):
            other_len=round(math.sqrt(other_len),4)
            final_cos=float(all_cos)/float(other_len)*float(target_len)
        #如果人數小於五就增加，大於則比較
        if(len(max_cos)>=5):
            if(final_cos>min(max_cos)):
                switch=max_cos.index(min(max_cos))
                max_cos[switch]=final_cos
                max_name[switch]=i[0]
        elif(other_len>0 and all_cos>0):
            max_cos.append(final_cos)
            max_name.append(i[0])
            
    #找出相似的使用者後再找出他們資料庫中的評分資料
    recommend_data=[]
    for name in max_name:
        sql="SELECT * FROM restaurant_data WHERE user_name='{user_name}'".format(user_name=name)
        cursor.execute(sql)
        tmp_data=cursor.fetchall()
        recommend_data.append(list(tmp_data[0]))
    
    #先抓餐廳名稱，再找出共同喜愛的幾家餐廳
    best_rest_rank=[];best_rest_name=[]
    sql="SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='restaurant_data'"
    cursor.execute(sql)
    all_restaurant_name=cursor.fetchall()
    all_restaurant_name=[i[0] for i in all_restaurant_name]
    #執行次數=店家數量
    for i in range(1,len(all_restaurant_name)):
        total_score=0;rank_num=0
        #將五個人給分加起來
        for j in recommend_data:
            if(j[i]!=None):
                rank_num+=1
                total_score+=j[i]
        #五人都沒給分就跳過
        if(rank_num==0 or total_score==0):
            continue
        #算出平均
        final_rank=total_score/rank_num
        #如果已經有五間的話，比大小
        if(len(best_rest_rank)>=5):
            if(final_rank>min(best_rest_rank)):
                switch=best_rest_rank.index(min(best_rest_rank))
                best_rest_rank[switch]=final_rank
                best_rest_name[switch]=all_restaurant_name[i]
                
        else:
            best_rest_rank.append(final_rank)
            best_rest_name.append(all_restaurant_name[i])
    
    rest_id=[]
    #尋找店家id
    for name in best_rest_name:
        sql="SELECT id FROM restaurant_id WHERE name='{name}'".format(name=name)
        cursor.execute(sql)
        id=cursor.fetchall()
        rest_id.append(id[0][0])
        
    #關閉資料庫連線
    cursor.close()
    conn.close()
    
    data_for_web=[len(rest_id)]
    #再利用店家id尋找店家詳細資訊
    for id in rest_id  :
        url = "https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&language=zh-TW&key=AIzaSyCiDz6zKepKyIrKlfFeYYagsapLT1Xa7qw"\
            .format(place_id=id)
        payload={}
        headers = {}
        
        #抓取餐廳資訊並改成json格式
        ress = requests.request("GET", url, headers=headers, data=payload)
        ress.json()
        detail=json.loads(ress.text)
        data_web=['name','website','phone','rating','open','photo','photo','photo']
        try:
            data_web[0]=detail['result']['name'][:20]
        except KeyError:
            data_web[0]="無資料"
        try:
            data_web[1]=detail['result']['website']
        except KeyError:
            data_web[1]="無資料"
        try:
            data_web[2]=detail['result']['formatted_phone_number']
        except KeyError:
            data_web[2]="無資料"
        try:
            data_web[3]=detail['result']['rating']
        except KeyError:
            data_web[3]="無資料"
        try:
            data_web[4]=detail['result']['opening_hours']['open_now']
        except KeyError:
            data_web[4]="無資料"
        try:
            data_web[5]=detail['result']['photos'][0]['photo_reference']
        except KeyError:
            data_web[5]="無資料"
        try:
            data_web[6]=detail['result']['photos'][1]['photo_reference']
        except KeyError:
            data_web[6]="無資料"
        try:
            data_web[7]=detail['result']['photos'][2]['photo_reference']
        except KeyError:
            data_web[7]="無資料"
        
        data_web[1]="https://www.foodpanda.com.tw/" if data_web[1]=="無資料" else data_web[1]
        for i in range(5,8):
            #如果圖片不存在則利用指定圖片代替
            if(data_web[i]=="無資料"):
                data_web[i]=="https://media.istockphoto.com/vectors/open-source-concept-trendy-icon-simple-line-colored-illustration-vector-id1160220663"
            else:
                data_web[i]="https://maps.googleapis.com/maps/api/place/photo?maxwidth=300&maxheight=250&photo_reference={photo_id}&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A".format(photo_id=data_web[i])
        data_web[4]='營業中' if data_web[4]== True else '休息中'
        data_for_web.extend(data_web)
    data_for_web=str(data_for_web).strip('[]')
    return render_template("recommend.html",recommendData=data_for_web)


#line-bot
#抓User_id
def User_id(event):
    tmp=event.source
    tmp=str(tmp)
    userid_tmp=re.search(r'U[0-9a-f]{32}',tmp)
    tmp=str(userid_tmp.group())
    return tmp

#抓取經緯度
def message_location(event):
    lat = event.message.latitude
    lng = event.message.longitude
    return lat,lng

#把店家資料轉換成CarouselTemplate形式
def message_link(event):
    #無資料處理
    if(event[0]=='無資料'):
        event[0]='https://lh3.googleusercontent.com/places/AAcXr8reLx16i5Y9HkTVsmhB_kCiQvYk_k_PYB1vvfY9Rog_3D9hAA8glxHBhZ4N0Mk7yhnQMMlXGEsnBJHbWdI9DDfUrb0n47hFpzk=s1600-w400-h300'
    if(event[5]=='無資料'):
        event[5]='https://www.foodpanda.com.tw/?gclid=CjwKCAjwv-GUBhAzEiwASUMm4v5rWIn1SAkh0M6VH7aTcQxXFlXogwARYeKvbyOhOKrEmVz0-EK-mxoC7A4QAvD_BwE'
    
    return CarouselColumn(
                    thumbnail_image_url=event[0],
                    title=event[1],
                    text="評分: "+str(event[3])+"\n地址: "+event[2]+"\n狀態: "+event[6],
                    actions=[
                        MessageAction(
                            label='電話',
                            text=event[4]
                        ),
                        URIAction(
                            label='官網',
                            uri=event[5]
                        ),
                        URIAction(
                            label='foodpanda',
                            uri='https://www.foodpanda.com.tw/?gclid=CjwKCAjwv-GUBhAzEiwASUMm4v5rWIn1SAkh0M6VH7aTcQxXFlXogwARYeKvbyOhOKrEmVz0-EK-mxoC7A4QAvD_BwE'
                        )
                    ]
                )
# Channel Access Token
line_bot_api = LineBotApi('+2izojVo42xI0qEcngmy3CEbEdwfdysKyHDdNxkShWEFwnISXELa7qaZVev3enlz8pkybGwBgZsba+zWSYcasY0icwlv9ottrdblv6XbNXj3Q7uLl53Z0Q5XT5R+MRnw1wr+EnTjAEZBPdoM+nzmuAdB04t89/1O/w1cDnyilFU=')
#or line_bot_api = 'Channel_token'

# Channel Secret
handler = WebhookHandler('05c75e8423c5d95b16c066dd757b110c')
#or handler = 'Channel_secret'

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

#範例資料
a = [['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEBMCIF83CwJFEUEPcv0SIYt6uo4cIRtMEqfqjSxqAuvCkKrYXM2WxxtzLzrY7DZka5ULwliHAHrF_SFo3m39WeRMQYmWi1rGERR3psPDQA2hxYXk0xz1D9IrBGS41RfexKNKiprllAZBE9gYklsOGnN4zDtWiVo4CKkYDje_d_0P1oA&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '紅樓麻辣燙', '621台灣嘉義縣民雄鄉文化路4-2號', 4.4, '無資料', 'https://www.facebook.com/HongLouMaLaTang/', '營業中'],['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEAN0nO_h9o3AgbEMHH7mhtnMCGd_iiTcXMtBpGmbfMLpd-H4W-6baELvRkd_CWillGvq8UIPRKw3HgIdbrs_cadQ1RV-sqxOvNOkBMJunbrxsmTUPQytWpBseZRoA7nosbi4F0WZV-4LR75NsMloaXiea7GEKqqltEhzsHSH4hZH6Jm&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '蜀川麻辣鴛鴦鍋', '621台灣嘉義縣民雄鄉保生街197號', 4.3, '05 226 9183', 'http://hot-pot-restaurant-218.business.site/', '營業中'],['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEDKdV-KSPE1X5vdJJbovimqNmumYzVX4WS_yFGSjqcP9v7IoxSBjY7eClpLpIKer9MVNprFlSq9tkF4Dw6yJ2GAZBvXAVYSMqkENQIW1CL5IjO4rSZPui2o4-sE9MDOeYeXBP2GYC76Sg6732AGAz0hN7eoZ7jdd93-spWZNgJwDt9j&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '辛屋鴛鴦鍋物 民雄店', '621台灣嘉義縣民雄鄉保生街216號', 4.4, '05 206 0896', '無資料', '營業中'], ['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uECoRkDL-FGVcpmgW2Ec2N7RN-61fscvw5MYGn00bT-9kDP_qKmTIgqWc2NH3R-1KKKZjfXvricXu6cecGUAu0_aiFIAY8ui_1Dlcrp4f3zVoT-tjRiy5onTVH8nXd2xAC1m4M9xXNpkivZKEgSnlK73i6CI4_KHgao_KlRs20_bzBoM&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', 'Oppa川丸子麻辣燙-民雄文化直營店', '621台灣嘉義縣民雄鄉文化路30-19號', 3.9, '05 206 5657', 'https://www.facebook.com/pg/Oppa.Minxiong/posts/?ref=page_internal', '休息 中'], ['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEBmuGfz9_cc901DF3RdDB3tqJsyD1gYc-9ECfQLsU2Qt7laJDyuR0e9QdwLnae1T163elyqJsn0vwWMlsA3hjjlSSz21u0OQeuwhyLVN4Uvu3MX1vUe8nubvHWwX4erEzxStJeSFvS4aR0KbB7zSloYz9JM2RWWA0oCoWBRhg1JsBdo&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '鬼椒麻辣王', '621台灣嘉義縣民雄 鄉建國路二段415號附5', 4.2, '05 206 7158', 'http://www.bhutjolokia.com.tw/p/', '休息中'], ['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEDW_N12oIYE-EGAHjAs7ZYWpE4wMmj5nnIUqXuPfkQpPlMgVsrkcPxw52DqbJr3mlQAbql1SMrekv7JmTwbJhD7cKO80Af5Ug7Vcu9jYtVxYaVcbRN3URQtdlRbDHlaU0CSkYhzEUKBoTZTS3ji3teTO8FpdiuBvrdvynIuxI3pL7JL&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '川醉湘麻辣燙 嘉義民雄店', '621台灣嘉義縣民雄鄉保生街150之2號', 3.4, '無資料', '無資料', '休息中'], ['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEBEPx-cQl7XmZJUAfjEh5W98BPWMl0E0-_WRRDKjQAedOaZNMSkAAQrK77f0n0m9-VZBm6VuOuhq55fw-YiPyEawhteRlsCd2Bbyo4BAC4xzm7vRfqOERWyiRX9iPyPeeni4PtjudRn1k83C1CTwDkLFV-u5i6puvIpRtSixtf9ePPH&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '湯師父 美味鍋24Ｈ（嘉義民雄）', '621台灣嘉義縣民雄鄉建國路一段45號', 3.9, '05 226 5222', 'https://www.facebook.com/%E6%B9%AF%E5%B8%AB%E7%88%B6%E7%BE%8E%E5%91%B3%E9%8D%8B-%E5%98%89%E7%BE%A9%E6%B0%91%E6%97%8F%E5%BA%97-249701818510065', '營業中'], ['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEANOA92CmuQyjNwAjTO_FFReDHO7dOi_1fcQjdgcQtDKwSMyfg0ObCO2GqjHENRE_sKpdELYCz16XgDG9zKDOMXPDFZ7pE8NgjceuAPSZQLZr8R2fkmUNoM5UyyTCP1z4R037mqU5Vygj7O2_eglZHEzZjkKaPQy_Hdu1Qcz_rYhtZG&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '大呼過癮臭臭鍋(民雄店)民雄美食/民雄美食 ', '621台灣嘉義縣民雄鄉民溪南路369號之5號', 4.2, '05 226 2785', 'https://www.052262785.com/', '營業中'],['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEBHeuijJzYbK4hrZAibx7jLkLMy_LWIlpz0fjaluK1ZJN9wtqDBMYZCmyz6vu1LqgVeiwr8d5nwPiG8-CW9laUnLkCmDHdnkPhVxq5ZN8vQXLbhQygFKOv_mLss9vHCJG9pV3fOz-7QBcbC0l7YRHLhf_vGTQ4kWtKtyu8OTHfGMYe9&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '六扇門時尚 湯鍋 民雄保生店', '621台灣嘉義縣民雄鄉保生街211號', 4.2, '05 206 0900', '無資料', '營業中'], ['https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference=Aap_uEBxsroxEBhiI9uxSWyx37zGpwWWgXR3ZKMw1OMbrjWFs-pjPqPkMI_Fq643dQcnrfzOvsgfYbryOCjWqZcl2aCYbOjLw9V5cUr3K7PxxUhvwAbpqmw-wjqapzVshpedA96EavNuzSCr0XBA55zCQFzKB38zGk5tlzyzVO9v_olc9mke&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A', '米澤日式涮涮鍋', '621台灣嘉義縣民雄鄉保生街189號', 4.2, '05 226 9156', 'https://www.facebook.com/pages/%E6%B0%91%E9%9B%84%E7%B1%B3%E6%BE%A4%E7%81%AB%E9%8D%8B%E5%BA%97/188455917885224', '營業中']]
# 處理訊息
@handler.add(MessageEvent)
def handle_message(event):
    #如果是文字訊息則看使否有啟動字元
    try:
        tmp_text=event.message.text
        match = re.search(r'^(A|a){1}(ccount:){1}', tmp_text)
        recommend=re.search(r'^(R|r){1}(ecommend:){1}', tmp_text)
        record=re.search(r'^(R|r){1}(ecord){1}',tmp_text)
    except:
        pass
    #位置資訊則進入第一個if
    if(event.message.type == 'location'):
        #找出user_lineid
        user_id=User_id(event)
        
        #利用user_id找出user想被推薦的食物種類
        conn = psycopg2.connect(database_url,sslmode='require')
        cursor=conn.cursor()

        sql="SELECT favorite FROM user_data where line_userid='{user_id}' "\
            .format(user_id=user_id)
        cursor.execute(sql)
        favorite=cursor.fetchall()
        favorite=[list(i) for i in favorite]
        favorite=[i[0] for i in favorite]     
        
        #記得關閉資料庫連線
        cursor.close()
        conn.close()

        
        #獲取使用者現在經緯度
        lat,lng = message_location(event)
        #ap = "經度:{lat},緯度:{lng}".format(lat=lat,lng=lng)
        
        #尋找附近的店家
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude}, {longitude}&radius=2000&keyword='{keyword}'&language=zh-TW&key=AIzaSyCiDz6zKepKyIrKlfFeYYagsapLT1Xa7qw"\
            .format(latitude=lat,longitude=lng,keyword=favorite[0])
        payload={}
        headers = {}
        
        #尋找附近店家
        response = requests.request("GET", url, headers=headers, data=payload)
        response.json()
        res=json.loads(response.text)
        
        data_for_line=[]
        data_num=0
        
        #整理店家資料[照片連結,名稱,地址,評分,電話,官網,是否營業]
        for i in res['results']:
            if(data_num>=10):
                break
            url = "https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&language=zh-TW&key=AIzaSyCiDz6zKepKyIrKlfFeYYagsapLT1Xa7qw"\
                .format(place_id=i['place_id'])
            payload={}
            headers = {}

            ress = requests.request("GET", url, headers=headers, data=payload)
            ress.json()
            detail=json.loads(ress.text)

            #要給line的資料
            data_name=['photo_id','name','address','rating','phone_num','website','open']
            try:
                data_name[0]=detail['result']['photos'][0]['photo_reference']
            except KeyError:
                data_name[0]="無資料"
            try:
                data_name[1]=detail['result']['name'][:20]
            except KeyError:
                data_name[1]="無資料"
            try:
                data_name[2]=detail['result']['formatted_address']
            except KeyError:
                data_name[2]="無資料"
            try:
                data_name[3]=detail['result']['rating']
            except KeyError:
                data_name[3]="無資料"
            try:
                data_name[4]=detail['result']['formatted_phone_number']
            except KeyError:
                data_name[4]="無資料"
            try:
                data_name[5]=detail['result']['website']
            except KeyError:
                data_name[5]="無資料"
            try:
                data_name[6]=detail['result']['opening_hours']['open_now']
            except KeyError:
                data_name[6]="無資料"
            
            #找到圖片id後，要用google提供的api找出圖片
            data_name[0]="https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&maxheight=300&photo_reference={photo_id}&key=AIzaSyBx2V_QiQ5aXZlV5RxvPOUqC90B511Kv0A".format(photo_id=data_name[0])
            data_name[6]='營業中' if data_name[6]== True else '休息中'
            data_for_line.append(data_name)
            data_num+=1
        
        #傳入副函式並顯示在line中
        line_bot_api.reply_message( event.reply_token,TemplateSendMessage(
            alt_text='CarouselTemplate',
            template=CarouselTemplate(
            columns =[message_link(i) for i in data_for_line]
            )
        ))
         
    #match是設定使用者帳號的功能
    elif match:
        user_id=User_id(event)
        #資料庫連線
        conn = psycopg2.connect(database_url,sslmode='require')
        cursor=conn.cursor()
        
        #把資料整理到剩下帳號名稱的狀況
        tmp = tmp_text.lstrip('Aacount')
        tmp = tmp.lstrip(':')
        
        #從資料庫找出已經註冊的帳號
        sql="SELECT user_name FROM user_data"
        cursor.execute(sql)
        all_user_name=cursor.fetchall()
        
        #資料格式轉換一下
        all_user_name=[list(i) for i in all_user_name]
        all_user_name=[i[0] for i in all_user_name]
        
        #判斷使用者是否存在
        if (str(tmp) in all_user_name):
            #存在則新增line_userid
            sql="UPDATE user_data SET line_userid = '{user_id}' WHERE user_name='{user_name}'"\
                .format(user_id=user_id,user_name=tmp)
            cursor.execute(sql)
            conn.commit()
            return_text='success'
        else:
            return_text='小魔女最討厭來路不明的怪叔叔了'
            
        cursor.close()
        conn.close()
        message = TextSendMessage(text = return_text)
        line_bot_api.reply_message(event.reply_token, message)
        
    #recommend是設定使用者所偏好的食物種類
    elif recommend:
        #先找出使用者id
        user_id=User_id(event)
        
        #資料庫連線
        conn = psycopg2.connect(database_url,sslmode='require')
        cursor=conn.cursor()
        
        #整理資料，留下推薦風格就好
        tmp = tmp_text.lstrip('Rrecomend')
        tmp = tmp.lstrip(':')
        
        #從資料庫找出已經註冊的line_userid
        sql="SELECT line_userid FROM user_data"
        cursor.execute(sql)
        all_user_id=cursor.fetchall()
        
        #資料格式轉換一下
        all_user_id=[list(i) for i in all_user_id]
        all_user_id=[i[0] for i in all_user_id]
        
        #判斷userid是否存在
        if (str(user_id) in all_user_id):
            try:
                #存在則新增favorite
                sql="UPDATE user_data SET favorite = '{favorite}' WHERE line_userid='{user_id}'"\
                    .format(favorite=tmp,user_id=user_id)
                cursor.execute(sql)
                conn.commit()
                return_text='success'
            except:
                return_text=tmp
        else:
            #return_text='小魔女最討厭來路不明的怪叔叔了'
            return_text=all_userid
            
        cursor.close()
        conn.close()
        message = TextSendMessage(text = return_text)
        line_bot_api.reply_message(event.reply_token, message)
        
    #尋找過去飲食紀錄
    elif record:
        #先找出使用者user_id
        user_id=User_id(event)
        
        #利用id找出使用者名稱
        #資料庫連線
        conn = psycopg2.connect(database_url,sslmode='require')
        cursor=conn.cursor()
        
        sql="SELECT user_name FROM user_data WHERE line_userid='{user_id}'".format(user_id=user_id)
        cursor.execute(sql)
        user_name=cursor.fetchall()
        user_name=user_name[0][0]
        
        #找出名稱後再找出最近飲食紀錄，找最近10筆
        sql="SELECT * FROM history_eat WHERE user_name='{user_name}' ORDER BY day DESC LIMIT 10 ".format(user_name=user_name)
        cursor.execute(sql)
        record_data=cursor.fetchall()
        record_data=[list(i) for i in record_data]
        
        final_data=""
        for i in record_data:
            day=str(i[3])
            final_data+="日期 :{day}\n店家名稱 :{name}\n評分 :{rank}\n\n"\
                .format(day=day[:-6],name=i[1],rank=i[2])
        #關閉資料庫
        cursor.close()
        conn.close()
        
        message = TextSendMessage(text = final_data)
        line_bot_api.reply_message(event.reply_token, message)
        
    #資料==魔女食堂
    elif event.message.text == "魔女食堂":
        line_bot_api.reply_message( event.reply_token,TemplateSendMessage(
            alt_text='CarouselTemplate',
            template=CarouselTemplate(
            columns =[message_link(i) for i in a]
            )
        ))

if __name__ == 'main':
    app.run() #啟動伺服器
