"""同じディレクトリのCSVファイルをMySQLに挿入する
手順
1. google スプレッドシート
2. Numbers貼り付け
3. csvファイルに書き出す
4. 3.をinsert_csv.pyと同じディレクトリにおく
※3→4でカンマが生成される

# HACK:jrfoodadv/csv/insert_csv.pyとはほぼ同じ内容。
しかしながら重複してデータが挿入されることを防ぐため以下のことで制御しておく。
違うところは、
1. cursor.executeするところのカラム名の違い
2. os.environ['csv_file'] のファイル名の違い
"""

import csv
import os
import MySQLdb
from dotenv import load_dotenv

load_dotenv()

# 接続準備
connection = MySQLdb.connect(
    db='foodtech',
    user=os.environ['MYSQL_USER'],
    passwd=os.environ['MYSQL_PASSWORD'],
    host=os.environ['DATABASES_HOST'],
    port=3306,
    charset='utf8mb4',
)

# 接続確認
cursor = connection.cursor()
# SQL実行
# sql = cursor.execute(
#     # "select * from jr_food_labeling_advise_question;"
# )
# data = cursor.fetchall()
# for item in data:
#     print(item)

csv_file = os.environ['food_labeling_csv_file']
with open(csv_file, 'r') as file:
    EXE_CNT = 0
    rows = csv.reader(file)
    header = next(rows) # 1行目をスキップ
    search_same_num_list = []
    for row in rows:

        # MySQLのPKでも発動できるば、念の為もし重複した文字列があったらbreak
        if row in search_same_num_list:
            print('重複した文字列が見つかりました。')
            break
        search_same_num_list.append(row)

        # SQLの実行
        cursor.execute(
            'INSERT INTO food_labeling_advise_question (\
                question_id,\
                original_data,\
                original_data_num,\
                textbook_chapter,\
                question_title,\
                sub_question_title,\
                question_type,\
                question_img,\
                choice_a,\
                choice_b,\
                choice_c,\
                choice_d,\
                correct_answer,\
                commentary,\
                created_at,\
                updated_at\
                ) VALUES (\'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\',\
                        \'{}\'\
                );'\
                .format(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    row[12],
                    row[13],
                    row[14],
                    row[15]
                    )
        )

        EXE_CNT += 1
        print('%s回目の処理を実行しました。' % EXE_CNT)

connection.commit() # 更新の確定
connection.close() # 接続解除
