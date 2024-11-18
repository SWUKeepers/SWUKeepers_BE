from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer
from .models import ChatRoom
from api.utils.bert_load import predict_with_cyberbullying_check  # 사이버불링 함수 import
import torch  # torch 명시적 import

class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]
        serializer = ChatRoomSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            try:
                chat_room = serializer.save()
                chat_room.analyze_cyberbullying()  # 사이버불링 분석 수행
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error while processing file: {e}")
                return Response(
                    {"detail": "파일 처리 중 오류가 발생했습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            print("Validation errors: ", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
