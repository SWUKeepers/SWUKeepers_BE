import re
from datetime import datetime
from django.utils import timezone
from .models import ChatRoom, Message, TextFile

ACTIONS = ["님을 내보냈습니다.", "님이 나갔습니다.", "님이 들어왔습니다."]

class KakaoChatParser:
    @staticmethod
    def read_kakao_txt_file(input_file_name, has_header=True):
        """카카오톡 채팅 데이터를 읽고 context 리스트를 반환합니다."""
        context_list, tmp_context_list = [], []
        with open(input_file_name, "r", encoding="utf-8-sig") as input_file:
            for line in input_file:
                line = line.rstrip('\n')  # 줄 끝의 줄바꿈 문자만 제거하여 데이터 유실 방지
                # 날짜 및 시간 패턴을 단순 문자열 방식으로 확인
                if line and ("오전" in line or "오후" in line) and "년" in line and "월" in line and "일" in line:
                    if tmp_context_list:
                        context_list.append(tmp_context_list)
                    tmp_context_list = [line]  # 새 대화 그룹 시작
                else:
                    tmp_context_list.append(line)

            if tmp_context_list:
                context_list.append(tmp_context_list)

        print("주어진 텍스트 파일 {}의 일자별 context는 {}건입니다.".format(input_file_name, len(context_list)))
        return context_list

    @staticmethod
    def split_talk_by_user(context):
        """작성자+작성시간별 메시지를 합칩니다."""
        whole_txt, merge_txt = [], []
        for index, element in enumerate(context):
            # 날짜 및 시간 패턴을 단순 문자열 방식으로 확인
            if ("오전" in element or "오후" in element) and "년" in element and "월" in element and "일" in element:
                if merge_txt:
                    whole_txt.append(' '.join(merge_txt))
                merge_txt = [element]
            else:
                is_contain = any(action in element for action in ACTIONS)
                if is_contain:
                    if merge_txt:
                        whole_txt.append(' '.join(merge_txt))
                    whole_txt.append(element)
                    merge_txt = []
                else:
                    merge_txt.append(element)
        if merge_txt:
            whole_txt.append(' '.join(merge_txt))
        return [e for e in whole_txt if e.strip()]

    @staticmethod
    def get_writer_and_wrote_at_and_msg(line):
        """작성자, 작성 시간, 메시지를 추출합니다."""
        def convert_time(ko_wrote_at):
            if '오전' in ko_wrote_at:
                time_str = ko_wrote_at.replace('오전', 'AM')
            elif '오후' in ko_wrote_at:
                time_str = ko_wrote_at.replace('오후', 'PM')
            return datetime.strptime(time_str, '%Y년 %m월 %d일 %p %I:%M').strftime('%Y-%m-%d %H:%M')
        
        # 날짜와 작성자, 메시지를 나누기 위한 단순 문자열 방식
        parts = line.split(", ", 1)  # 첫 번째로 날짜와 나머지를 분리
        if len(parts) != 2:
            return None, None, None

        date_str, rest = parts
        rest_parts = rest.split(": ", 1)  # 두 번째로 작성자와 메시지를 분리
        if len(rest_parts) != 2:
            return None, None, None

        writer, msg = rest_parts
        wrote_at = convert_time(date_str)
        return writer.strip(), wrote_at, msg.strip()

    @staticmethod
    def parse_kakao(input_file_name, has_header=True):
        """카카오톡 채팅 데이터 파일을 파싱하고 메시지를 저장합니다."""
        try:
            # 첫 번째 줄에서 room_name 추출
            with open(input_file_name, "r", encoding="utf-8-sig") as input_file:
                first_line = input_file.readline().rstrip('\n')  # 맨 끝의 공백만 제거
                if first_line:
                    room_name = first_line.split(":")[-1].strip() if ":" in first_line else "Default Chat Room"
                else:
                    room_name = "Default Chat Room"

            # ChatRoom 생성 또는 불러오기
            chat_room, created = ChatRoom.objects.get_or_create(room_name=room_name)

            # 파일에서 데이터 읽기
            context_list = KakaoChatParser.read_kakao_txt_file(input_file_name, has_header)

            for context in context_list:
                contents_list = KakaoChatParser.split_talk_by_user(context)
                for content in contents_list:
                    writer, wrote_at, msg = KakaoChatParser.get_writer_and_wrote_at_and_msg(content)
                    if writer and wrote_at and msg:
                        time_sent = datetime.strptime(wrote_at, '%Y-%m-%d %H:%M')
                        print(f"Message: {msg}")  # 메시지를 출력하여 확인
                        # Message 인스턴스 생성 및 저장
                        Message.objects.create(
                            chat_room=chat_room,
                            sender=writer,
                            time_sent=time_sent,
                            content=msg
                        )

            print(f"채팅방 '{chat_room.room_name}'에 메시지가 저장되었습니다.")
            return chat_room  # ChatRoom 인스턴스를 반환

        except Exception as e:
            print(f"Error occurred: {e}")
            return None
