from django.urls import path
from .views import FileUploadView
from .views import ChatRoomResultView

urlpatterns = [
    path("upload/", FileUploadView.as_view(), name="file-upload"),
     path("api/result/", ChatRoomResultView.as_view(), name="chat-room-result"),
]

