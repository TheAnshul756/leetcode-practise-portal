from flask import Flask, render_template
import os
import csv
import requests
import json

app = Flask(__name__, template_folder='templates')

graphql_url = "https://leetcode.com/graphql/"

with open("cookies.txt", "r") as file:
        cookieData = file.readline()

@app.route("/")
def list_companies():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    problems_dir = os.path.join(current_dir, "problems")
    companies = os.listdir(problems_dir)
    companies.sort()
    return render_template("companies.html", contents=companies)

def get_status(num):
    payload = json.dumps({
        "query": "\n    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {\n  problemsetQuestionList: questionList(\n    categorySlug: $categorySlug\n    limit: $limit\n    skip: $skip\n    filters: $filters\n  ) {\n    total: totalNum\n    questions: data {\n      acRate\n      difficulty\n      freqBar\n      frontendQuestionId: questionFrontendId\n      isFavor\n      paidOnly: isPaidOnly\n      status\n      title\n      titleSlug\n      topicTags {\n        name\n        id\n        slug\n      }\n      hasSolution\n      hasVideoSolution\n    }\n  }\n}\n    ",
        "variables": {
            "categorySlug": "",
            "skip": num,
            "limit": 1,
            "filters": {}
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'Cookie': cookieData
    }
    response = requests.request("POST", graphql_url, headers=headers, data=payload).json()
    response = response['data']['problemsetQuestionList']['questions']
    return response[0]

@app.route("/problem/<questionId>")
def get_problem_detail(questionId):
    return get_status(int(questionId) - 1)

@app.route("/company/<name>")
def show_content(name):
    with open(f"problems/{name}", "r") as file:
        reader = csv.reader(file)
        data = list(reader)
    return render_template("problems.html", contents=data)

if __name__ == "__main__":
    app.run()
