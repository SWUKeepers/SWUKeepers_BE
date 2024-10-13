from django.contrib import admin
from .models import TextFile


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
