from django.contrib import admin
from .models import TextFile, ChatRoom, Message


@admin.register(TextFile)
class TextFileAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at", "preview_text")

    def preview_text(self, obj):
        try:
            with open(obj.file.path, "r", encoding="utf-8") as f:
                content = f.read()
                return content[:100]  # 파일의 첫 100자를 미리보기로 표시
        except UnicodeDecodeError:
            return "파일 인코딩 오류"

    preview_text.short_description = "파일 미리보기"


# Message 모델을 ChatRoom의 인라인으로 설정
class MessageInline(admin.TabularInline):
    model = Message
    extra = 1  # 새로운 메시지 추가를 위해 빈 필드를 1개 제공


# ChatRoom 모델 관리자 설정
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("room_name", "saved_at")  # 목록에서 표시할 필드
    inlines = [MessageInline]  # 메시지를 인라인 형태로 표시
    search_fields = ["room_name"]  # 검색 기능 추가 (방 이름 기준)


# Message 모델도 직접 관리하고 싶을 경우 (선택적)
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "chat_room",
        "sender",
        "time_sent",
        "content",
    )  # 목록에서 표시할 필드
    list_filter = ("chat_room", "sender")  # 필터 추가 (방 이름, 발신자 기준)
    search_fields = ["sender", "content"]  # 검색 기능 추가 (발신자, 메시지 내용 기준)
