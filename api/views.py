# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer
from .models import Message
import sys
import os
from sklearn.model_selection import train_test_split
from transformers import BertTokenizer, BertForSequenceClassification
import torch
from torch.optim import AdamW

# 상위 디렉토리의 codes 폴더를 Python 경로에 추가
sys.path.append('/home/doa/codes')
# AI 모델을 가져오기
import FinalTestModel

model = BertForSequenceClassification.from_pretrained('bert-base-multilingual-cased', num_labels=2)
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)



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
            #serializer.save()
            chat_room, sentences = serializer.create(serializer.validated_data)  # ChatRoom과 sentences를 반환
            #return Response(serializer.data, status=status.HTTP_201_CREATED)

             
            #results = FinalTestModel.predict_sentiment(sentences)  # AI 모델의 예측 함수 호출
            # AI 모델을 통한 감정 예측
            results = []
            for sentence in sentences:
                sentiment = FinalTestModel.predict_sentiment(sentence)  # AI 모델의 예측 함수 호출
                results.append(sentiment)
                print(f"Sentence: {sentence}, Sentiment: {sentiment}") 

            # 각 문장과 그에 대한 감정 판단 결과를 포함한 리스트 생성
            final_results = []
            for i, sentence in enumerate(sentences):
                
                # Message 모델에 저장
                message = Message.objects.create(
                    chat_room=chat_room,  # 해당 대화방의 인스턴스
                    sender="민병관",  # 로부터의 메시지
                    time_sent=datetime.now(),  # 현재 시간
                    content=sentence,
                    sentiment=results[i] if i < len(results) else None # AI 모델의 결과를 sentiment 필드에 저장
                )
                print(f"Saved Message: {message.content}, Sentiment: {message.sentiment}")  # 저장된 메시지와 감정 확인
                final_results.append({
                    "sentence": sentence,
                    "sentiment": results[i] if i < len(results) else None # AI 모델의 결과
                })

            return Response(final_results, status=status.HTTP_200_OK)
        
        # 에러 발생 시 로그 출력
        print(serializer.errors)  # 시리얼라이저의 오류 출력
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
