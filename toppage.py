import os
import openai
from flask import Flask, render_template_string, request
from googleapiclient.discovery import build

# 環境変数からAPIキーとカスタム検索エンジンID、OpenAI APIキーを取得
API_KEY = os.environ.get('GOOGLE_API_KEY')
CUSTOM_SEARCH_ENGINE_ID = os.environ.get('CUSTOM_SEARCH_ENGINE_ID')
OPENAI_API_SECRET_KEY = os.environ.get('OPENAI_API_SECRET_KEY')

app = Flask(__name__)

# OpenAIのAPIを利用してタイトルが同じ出来事を指しているか判断する関数
def is_duplicate(title1, title2):
    openai.api_key = OPENAI_API_SECRET_KEY
    prompt = f"Determine if the following two news titles are about the same event.\nTitle 1: \"{title1}\"\nTitle 2: \"{title2}\"\nAre they about the same event?"
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": ""}
        ],
        max_tokens=60
    )
    answer = response.choices[0].message['content'].strip().lower()
    return "yes" in answer

# 重複除去ロジック
def remove_duplicates(search_results):
    unique_results = []
    for result in search_results:
        if not any(is_duplicate(result['title'], existing_result['title']) for existing_result in unique_results):
            unique_results.append(result)
    return unique_results

# APIにアクセスして結果を取得するメソッド
def get_search_results(query):
    search = build("customsearch", "v1", developerKey=API_KEY)
    # 最初の10件の検索結果を取得
    result1 = search.cse().list(q=query, cx=CUSTOM_SEARCH_ENGINE_ID, lr='lang_ja', num=10, start=1).execute()
    items1 = result1.get('items', [])

    # 次の10件の検索結果を取得
    result2 = search.cse().list(q=query, cx=CUSTOM_SEARCH_ENGINE_ID, lr='lang_ja', num=10, start=11).execute()
    items2 = result2.get('items', [])

    # 両方の結果を結合
    return items1 + items2


# 検索結果の情報を整理するメソッド
def summarize_search_results(items):
    result_items = []
    for item in items:
        result_items.append({
            'title': item['title'],
            'url': item['link'],
            'snippet': item['snippet']
        })
    return result_items

@app.route('/', methods=['GET', 'POST'])
def index():
    raw_search_results = []
    unique_search_results = []  
    if request.method == 'POST':
        keyword1 = request.form.get('keyword1', '')
        keyword2 = request.form.get('keyword2', '')
        keyword3 = request.form.get('keyword3', '')
        period = request.form.get('period', 'all')

        if period == '3months':
            combined_query = f"{keyword1} {keyword2} {keyword3} news after:3m".strip()
        elif period == '6months':
            combined_query = f"{keyword1} {keyword2} {keyword3} news after:6m".strip()
        elif period == '12months':
            combined_query = f"{keyword1} {keyword2} {keyword3} news after:12m".strip()
        else:
            combined_query = f"{keyword1} {keyword2} {keyword3} news".strip()
        
        raw_results = get_search_results(combined_query)
        raw_search_results = summarize_search_results(raw_results)
        unique_search_results = remove_duplicates(raw_search_results)

    return render_template_string('''
<!doctype html>
<html>
<head>
    <title>Search with Google</title>
    <style>
        #loading {
            display: none;
            color: blue;
            font-size: 20px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <form id="searchForm" method="post">
        Keyword 1: <input type="text" name="keyword1"><br>
        Keyword 2: <input type="text" name="keyword2"><br>
        Keyword 3: <input type="text" name="keyword3"><br>
        Period:
        <select name="period">
            <option value="all">All Periods</option>
            <option value="3months">Last 3 Months</option>
            <option value="6months">Last 6 Months</option>
            <option value="12months">Last 12 Months</option>
        </select><br>
        <input type="submit" value="Search">
    </form>

    <div id="loading">loading...</div>

    <h2>Unique Results (Duplicates Removed)</h2>
    <div style="border: 1px solid #ddd; margin-bottom: 20px;">
        {% if unique_search_results %}
            <ul>
            {% for item in unique_search_results %}
                <li><a href="{{ item.url }}">{{ item.title }}</a> <br>- {{ item.snippet }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No unique results found.</p>
        {% endif %}
    </div>

    <h2>All Results (Before Removing Duplicates)</h2>
    <div style="border: 1px solid #ddd;">
        {% if raw_search_results %}
            <ul>
            {% for item in raw_search_results %}
                <li><a href="{{ item.url }}">{{ item.title }}</a> <br>- {{ item.snippet }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No results found.</p>
        {% endif %}
    </div>

    <script>
        document.getElementById('searchForm').onsubmit = function() {
            document.getElementById('loading').style.display = 'block';
        };
    </script>
</body>
</html>

    ''', unique_search_results=unique_search_results, raw_search_results=raw_search_results)

if __name__ == '__main__':
    app.run(debug=True)
