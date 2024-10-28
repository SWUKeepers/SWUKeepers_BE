import os
import hashlib
from datetime import datetime
from rest_framework import serializers
from .models import ChatRoom, Message, TextFile

class ChatRoomSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(required=False)

    class Meta:
        model = ChatRoom
        fields = ("room_name", "saved_at")

    def create(self, validated_data):
        request = self.context.get("request")
        file = request.FILES.get("file")

        if not file:
            raise serializers.ValidationError("File is missing or could not be found.")

        # 카카오톡 내보내기 형식 검사
        if not self.is_valid_kakao_format(file):
            raise serializers.ValidationError(
                {"detail": "Only KakaoTalk export files are allowed."}
            )

        # 파일 해시 계산
        file_hash = self.calculate_file_hash(file)

        # 해시 중복 체크
        if TextFile.objects.filter(file_hash=file_hash).exists():
            raise serializers.ValidationError(
                {"detail": "This file has already been uploaded."}
            )

        # 파일 저장
        text_file = TextFile.objects.create(file=file, file_hash=file_hash)

        # 파일에서 room_name 추출
        room_name = self.extract_room_name(file)
        if not room_name:
            raise serializers.ValidationError(
                {"detail": "Room name could not be extracted from the file."}
            )

        # ChatRoom 저장 및 파일 파싱
        chat_room = ChatRoom.objects.create(room_name=room_name)
        self.parse_file(file, chat_room)

        return chat_room

    def is_valid_kakao_format(self, file):
        """파일에 '저장한 날짜'와 '[이름] [시간]' 형식이 포함되어 있는지 확인합니다."""
        file.seek(0)  # 파일 포인터를 처음으로 이동
        lines = [line.decode("utf-8").strip() for line in file]

        # '저장한 날짜'가 포함된 줄이 있는지 확인
        has_saved_date = any("저장한 날짜" in line for line in lines)

        # '[이름] [시간]' 형식을 포함한 줄이 있는지 확인
        has_name_time_format = any(
            "[" in line and "]" in line and line.count("[") >= 2 for line in lines
        )

        # 디버그 로그 출력 (선택 사항)
        print(f"저장한 날짜 포함 여부: {has_saved_date}")
        print(f"[이름] [시간] 형식 포함 여부: {has_name_time_format}")

        # 두 조건을 모두 만족해야 통과
        return has_saved_date and has_name_time_format

    def calculate_file_hash(self, file):
        """파일의 해시 값을 계산합니다."""
        hasher = hashlib.sha256()
        file.seek(0)  # 파일 포인터를 처음으로 이동
        for chunk in file.chunks():
            hasher.update(chunk)
        file.seek(0)  # 파일 포인터를 다시 처음으로 이동
        return hasher.hexdigest()

    def extract_room_name(self, file):
        """파일에서 채팅방 이름을 추출합니다."""
        file.seek(0)  # 파일 포인터를 처음으로 이동
        first_line = file.readline().decode("utf-8").strip()
        return first_line.split(":")[-1].strip()

    def parse_file(self, file, chat_room):
        """파일을 파싱하여 메시지를 생성합니다."""
        for line in file:
            try:
                line = line.decode("utf-8").strip()
                if line.startswith("["):  # 메시지 포맷 확인
                    sender_end_idx = line.index("]") + 1
                    time_end_idx = line.index("]", sender_end_idx) + 1
                    sender = line[1:sender_end_idx - 1]
                    time_sent = line[sender_end_idx + 2:time_end_idx - 1]
                    content = line[time_end_idx + 2:]

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
            except Exception as e:
                print(f"Error parsing line '{line}': {e}")
