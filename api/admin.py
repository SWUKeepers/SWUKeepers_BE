from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TextFile, ChatRoom, Message
from django.urls import reverse
from django.utils.html import format_html


@admin.register(TextFile)
class TextFileAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at", "file_hash", "preview_text")  # 해시 필드 추가
    search_fields = ("file_hash",)  # 해시 값 검색 기능 추가

    def preview_text(self, obj):
        """파일의 첫 100자를 미리보기로 표시합니다."""
        try:
            with open(obj.file.path, "r", encoding="utf-8") as f:
                content = f.read()
                return content[:100]  # 파일의 첫 100자 표시
        except UnicodeDecodeError:
            return "파일 인코딩 오류"
        except FileNotFoundError:
            return "파일을 찾을 수 없습니다."

    preview_text.short_description = "파일 미리보기"  # 미리보기 컬럼 제목 설정


# Message 모델을 ChatRoom의 인라인으로 설정
class MessageInline(admin.TabularInline):
    model = Message
    extra = 1  # 새로운 메시지 추가를 위해 빈 필드를 1개 제공


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("room_name", "saved_at", "room_hash", "is_cyberbullying")  # 해시 필드 추가
    inlines = [MessageInline]  # 메시지를 인라인 형태로 표시
    search_fields = ["room_name", "room_hash","is_cyberbullying"]  # 검색 기능 추가 (방 이름 및 해시)

    def room_hash(self, obj):
        """채팅방에 저장된 해시 값을 반환합니다."""
        return obj.room_hash if obj.room_hash else "No Hash"

    room_hash.short_description = "Room Hash"  # 관리자 페이지에 해시 필드 표시

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
        "is_curse",  # 욕설 여부 필드 추가
    )  # 목록에서 표시할 필드
    list_filter = ("chat_room", "sender", "is_curse")  # 필터 추가 (방 이름, 발신자, 욕설 여부 기준)
    search_fields = ["sender", "content", "is_curse"]  # 검색 기능 추가 (발신자, 메시지 내용, 욕설 여부 기준)

    def is_curse(self, obj):
        """욕설 여부를 표시합니다."""
        return "Yes" if obj.is_curse else "No"

    is_curse.short_description = "욕설 여부"  # 관리자 페이지에 욕설 여부 필드 표시



