from django.urls import path
<<<<<<< HEAD
from .views import FileUploadView
from .views import ChatRoomBullyingMessages,  DownloadBullyingPDF
from .views import chatroom_result_api

urlpatterns = [
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("chatroom/<int:pk>/messages/", ChatRoomBullyingMessages.as_view(), name="chatroom-messages"),
    path("chatroom/<int:pk>/download-pdf/", DownloadBullyingPDF.as_view(), name="chatroom-download-pdf"),
    path("chatroom/<int:pk>/result/", chatroom_result_api, name="chatroom-result-api"),
]
=======
from .views import FileUploadView, download_cyberbullying_pdf

urlpatterns = [
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("chatroom/<int:pk>/download/", download_cyberbullying_pdf, name="download-cyberbullying-pdf"),
]
>>>>>>> develop
