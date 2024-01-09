from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import requests, random, re
from bs4 import BeautifulSoup
import pandas as pd
import pyodbc
import openai
app = Flask(__name__)
app.static_folder = 'static'
bcrypt = Bcrypt()
app.config['SECRET_KEY'] = '0]w;vPTLan+Nt!j$blUzw@5:R~u)~_'
openai.api_key = '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'
'''
#Mysql
db = SQLAlchemy()
user = "DevAuth"
pin = "Dev127336"
host = "localhost"
db_name = "DevDb"
# Configuring database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{user}:{pin}@{host}/{db_name}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
'''
#sql server
SERVER = 'localhost,1400'
DATABASE = 'master'
USERNAME = 'sa'
PASSWORD = 'Passw0rd'
connectionString = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

# 设置 SQLALCHEMY_DATABASE_URI，连接到 SQL Server
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={connectionString}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email))

def fetch_news_content(url):
    user_agents = user_agents = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
        ]
    headers = {"user-agent": random.choice(user_agents)}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "lxml")
    # 抓取标题    
    '''title_elem = soup.select_one('head title')'''
    news_title = soup.title.string if soup.title else None
    '''news_title = title_elem.text if title_elem else None'''
    # 抓取内容  
    elem = soup.select('.story')
    content = []
    for e in elem:
        paragraphs = e.find_all('p', class_=False)
        paragraphs = [p for p in paragraphs if not p.find('strong')]
        for paragraph in paragraphs:
            content.append(paragraph.text)
    content_text = ' '.join(content)

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="幫我精簡內容500字:" + content_text,
        max_tokens=900,
        temperature=0.5,
    )
    completed_text = response["choices"][0]["text"]      
    return news_title, completed_text

class sign_up(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(500), nullable=False)
    password = db.Column(db.String(500), nullable=False)

    
@app.route('/', methods=['POST', 'GET'])
def login_page():
    error_message = None
    if request.method == 'POST':
        user_name = request.form.get('username')
        user_password = request.form.get('password')
        user = sign_up.query.filter_by(name=user_name).first()
        if user and bcrypt.check_password_hash(user.password, user_password):
            session['username'] = user_name
            return redirect(url_for('main_page'))
        else:
            error_message = 'Invalid username or password'
            return render_template('login.html', error_message=error_message)      
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup_page():
    warning_message = None
    if request.method == 'POST':
        
        user_name = request.form.get('username')
        user_email = request.form.get('email')       
        user_password= request.form.get('password')
        if user_name == '' or user_email == '' or user_password == '' or is_valid_email(user_email) == 0:
           warning_message = 'Please fill in required fields'
           return render_template('signup.html', warning_message = warning_message) 

        else:
            hashed_password = bcrypt.generate_password_hash(user_password).decode('utf-8')
            add_detail = sign_up (
                name = user_name,
                email = user_email,
                password = hashed_password
            )
            db.session.add(add_detail)
            db.session.commit()
            return redirect(url_for('login_page'))  # 可以改為重新導向到成功頁面或其他操作

    return render_template('signup.html')

@app.route('/main', methods=['POST', 'GET'])
def main_page():        
    user_name = session.get('username')
    
    return render_template('main.html', username=user_name)

@app.route('/fetch_news', methods=['GET', 'POST'])
def fetch_news():
    request_data = request.get_json()
    selected_value = request_data.get('selected_value') 
    url = "https://www.ettoday.net/news/news-list.htm"

    user_agents = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    ]
    headers = {
        "user-agent":random.choice(user_agents)
    }
    resp =requests.get(url, headers = headers)
    soup = BeautifulSoup(resp.text,"lxml")
    elem = soup.select(".part_list_2")

    title_list = []
    date_list = []
    cate_list = []
    link_list = []

    specific_category_title_list = []
    specific_category_link_list = []
    specific_category_date_list = []
    specific_category_cate_list = []

    if selected_value != '全部':
        for e in elem:
            
            titles = [title.text for title in e.select("a")]
            links = [i.get('href') for i in e.select("a")]
            dates = [date.text for date in e.select(".date")]
            cates = [cate.text for cate in e.select("em")]

            for title, link, date, cate in zip(titles, links, dates, cates):
                if selected_value in cate:  # 修改为你感兴趣的特定类别
                    specific_category_title_list.append(title)
                    specific_category_link_list.append(link)
                    specific_category_date_list.append(date)
                    specific_category_cate_list.append(cate)   
    
        df = pd.DataFrame({
        "title": specific_category_title_list,
        "link": specific_category_link_list,
        "date": specific_category_date_list,
        "category": specific_category_cate_list
        })
        return jsonify(df.to_dict('records'))
    else:
        for e in elem:
            
            titles = [title.text for title in e.select("a")]
            links = [i.get('href') for i in e.select("a")]
            dates = [date.text for date in e.select(".date")]
            cates = [cate.text for cate in e.select("em")]
            
            title_list.extend(titles)
            link_list.extend(links)
            date_list.extend(dates)
            cate_list.extend(cates)
            
        df = pd.DataFrame({
           "title": title_list,
            "link": link_list,
            "date": date_list,
            "category": cate_list 
        })
        return jsonify(df.to_dict('records'))
    

@app.route('/fetch_content', methods=['GET', 'POST'])
def fetch_content():
    request_data = request.get_json()
    news_url = request_data.get('url')

    # 使用 fetch_news_content 函數抓取新聞內容
    news_title, news_content = fetch_news_content(news_url)
    return jsonify({
        
        'title' : news_title,
        'content': news_content
        })

@app.route('/modify', methods=['GET', 'POST'])
def modify_page():
    if request.method == 'POST':
        user_name = request.form.get('username')
        user_email = request.form.get('email')    
        old_password = request.form.get('old_password')   
        new_password = request.form.get('password')
        
        if user_name == '' or user_email == '' or new_password == '' or old_password == '' or is_valid_email(user_email) == 0:
            warning_message = 'Please fill in required fields'
            return render_template('modify.html', warning_message=warning_message) 
        else:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            
            # 寻找用户
            user = sign_up.query.filter_by(email=user_email).first()
            
            if user :
                # 更新密码
                if bcrypt.check_password_hash(user.password, old_password) and old_password != new_password:
                    user.password = hashed_password
                    db.session.commit()
                    return redirect(url_for('login_page')) 
                    # 重定向到成功页面或其他操作
                else:
                    warning_message = 'password error'
                    return render_template('modify.html', warning_message = warning_message)
            else:
                warning_message = user
                return  render_template('modify.html', warning_message = warning_message)#render_template('signup.html', error_message=error_message)
    return render_template('modify.html')


if __name__ == "__main__":
    app.run(debug=True)
