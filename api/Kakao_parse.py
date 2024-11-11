import re
from datetime import datetime
from api.models import ChatRoom, Message

# 관리자 행동 및 참여자 인입 기본 패턴
ACTIONS = ["님을 내보냈습니다.", "님이 나갔습니다.", "님이 들어왔습니다."]

# 카카오톡 채팅 데이터 읽기
def read_kakao_txt_file(file):
    context_list, tmp_context_list = [], []

    for line in file:
        line = line.strip()
        if line and re.match(r'\d{4}년 \d{1,2}월 \d{1,2}일 오후|\d{4}년 \d{1,2}월 \d{1,2}일 오전', line):
            if tmp_context_list:
                context_list.append(tmp_context_list)
            tmp_context_list = [line]
        else:
            tmp_context_list.append(line)
            
    if tmp_context_list:
        context_list.append(tmp_context_list)

    return context_list

# 작성자+작성시간별 메시지 합치기
def split_talk_by_user(context):
    whole_txt, merge_txt = [], []
    for index, element in enumerate(context):
        start_str = re.match(r'\d{4}년 \d{1,2}월 \d{1,2}일 오후|\d{4}년 \d{1,2}월 \d{1,2}일 오전', element)
        if start_str:
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

# 작성자, 작성 시간, 메시지 추출
def get_writer_and_wrote_at_and_msg(line):
    def convert_time(ko_wrote_at):
        try:
            if '오전' in ko_wrote_at:
                time_str = ko_wrote_at.replace('오전', 'AM')
            elif '오후' in ko_wrote_at:
                time_str = ko_wrote_at.replace('오후', 'PM')
            return datetime.strptime(time_str, '%Y년 %m월 %d일 %p %I:%M')
        except ValueError as e:
            print(f"Time conversion error for '{ko_wrote_at}': {e}")
            return None

    match = re.match(r'(\d{4}년 \d{1,2}월 \d{1,2}일 \S{2} \d{1,2}:\d{2}), (.*?): (.*)', line)
    if match:
        date_str, writer, msg = match.groups()
        wrote_at = convert_time(date_str)
        if wrote_at:
            return writer, wrote_at, msg
    return None, None, None

# 파싱을 수행하여 메시지를 데이터베이스에 저장
def parse_kakao_file(file, chat_room):
    context_list = read_kakao_txt_file(file)

    for context in context_list:
        contents_list = split_talk_by_user(context)
        for content in contents_list:
            writer, wrote_at, msg = get_writer_and_wrote_at_and_msg(content)
            if writer and wrote_at and msg:
                try:
                    # Message 인스턴스 생성 및 저장
                    Message.objects.create(
                        chat_room=chat_room,
                        sender=writer,
                        time_sent=wrote_at,
                        content=msg
                    )
                except Exception as e:
                    print(f"Error saving message - Sender: '{writer}', Time: '{wrote_at}', Content: '{msg}': {e}")
