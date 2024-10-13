# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer


class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ChatRoomSerializer(
            data=request.data, context={"request": request}
        )  # context로 request 전달
        if serializer.is_valid():
            # 파일을 저장하고 파싱 처리
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # 에러 발생 시 로그 출력
        print(serializer.errors)  # 시리얼라이저의 오류 출력
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
