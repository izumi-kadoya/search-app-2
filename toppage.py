import os
from flask import Flask, render_template_string, request
from googleapiclient.discovery import build

# 環境変数からAPIキーとカスタム検索エンジンIDを取得
API_KEY = os.environ.get('GOOGLE_API_KEY')
CUSTOM_SEARCH_ENGINE_ID = os.environ.get('CUSTOM_SEARCH_ENGINE_ID')

app = Flask(__name__)


# APIにアクセスして結果を取得するメソッド
def get_search_results(query):
    search = build("customsearch", "v1", developerKey=API_KEY)
    result = search.cse().list(q=query, cx=CUSTOM_SEARCH_ENGINE_ID, lr='lang_ja', num=10, start=1).execute()
    return result

# 検索結果の情報を整理するメソッド
def summarize_search_results(result):
    result_items = []
    for item in result.get('items', []):
        result_items.append({
            'title': item['title'],
            'url': item['link'],
            'snippet': item['snippet']
        })
    return result_items

@app.route('/', methods=['GET', 'POST'])
def index():
    search_results = []
    if request.method == 'POST':
        # 3つの検索キーワードを取得
        query1 = request.form.get('search1', '')
        query2 = request.form.get('search2', '')
        query3 = request.form.get('search3', '')

        # 3つのキーワードを結合
        combined_query = f"{query1} {query2} {query3}".strip()

        # 結合したクエリで検索を実行
        if combined_query:  # 空でない場合のみ検索を実行
            result = get_search_results(combined_query)
            search_results = summarize_search_results(result)

    return render_template_string('''
    <!doctype html>
    <html>
    <head><title>Search with Google</title></head>
    <body>
        <form action="" method="post">
            <input type="text" name="search1" placeholder="Enter first query">
            <input type="text" name="search2" placeholder="Enter second query">
            <input type="text" name="search3" placeholder="Enter third query">
            <input type="submit" value="Search">
        </form>
        {% if search_results %}
            <ul>
            {% for item in search_results %}
                <li><a href="{{ item.url }}">{{ item.title }}</a> - {{ item.snippet }}</li>
            {% endfor %}
            </ul>
        {% endif %}
    </body>
    </html>
    ''', search_results=search_results)

if __name__ == '__main__':
    app.run(debug=True)