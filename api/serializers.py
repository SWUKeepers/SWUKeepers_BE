# serializers.py
from rest_framework import serializers
from .models import ChatRoom, Message
from datetime import datetime


class ChatRoomSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(required=False)

    class Meta:
        model = ChatRoom
        fields = ("room_name", "saved_at")

    def create(self, validated_data):
        request = self.context.get("request")  # 요청 객체 가져오기
        file = request.FILES.get("file")  # 파일을 가져오기

        if not file:
            raise serializers.ValidationError("File is missing or could not be found.")

        # 파일에서 room_name 추출
        room_name = self.extract_room_name(file)
        if not room_name:
            raise serializers.ValidationError(
                "Room name could not be extracted from the file."
            )

        # ChatRoom 저장
        chat_room = ChatRoom.objects.create(room_name=room_name)

        # 파일 파싱 및 메시지 저장 처리
        sentences = self.parse_file(file, chat_room)

        return chat_room,sentences
    
    def extract_room_name(self, file):
        file.seek(0)  # 파일 포인터를 처음으로 이동
        first_line = file.readline().decode("utf-8").strip()
        return first_line

    def parse_file(self, file, chat_room):
        sentences = []
        for line in file:
            try:
                line = line.decode("utf-8").strip()
                if line.startswith("["):  # 메시지 포맷 확인
                    sender_end_idx = line.index("]") + 1
                    time_end_idx = line.index("]", sender_end_idx) + 1
                    sender = line[1 : sender_end_idx - 1]
                    time_sent = line[sender_end_idx + 2 : time_end_idx - 1]
                    content = line[time_end_idx + 2 :]

                    # 한국어 오전/오후 변환
                    if "오전" in time_sent:
                        time_sent = time_sent.replace("오전", "AM")
                    elif "오후" in time_sent:
                        time_sent = time_sent.replace("오후", "PM")

                    # 시간 파싱
                    time_sent = datetime.strptime(time_sent, "%p %I:%M").time()

                    # 메시지 생성 및 ChatRoom과 연결
                    Message.objects.create(
                        chat_room=chat_room,
                        sender=sender,
                        time_sent=datetime.combine(datetime.today(), time_sent),
                        content=content,
                    )


                    # 각 메시지를 sentences 리스트에 추가
                    sentences.append(content)

            except Exception as e:
                print(f"Error parsing line '{line}': {e}")
        return sentences