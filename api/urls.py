from django.urls import path
from .views import FileUploadView, DownloadCyberbullyingPDF  # 필요한 뷰만 import

urlpatterns = [
    path("upload/", FileUploadView.as_view(), name="file-upload"),  # 파일 업로드 처리
    path("chatroom/<int:pk>/download/", DownloadCyberbullyingPDF.as_view(), name="download-cyberbullying-pdf"),  # PDF 다운로드 처리
]