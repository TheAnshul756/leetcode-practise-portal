from flask import Flask, render_template, request
import sqlite3
import os
import csv
import requests
import json
app = Flask(__name__, template_folder='templates')

graphql_url = "https://leetcode.com/graphql/"

cookieData = os.getenv("COOKIE")
if cookieData == "":
    sys.exit(1)
print(cookieData)

def get_db_connection():
    conn = sqlite3.connect('questions.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    print("creating table...")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problemId INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    isSolved INTEGER NOT NULL,
                    isLocked INTEGER NOT NULL,
                    UNIQUE (problemId)
                    );''')
    print('table created successfully')
    conn.commit()
    conn.close()

def add_question(problemId, title, isSolved, isLocked):
    result = get_question_from_datbase(problemId)
    conn = get_db_connection()
    c = conn.cursor()
    if result is None:
        c.execute("INSERT INTO questions (problemId, title, isSolved, isLocked) VALUES (?, ?, ?, ?)", (problemId, title, isSolved, isLocked))
        conn.commit()
        print("Question added successfully")
    else:
        c.execute("UPDATE questions SET title = ?, isSolved=?, isLocked=? WHERE problemId=?", (title, isSolved, isLocked, problemId))
        conn.commit()
        print("Question updated successfully")
    conn.close()


def get_question_from_datbase(problemId):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE problemId=?", (problemId,))
    question = c.fetchone()
    conn.close()
    return question

@app.route("/")
def list_companies():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    problems_dir = os.path.join(current_dir, "problems")
    companies = os.listdir(problems_dir)
    companies.sort()
    return render_template("companies.html", contents=companies)

def get_status(num):
    que = get_question_from_datbase(num)
    if que and (que[4] == 1 or que[3] == 1):
        return {
            'title' : que[2],
            'status' : 'ac' if que[3] == 1 else None,
            'paidOnly' : True if que[4] == 1 else False,
        }

    payload = json.dumps({
        "query": "\n    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {\n  problemsetQuestionList: questionList(\n    categorySlug: $categorySlug\n    limit: $limit\n    skip: $skip\n    filters: $filters\n  ) {\n    total: totalNum\n    questions: data {\n      acRate\n      difficulty\n      freqBar\n      frontendQuestionId: questionFrontendId\n      isFavor\n      paidOnly: isPaidOnly\n      status\n      title\n      titleSlug\n      topicTags {\n        name\n        id\n        slug\n      }\n      hasSolution\n      hasVideoSolution\n    }\n  }\n}\n    ",
        "variables": {
            "categorySlug": "all-code-essentials",
            "skip": num,
            "limit": 1,
            "filters": {}
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'cookie': cookieData
    }
    response = requests.request("POST", graphql_url, headers=headers, data=payload).json()
    response = response['data']['problemsetQuestionList']['questions']
    add_question(num, response[0]['title'], 1 if response[0]['status'] == 'ac' else 0, 1 if response[0]['paidOnly'] else 0)
    return response[0]

@app.route("/daily", methods=['GET', 'POST'])
def daily_questions():
    if request.method == 'GET':
        return render_template("daily.html")
    year = request.form.get('year')
    month = request.form.get('month')
    payload = json.dumps({
            "query": "\n    query dailyCodingQuestionRecords($year: Int!, $month: Int!) {\n  dailyCodingChallengeV2(year: $year, month: $month) {\n    challenges {\n      date\n      userStatus\n      link\n      question {\n        questionFrontendId\n        title\n        titleSlug\n      }\n    }\n    weeklyChallenges {\n      date\n      userStatus\n      link\n      question {\n        questionFrontendId\n        title\n        titleSlug\n        isPaidOnly\n      }\n    }\n  }\n}\n    ",
            "variables": {
                "year": year,
                "month": month
            }
        })
    headers = {
        'Content-Type': 'application/json',
        'cookie': cookieData
    }
    try:
        response = requests.request("POST", graphql_url, headers=headers, data=payload).json()
    except:
        return 'Something went wrong', 400
    questions = response['data']['dailyCodingChallengeV2']
    return render_template("daily.html", contents=questions['challenges'], weekly=questions['weeklyChallenges'])

@app.route("/problemChangeStatus/<questionId>")
def change_status(questionId):
    questionId = int(questionId)
    response = get_status(questionId - 1)
    response['status'] = 'ac' if response['status'] is None else None 
    add_question(questionId - 1, response['title'], 1 if response['status'] == 'ac' else 0, 1 if response['paidOnly'] else 0)
    return {'status': 'ok'}

@app.route("/problem/<questionId>")
def get_problem_detail(questionId):
    try:
        questionId = int(questionId)
    except:
        return 'question id is wrong', 400
    return get_status(int(questionId) - 1)

@app.route("/company/<name>")
def show_content(name):
    with open(f"problems/{name}", "r") as file:
        reader = csv.reader(file)
        data = list(reader)
    return render_template("problems.html", contents=data)

if __name__ == "__main__":
    create_db()
    app.run(host='0.0.0.0', port=3000)
