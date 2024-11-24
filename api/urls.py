from django.urls import path
from .views import FileUploadView, download_cyberbullying_pdf

urlpatterns = [
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("chatroom/<int:pk>/download/", download_cyberbullying_pdf, name="download-cyberbullying-pdf"),
]
