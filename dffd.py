import qrcode
import time
import uuid
import csv
from flask import Flask, request, jsonify, render_template_string
from threading import Thread
from datetime import datetime

app = Flask(__name__)

# 출석 데이터 저장 파일
ATTENDANCE_FILE = "attendance.csv"
current_code = None  # 🔹 전역 변수 초기화

def generate_qr():
    """1분마다 새로운 QR 코드를 생성하는 함수"""
    global current_code
    while True:
        unique_code = str(uuid.uuid4())  # 고유 코드 생성
        qr = qrcode.make(f"http://localhost:5000/attendance?code={unique_code}")
        qr.save("current_qr.png")
        print(f"새로운 QR 코드 생성됨: {unique_code}")
        current_code = unique_code  # 🔹 전역 변수에 저장
        time.sleep(60)  # 1분마다 새 QR 코드 생성

@app.route("/attendance", methods=["GET", "POST"])
def record_attendance():
    """QR 코드를 스캔하면 학번과 이름을 입력할 수 있도록 하는 함수"""
    global current_code

    if request.method == "GET":
        code = request.args.get("code")

        # 🔹 QR 코드가 아직 생성되지 않은 경우 예외 처리
        if current_code is None:
            return "QR 코드가 아직 생성되지 않았습니다. 잠시 후 다시 시도해주세요.", 400

        if code != current_code:
            return "QR 코드가 만료되었습니다.", 400

        return render_template_string('''
            <form action="/attendance" method="post">
                <input type="hidden" name="code" value="{{ code }}">
                학번: <input type="text" name="student_id" required><br>
                이름: <input type="text" name="student_name" required><br>
                <input type="submit" value="출석 확인">
            </form>
        ''', code=code)
    
    elif request.method == "POST":
        code = request.form.get("code")
        student_id = request.form.get("student_id")
        student_name = request.form.get("student_name")

        # 🔹 QR 코드가 아직 생성되지 않았거나 유효하지 않은 경우 예외 처리
        if current_code is None or code != current_code:
            return "QR 코드가 만료되었거나 아직 생성되지 않았습니다.", 400

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(ATTENDANCE_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([student_id, student_name, timestamp])

        return f"출석 확인됨: {student_id} - {student_name} ({timestamp})"

if __name__ == "__main__":
    # 백그라운드에서 QR 코드 생성 스레드 실행
    qr_thread = Thread(target=generate_qr)
    qr_thread.daemon = True
    qr_thread.start()

    # Flask 서버 실행
    app.run(debug=True)
