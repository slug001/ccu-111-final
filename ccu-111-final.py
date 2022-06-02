from flask import Flask, request,render_template
import requests
import json
import psycopg2
import math
database_url='postgres://zlujzrtgrbvpgb:ba830f737f30a8309677d917becefb9295f1956a8521b478604e3e4e54c76bb1@ec2-54-165-90-230.compute-1.amazonaws.com:5432/d64qh26kv7tm2k'

app = Flask(__name__)


@app.route('/', methods=['GET','POST'])
def home():
    if request.method =='GET':
        #抓取使用者資料
        """
        conn = psycopg2.connect(database_url,sslmode='require')
        cursor=conn.cursor()
        sql="SELECT * FROM restaurant_data "
        cursor.execute(sql)
        all_data=cursor.fetchall()
        cursor.close()
        conn.close()
        all_data=json.dumps(all_data)
        """
        return render_template("home.html")
    else:
        #user_position=request.values['input']

        #抓取資料
        user_name=request.values['user_name']
        restaurant_name=request.values['restaurant_name']
        rank=request.values['rank']

        #資料庫連線
        conn = psycopg2.connect(database_url,sslmode='require')
        cursor=conn.cursor()
        
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
            return render_template("home.html",repeat='same_name success')
       
        cursor.close()
        conn.close()
        
        if(1):
            return render_template("home.html",repeat=all_restaurant_name)
        else:
            return render_template("home.html",repeat='false')


@app.route("/login", methods=['GET','POST'])
def login():
    
    user_name=request.values['new_user_name']
    user_password=request.values['new_password']
    #資料庫連線
    
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

#推薦系統
@app.route("/recommend", methods=['GET','POST'])
def recommend():
    name=request.values['search_name']
    
    #先抓取資料庫的資料
    conn = psycopg2.connect(database_url,sslmode='require')
    cursor=conn.cursor()

    sql="SELECT * FROM restaurant_data "
    cursor.execute(sql)
    all_data=cursor.fetchall()
    
    sql="SELECT * FROM restaurant_data WHERE user_name='{user_name}'".format(user_name=name)
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

    #計算目標資料和其他資料的餘弦相似度
    #並找出最相近的五位使用者，在近一步找出共同喜歡的餐廳
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
            """
            for j in range(len(max_cos)):        
                if(final_cos>max_cos[j]):
                    max_cos[j]=final_cos
                    max_name[j]=i[0]
                    break
            """
        elif(other_len>0 and all_cos>0):
            max_cos.append(final_cos)
            max_name.append(i[0])
            
    #找出相似的後再找出資料庫中的評分資料
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
            
    #關閉資料庫連線
    cursor.close()
    conn.close()
    return render_template("home.html",recommend=best_rest_name)


if __name__ == 'main':
    app.run() #啟動伺服器
