import random

# db.py

import pymysql
from config import movie_db, news_db

def get_connection():
    return pymysql.connect(**movie_db)

def get_latest_news(limit=5):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT title, url FROM news ORDER BY publish_time DESC LIMIT %s", (limit,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_latest_movies(limit=20):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT title,intro,douban_score,imdb_score,`year`,duration FROM heaven_movie where douban_score >7.5 and imdb_score >6.5 LIMIT %s", (limit,))
    result = cursor.fetchall()

    sent_titles = get_movie_sended()  # 获取已发送电影标题集合

    while True:
        num_one = result[random.randint(0, len(result) - 1)]  # 随机选一个
        if num_one['title'] not in sent_titles:
            break  # 不在集合中，跳出循环

    # 插入到 movies_sended 表中
    insert_sql = "INSERT INTO movies_sended (title,send_time) VALUES (%s,now())"
    cursor.execute(insert_sql, (num_one['title']))
    conn.commit()  # 提交事务
    conn.close()
    print(num_one)
    return num_one

def get_movie_sended():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT title FROM movies_sended")
    result = cursor.fetchall()
    movies_set = set()
    for i in result:
        movies_set.add(i['title'])
    conn.close()
    return movies_set
def search_content(keyword):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT '新闻' AS type, title, url FROM news WHERE title LIKE %s
        UNION
        SELECT '电影' AS type, title, '' FROM movies WHERE title LIKE %s
        LIMIT 10
    """, (f'%{keyword}%', f'%{keyword}%'))
    result = cursor.fetchall()
    conn.close()
    return result

get_latest_movies()