import re
from .models import ChatRoom, Message
from django.utils import timezone

def parse_kakao_file(file, room_name):
    """
    카카오톡 내보내기 파일을 파싱하고, 채팅방과 메시지 인스턴스를 반환합니다.
    """

    messages = []
    pattern = r"(\d{4}-\d{2}-\d{2}) (오전|오후) (\d{1,2}:\d{2}), (.*?): (.*)"
    file.seek(0)

    for line in file:
        line = line.decode("utf-8").rstrip("\n") # 파일을 디코딩

        match = re.match(pattern, line)
        if match:
            date, am_pm, time, sender, content = match.groups()
            # 전송 시간 및 날짜 조합
            time_format = f"{date} {am_pm} {time}"
            time_sent = timezone.datetime.strptime(time_format, "%Y-%m-%d %p %I:%M")
            
            messages.append({
                "sender": sender,
                "time_sent": time_sent,
                "content": content
            })

        else:
            print(f"Parsing issue with line: {line}")  # 디버깅용 메시지

    
    # 채팅방 인스턴스 생성 (또는 가져오기)
    chat_room, created = ChatRoom.objects.get_or_create(room_name=room_name)
    return chat_room, messages