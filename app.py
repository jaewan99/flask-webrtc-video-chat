from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, send, disconnect
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


# 현재 생성된 방들
rooms = {}



@app.route('/<room_id>')
def room(room_id,):
    
    session["room"] = room_id
    
    # 입력한 room_id가 rooms에 없으면 새로운 방 생성
    if room_id not in rooms:
        rooms[room_id] = {"members" : 0, "userIDs":{}}
    
    return render_template("room.html", room_id=room_id, username = "userFound")


@socketio.on("join")
def handle_join(data):
    user_id = session.get("user")
    room_id = session.get("room")

    rooms[room_id]["userIDs"][user_id] = request.sid
    
    # 자바스크립트에서 전달된 데이터 가져오기 (룸 ID)
    room = data["room"]

    # 현재 세션 ID
    user_id = request.sid

    # 클라이언트 연결을 위해 소켓에서 방 참여 - 추후 아무도 없을때 방 삭제
    join_room(room)

    # 생성된 방의 인원 수 1명 증가
    rooms[room]["members"] += 1

    # 자바스크립트 " socketio.on("user-joined.."로 이동 // 현재 들어온 유저 제외 모든 사람한테 전달
    emit("user-joined", {"userId": user_id}, room=room, include_self=False)


# A 유저에서 B 유저한테 signal - offer / answer / ICE 전송
@socketio.on("signal")
def handle_signal(data):
    to_user = data["to"]
    emit("signal", {**data, "from": request.sid}, room=to_user)

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": "Unknown",
        "message": data["data"]
    }
    send(content, to=room)

# 이게 있어야 disconnect 작동가능 - 소켓 서버 열결 코드는 "join"
@socketio.on("connect")
def connect():
    return

@socketio.on("disconnect")
def disconnect():
    room = session.get('room')
    leave_room(room)
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    user_id = request.sid
    emit("user-left", {"userId": user_id}, room=room)   


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, ssl_context="adhoc")