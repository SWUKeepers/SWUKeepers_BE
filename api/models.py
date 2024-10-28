import hashlib
from django.db import models

class TextFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)  # 파일 해시 필드

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        """파일 해시를 계산하여 저장합니다."""
        self.file_hash = self.calculate_file_hash()
        super().save(*args, **kwargs)  # 부모 클래스의 save 호출

    def calculate_file_hash(self):
        """파일의 해시 값을 계산합니다."""
        hasher = hashlib.sha256()
        if self.file:
            self.file.seek(0)  # 파일 포인터를 처음으로 이동
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.file.seek(0)  # 파일 포인터를 다시 처음으로 이동
        return hasher.hexdigest()


class ChatRoom(models.Model):
    room_name = models.CharField(max_length=255)  # 대화방 이름
    saved_at = models.DateTimeField(auto_now_add=True)  # 대화 저장 날짜
    room_hash = models.CharField(max_length=64, unique=True, blank=True, null=True, editable=False)  # 필드 수정

    def __str__(self):
        return self.room_name

    def save(self, *args, **kwargs):
        """채팅방 이름을 해시화하여 저장합니다."""
        if not self.room_hash:  # 이미 존재하는 경우 재생성하지 않음
            self.room_hash = self.generate_hash()
        super().save(*args, **kwargs)  # 부모 클래스의 save 호출

    def generate_hash(self):
        """room_name을 해시화하여 반환합니다."""
        hasher = hashlib.sha256()
        hasher.update(self.room_name.encode("utf-8"))
        return hasher.hexdigest()


class Message(models.Model):
    chat_room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )  # 대화방과 연결
    sender = models.CharField(max_length=100)  # 발신자 이름
    time_sent = models.DateTimeField()  # 메시지 전송 시간
    content = models.TextField()  # 메시지 내용

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}"  # 메시지 일부를 출력

