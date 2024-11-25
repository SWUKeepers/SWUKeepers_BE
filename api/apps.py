# api/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = 'api'

    def ready(self):
        # 서버 시작 시 모델과 토크나이저 로드 및 전역 변수 설정
        model, tokenizer = load_model_and_tokenizer()
        MyAppConfig.model = model
        MyAppConfig.tokenizer = tokenizer
