from flask import Flask, render_template, request, redirect, url_for
import dropbox
import os

app = Flask(__name__)

# Dropbox 인증 정보 (환경 변수에서 가져오기 권장)
APP_KEY = os.getenv("APP_KEY", "gbgcgfcmt8h7mfi")  # Dropbox App Console → "App key"
APP_SECRET = os.getenv("APP_SECRET", "b38y7dtuflte4p5")  # Dropbox App Console → "App secret"
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN", "Jb1158wBIKIAAAAAAAAAAaLB5xPV5PMkoRKjBO-jNqsvoEgYO621xujGkBG5u69N")  # 리프레시 토큰

# Dropbox 클라이언트 초기화 (리프레시 토큰 사용)
dbx = dropbox.Dropbox(
    oauth2_refresh_token=REFRESH_TOKEN,
    app_key=APP_KEY,
    app_secret=APP_SECRET
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/grade")
def select_grade():
    group_type = request.args.get("type", "weekday")
    return render_template("grade.html", group_type=group_type)

@app.route("/students")
def student_list():
    group_type = request.args.get("type", "weekday")
    grade = request.args.get("grade", "중1")
    students = []
    try:
        _, res = dbx.files_download("/scores.txt")
        lines = res.content.decode("utf-8").splitlines()
        for line in lines:
            parts = line.strip().split(":")
            if len(parts) >= 5 and parts[2] == group_type and parts[3] == grade:
                students.append(f"{parts[0]} {parts[1]}")
    except:
        students = ["2025-04-21 홍길동"]
    return render_template("students.html", group_type=group_type, grade=grade, students=students)

@app.route("/score")
def scoring():
    name = request.args.get("name")
    date = request.args.get("date")
    correct_answers = []
    try:
        _, res = dbx.files_download("/scores.txt")
        lines = res.content.decode("utf-8").splitlines()
        for line in lines:
            parts = line.strip().split(":")
            if len(parts) >= 5 and parts[0] == date and parts[1] == name:
                correct_answers = parts[4].split("/")
                break
    except:
        correct_answers = ["1", "2", "3", "4", "5"]
    return render_template("score.html", name=name, date=date, answers=correct_answers)

@app.route("/submit", methods=["POST"])
def submit_score():
    name = request.form.get("name")
    date = request.form.get("date")
    group_type = request.form.get("group_type")
    grade = request.form.get("grade")
    user_answers = request.form.getlist("answers")

    correct_answers = []
    try:
        _, res = dbx.files_download("/scores.txt")
        lines = res.content.decode("utf-8").splitlines()
        for line in lines:
            parts = line.strip().split(":")
            if len(parts) >= 5 and parts[0] == date and parts[1] == name:
                correct_answers = parts[4].split("/")
                break
    except:
        pass

    wrong = []
    for i in range(len(correct_answers)):
        if i >= len(user_answers) or user_answers[i].strip() != correct_answers[i].strip():
            wrong.append(str(i + 1))

    result_entry = f"{date}:{name}:{group_type}:{grade}:{','.join(wrong) if wrong else '없음'}\n"
    try:
        content = ""
        try:
            _, res = dbx.files_download("/results.txt")
            content = res.content.decode("utf-8")
        except:
            pass
        content += result_entry
        dbx.files_upload(content.encode("utf-8"), "/results.txt", mode=dropbox.files.WriteMode.overwrite)
    except Exception as e:
        print("Dropbox 저장 실패:", e)

    return render_template("result.html", name=name, wrong=wrong)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
