from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer


class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        # 파일이 요청에 포함되지 않았을 경우 처리
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]

        # 시리얼라이저로 데이터를 전달
        serializer = ChatRoomSerializer(data=request.data, context={"request": request})

        # 유효성 검사
        if serializer.is_valid():
            try:
                # 파일 검증 및 파싱 처리
                chat_room = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error while processing file: {e}")
                return Response(
                    {"detail": "파일 처리 중 오류가 발생했습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # 유효성 검증 실패 시
            print("Validation errors: ", serializer.errors)  # 에러 로그 출력
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
