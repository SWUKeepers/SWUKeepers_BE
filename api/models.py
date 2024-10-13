from django.db import models


class TextFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class ChatRoom(models.Model):
    room_name = models.CharField(max_length=255)  # 대화방 이름 또는 참여자 정보
    saved_at = models.DateTimeField(auto_now_add=True)  # 대화를 저장한 날짜

    def __str__(self):
        return self.room_name


class Message(models.Model):
    chat_room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )  # 대화방과 연결
    sender = models.CharField(max_length=100)  # 발신자 이름
    time_sent = models.DateTimeField()  # 메시지가 전송된 시간
    content = models.TextField()  # 메시지 내용

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}"  # 발신자와 메시지의 일부를 출력
