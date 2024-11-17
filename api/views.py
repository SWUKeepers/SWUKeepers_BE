from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer
from django.shortcuts import render, get_object_or_404
from .models import ChatRoom, Message
from .utils.bert_load import load_model_and_tokenizer, predict_with_cyberbullying_check



import torch

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



class ChatRoomResultView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # 요청 데이터에서 room_hash 확인
            room_hash = request.data.get("room_hash")
            if not room_hash:
                return Response(
                    {"error": "room_hash is required"}, status=status.HTTP_400_BAD_REQUEST
                )

            # ChatRoom 객체 가져오기
            chat_room = get_object_or_404(ChatRoom, room_hash=room_hash)
            messages = Message.objects.filter(chat_room=chat_room)

            if not messages.exists():
                return Response(
                    {"error": "No messages found for the provided room_hash"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 메시지 내용 수집
            sentences = [message.content for message in messages]

            # BERT 모델 및 토크나이저 로드
            model, tokenizer = load_model_and_tokenizer()
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # 분석 수행
            result = predict_with_cyberbullying_check(sentences, tokenizer, model, device)

            # ChatRoom에 분석 결과 업데이트
            chat_room.cyberbullying_detected = (result.get("cyberbullying") == "사이버불링")
            chat_room.save()

            # 응답 데이터 구성
            response_data = {
                "isBullying": chat_room.cyberbullying_detected,
                "messageData": [
                    {
                        "id": message.id,
                        "message": message.content,
                        "sender": message.sender,
                    }
                    for message in messages
                ],
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )