import io
from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit  # 긴 문자열을 줄바꿈 처리
from .models import ChatRoom
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer
from api.utils.bert_load import predict_with_cyberbullying_check  # 사이버불링 함수 import
from django.utils.encoding import escape_uri_path  # 파일명 인코딩을 위한 모듈
import logging

# 로그 설정
logger = logging.getLogger(__name__)

# 한글 폰트 등록
font_path = "/home/doa/PPBL/static/fonts/NanumGothic-Regular.ttf"
try:
    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
    logger.info("NanumGothic 폰트 등록 성공")
except Exception as e:
    logger.error(f"폰트 등록 실패: {str(e)}")


def draw_wrapped_text(pdf, x, y, text, max_width, font_name="NanumGothic", font_size=12):
    """
    긴 문자열을 주어진 너비에 맞게 줄 바꿈하여 PDF에 그리는 함수.
    """
    try:
        pdf.setFont(font_name, font_size)
        lines = simpleSplit(text, font_name, font_size, max_width)  # 줄 바꿈 처리
        for line in lines:
            pdf.drawString(x, y, line)
            y -= 15  # 줄 간격 조정
        return y
    except Exception as e:
        logger.error(f"draw_wrapped_text 오류: {str(e)}")
        raise e


class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ChatRoomSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            try:
                # ChatRoom 저장 및 사이버불링 분석
                chat_room = serializer.save()
                is_cyberbullying = chat_room.analyze_cyberbullying()  # 사이버불링 여부 판별

                if not is_cyberbullying:
                    logger.info(f"ChatRoom '{chat_room.room_name}' - 사이버불링 탐지되지 않음.")
                    return Response(
                        {"message": "No cyberbullying detected. PDF not created."},
                        status=status.HTTP_200_OK
                    )

                logger.info(f"ChatRoom '{chat_room.room_name}' - 사이버불링 탐지됨.")
                return Response(
                    {"message": "Cyberbullying detected. You can download the PDF."},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                logger.error(f"사이버불링 분석 또는 저장 실패 - 오류: {str(e)}")
                return Response(
                    {"error": "Error occurred while processing."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class DownloadCyberbullyingPDF(APIView):
    def get(self, request, pk, *args, **kwargs):
        """
        사이버불링 PDF 다운로드를 처리하는 API 뷰.
        """
        try:
            # ChatRoom 객체 가져오기
            chat_room = ChatRoom.objects.get(pk=pk)
            if not chat_room.is_cyberbullying:
                logger.warning(f"ChatRoom ID: {pk} - 사이버불링이 아니므로 다운로드 불가")
                return Response(
                    {"error": "This chat room is not flagged for cyberbullying. PDF download is not allowed."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            logger.info(f"ChatRoom 조회 성공 - ID: {pk}, Room Name: {chat_room.room_name}")
        except ChatRoom.DoesNotExist:
            logger.error(f"ChatRoom 조회 실패 - ID: {pk}")
            return Response(
                {"error": "Chat room not found or not marked as cyberbullying."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            # PDF 생성
            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)

            # PDF 내용 작성
            pdf.setFont("NanumGothic", 12)
            pdf.drawString(100, 800, "Cyberbullying Report")
            pdf.drawString(100, 780, f"Room Name: {chat_room.room_name}")
            pdf.drawString(100, 760, f"Saved At: {chat_room.saved_at.strftime('%Y-%m-%d %H:%M:%S')}")
            y = draw_wrapped_text(pdf, 100, 740, f"Room Hash: {chat_room.room_hash}", max_width=400)

            pdf.drawString(100, y - 20, "Messages:")
            y -= 40
            for message in chat_room.messages.all():
                message_text = f"- {message.sender}: {message.content[:50]}{'...' if len(message.content) > 50 else ''}"
                y = draw_wrapped_text(pdf, 100, y, message_text, max_width=400)
                if y < 50:
                    pdf.showPage()
                    pdf.setFont("NanumGothic", 12)
                    y = 800

            pdf.save()  # PDF 저장
            buffer.seek(0)  # 스트림 시작 지점으로 이동

            # PDF 파일 이름 설정
            filename = f"{chat_room.room_name}_cyberbullying_report.pdf"
            encoded_filename = escape_uri_path(filename)

            # PDF 반환
            response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
            response["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

            buffer.close()  # 스트림 닫기
            return response

        except Exception as e:
            logger.error(f"PDF 생성 또는 응답 실패 - ID: {pk}, 오류: {str(e)}")
            return Response(
                {"error": "Failed to generate PDF. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

