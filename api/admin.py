from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.html import format_html
from django.urls import reverse
from .models import TextFile, ChatRoom, Message


@admin.register(TextFile)
class TextFileAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at", "file_hash", "preview_text")
    search_fields = ("file_hash",)

    def preview_text(self, obj):
        """
        파일의 첫 100자를 미리보기로 표시합니다.
        """
        try:
            with open(obj.file.path, "r", encoding="utf-8") as f:
                content = f.read()
                return content[:100]  # 파일의 첫 100자 표시
        except UnicodeDecodeError:
            return "파일 인코딩 오류"
        except FileNotFoundError:
            return "파일을 찾을 수 없습니다."

    preview_text.short_description = "파일 미리보기"


# Message 모델을 ChatRoom의 인라인으로 설정
class MessageInline(admin.TabularInline):
    model = Message
    extra = 1  # 새로운 메시지 추가를 위해 빈 필드를 1개 제공


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("room_name", "saved_at", "room_hash", "cyberbullying_status", "download_pdf_button")
    inlines = [MessageInline]
    search_fields = ["room_name", "room_hash"]

    def cyberbullying_status(self, obj):
        """
        사이버불링 여부를 표시합니다.
        """
        print(f"[DEBUG] ChatRoom {obj.pk} - is_cyberbullying: {obj.is_cyberbullying}")
        return "Yes" if obj.is_cyberbullying else "No"

    cyberbullying_status.short_description = "사이버불링 여부"

    def download_pdf_button(self, obj):
        """
        사이버불링 여부가 Yes인 경우 PDF 다운로드 버튼을 표시.
        """
        if obj.is_cyberbullying:
            url = reverse('download-cyberbullying-pdf', args=[obj.pk])
            return format_html('<a href="{}" class="button">Download PDF</a>', url)
        return "-"
    download_pdf_button.short_description = "Download Report"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "chat_room",
        "sender",
        "time_sent",
        "content",
        "is_curse",
    )
    list_filter = ("chat_room", "sender", "is_curse")  # 필터 추가 (방 이름, 발신자, 욕설 여부 기준)
    search_fields = ["sender", "content", "is_curse"]  # 검색 기능 추가 (발신자, 메시지 내용, 욕설 여부 기준)

    def is_curse(self, obj):
        """
        욕설 여부를 표시합니다.
        """
        return "Yes" if obj.is_curse else "No"

    is_curse.short_description = "욕설 여부"  # 관리자 페이지에 욕설 여부 필드 표시
