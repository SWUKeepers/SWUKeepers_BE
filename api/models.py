import hashlib
from django.db import models
from django.utils import timezone
from api.apps import MyAppConfig
from api.utils.bert_load import predict_with_cyberbullying_check  # 사이버불링 함수 import
import torch  # torch 명시적 import


class TextFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        self.file_hash = self.calculate_file_hash()
        super().save(*args, **kwargs)

    def calculate_file_hash(self):
        hasher = hashlib.sha256()
        if self.file:
            self.file.seek(0)
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.file.seek(0)
        return hasher.hexdigest()


class ChatRoom(models.Model):
    room_name = models.CharField(max_length=255)
    saved_at = models.DateTimeField(auto_now_add=True)
    room_hash = models.CharField(max_length=64, unique=True, blank=True, null=True, editable=False)
    is_cyberbullying = models.BooleanField(default=False)

    def __str__(self):
        return self.room_name

    def save(self, *args, **kwargs):
        if not self.room_hash:
            self.room_hash = self.generate_hash()
        super().save(*args, **kwargs)

    def generate_hash(self):
        hasher = hashlib.sha256()
        hasher.update(self.room_name.encode("utf-8"))
        return hasher.hexdigest()

    def analyze_cyberbullying(self):
        """채팅방 메시지를 분석하여 사이버불링 여부를 판별"""
        messages = [message.content for message in self.messages.all()]
        model = MyAppConfig.model
        tokenizer = MyAppConfig.tokenizer
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_cyberbullying = predict_with_cyberbullying_check(messages, tokenizer, model, device) == "사이버불링"
        self.save()


class Message(models.Model):
    chat_room = models.ForeignKey(
        'ChatRoom', related_name="messages", on_delete=models.CASCADE
    )
    sender = models.CharField(max_length=100)
    time_sent = models.DateTimeField()
    content = models.TextField()
    is_curse = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.time_sent and timezone.is_naive(self.time_sent):
            self.time_sent = timezone.make_aware(self.time_sent, timezone.get_default_timezone())

        model = MyAppConfig.model
        tokenizer = MyAppConfig.tokenizer
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_curse = predict_with_cyberbullying_check([self.content], tokenizer, model, device) == "사이버불링"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}"
