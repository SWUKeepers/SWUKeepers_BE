from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TextFile, ChatRoom, Message

@admin.register(TextFile)
class TextFileAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at", "file_hash", "preview_text")
    search_fields = ("file_hash",)

    def preview_text(self, obj):
        try:
            with open(obj.file.path, "r", encoding="utf-8") as f:
                content = f.read()
                return content[:100]
        except UnicodeDecodeError:
            return "파일 인코딩 오류"
        except FileNotFoundError:
            return "파일을 찾을 수 없습니다."

    preview_text.short_description = "파일 미리보기"


class MessageInline(admin.TabularInline):
    model = Message
    extra = 1


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("room_name", "saved_at", "room_hash", "cyberbullying_status", "download_pdf_button")
    inlines = [MessageInline]
    search_fields = ["room_name", "room_hash"]

    def cyberbullying_status(self, obj):
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
    list_filter = ("chat_room", "sender", "is_curse")
    search_fields = ["sender", "content", "is_curse"]

    def is_curse(self, obj):
        return "Yes" if obj.is_curse else "No"

    is_curse.short_description = "욕설 여부"
