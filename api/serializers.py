import os
import hashlib
from datetime import datetime
from django.conf import settings
from rest_framework import serializers
from .models import ChatRoom, Message, TextFile
import re
from .Kakao_parse import KakaoChatParser


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

        # 카카오톡 파일 형식 검증
        if not self.validate_kakao_chat_format(file):
            raise serializers.ValidationError(
                "카카오톡으로 내보내기 한 파일이 맞는지 확인해주세요!"
            )  # 커스텀 메시지 반환

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

        # 파일 파싱 및 메시지 저장 처리
        self.parse_file(file, chat_room)

        return chat_room

    def calculate_file_hash(self, file):
        """파일의 해시 값을 계산합니다."""
        hasher = hashlib.sha256()
        file.seek(0)  # 파일 포인터를 처음으로 이동
        for chunk in file.chunks():
            hasher.update(chunk)
        file.seek(0)  # 파일 포인터를 다시 처음으로 이동
        return hasher.hexdigest()

    def extract_room_name(self, file):
        file.seek(0)  # 파일 포인터를 처음으로 이동
        first_line = file.readline().decode("utf-8").strip()
        return first_line.split(":")[-1].strip()

    def save_file_locally(self, file):
        file_name = file.name
        file_path = os.path.join(settings.MEDIA_ROOT, "uploads", file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    def parse_file(self, file, chat_room):
        for line in file:
            try:
                line = line.decode("utf-8").strip()
                if line.startswith("["):
                    sender_end_idx = line.index("]") + 1
                    time_end_idx = line.index("]", sender_end_idx) + 1
                    sender = line[1:sender_end_idx - 1]
                    time_sent = line[sender_end_idx + 2:time_end_idx - 1]
                    content = line[time_end_idx + 2:]

                    if "오전" in time_sent:
                        time_sent = time_sent.replace("오전", "AM")
                    elif "오후" in time_sent:
                        time_sent = time_sent.replace("오후", "PM")

                    time_sent = datetime.strptime(time_sent, "%p %I:%M").time()

                    Message.objects.create(
                        chat_room=chat_room,
                        sender=sender,
                        time_sent=datetime.combine(datetime.today(), time_sent),
                        content=content,
                    )
            except Exception as e:
                print(f"Error parsing line '{line}': {e}")
    

    def validate_kakao_chat_format(self, file):
        """
        카카오톡 대화 내보내기 파일 형식을 검증하는 메서드.
        """
        file.seek(0)

        # 날짜 및 시간 포맷 예시 (ex: 2024년 9월 1일 일요일)
        # 날짜 줄이 '---'로 감싸져 있는 경우를 포함한 정규식
        date_time_pattern = re.compile(r"[-]+\s\d{4}년 \d{1,2}월 \d{1,2}일 .+\s[-]+")

        # 특수문자와 이모티콘을 포함할 수 있는 대화방 이름 정규식  ++++ 11/10 추가
        chat_room_name_pattern = re.compile(r".*님과 카카오톡 대화")

        # 대화 형식 예시 (ex: [김경식] [오전 12:10] 내용)
        chat_line_pattern = re.compile(r"\[.+?\] \[(오전|오후) \d{1,2}:\d{2}\] .+")
  
        first_line_checked = False
        date_line_checked = False

        for line in file:
            line = line.decode("utf-8").strip()

            # 첫 번째 라인: 대화 방 이름 정보 포함 (예: "민병관 님과 카카오톡 대화")
            if not first_line_checked:
                print(f"First line: {line}")  # 첫 번째 줄 디버깅 로그
                first_line_checked = True
                continue

            # 두 번째 라인: 저장 날짜 정보 (예: "저장한 날짜 : 2024-09-02 15:50:27")
            if not date_line_checked:
                if "저장한 날짜" in line:
                    print(f"Date line: {line}")  # 저장 날짜 줄 디버깅 로그
                    date_line_checked = True
                    continue
                else:
                    print(f"Invalid format at date line: {line}")
                    return False

            # 공백 줄 무시
            if not line:
                continue

            # 날짜 형식 확인 (새로운 날 시작 시 표시되는 날짜 정보)
            if date_time_pattern.match(line):
                print(f"Date line matched: {line}")  # 날짜 줄 매치 로그
                continue

            # 대화 형식 확인 (메시지 라인)
            if chat_line_pattern.match(line):
               print(f"Chat line matched: {line}")  # 대화 라인 매치 로그
               continue

            # 일반 대화 내용도 유효하게 처리  ++ 11/10 추가
            print(f"General chat line (non-error): {line}")
            continue  # 일반 대화 내용은 오류로 처리하지 않고 계속 진행



            # 모든 조건에 맞지 않으면 형식이 올바르지 않음
            print(f"Invalid format detected: {line}")
            return False

        # 모든 줄이 유효하다면 True 반환
        return True
