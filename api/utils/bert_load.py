import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from django.conf import settings
import re
import json


# 모델 및 토크나이저 로드 함수
def load_model_and_tokenizer():
    model_path = os.path.join(settings.BASE_DIR, "models/model_weight.bin")
    model = BertForSequenceClassification.from_pretrained(
        "bert-base-multilingual-cased", num_labels=2
    )
    tokenizer = BertTokenizer.from_pretrained("bert-base-multilingual-cased")

    model_path = os.path.join(settings.BASE_DIR, 'models/model_weight.bin')
    model = BertForSequenceClassification.from_pretrained('bert-base-multilingual-cased', num_labels=2)
    tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')

    try:
        state_dict = torch.load(model_path)
        model.load_state_dict(state_dict, strict=False)  # false/true 수정
        model.load_state_dict(state_dict, strict=False)  # false/true 수정
        print("[INFO] 모델 가중치 로드 성공")
    except Exception as e:
        print("[ERROR] 모델 로드 실패:", e)


    print("[DEBUG] 모델 상태 체크:", model.state_dict().keys())
    return model, tokenizer


# 욕설 단어 로드 함수
def load_abuse_words():
    curse_file_path = os.path.join(
        settings.BASE_DIR, "curse.json"
    )  # 욕설 단어 JSON 파일 경로
    curse_file_path = os.path.join(settings.BASE_DIR, '/root/SWUKeepers_BE/models/curse.json')  # 욕설 단어 JSON 파일 경로
    try:
        with open(curse_file_path, "r", encoding="utf-8") as f:
            curse_words = json.load(f)
        print("[INFO] 욕설 단어 로드 성공")
        return curse_words
    except Exception as e:
        print("[ERROR] 욕설 단어 파일 로드 실패:", e)
        return {}


# 욕설 단어 포함 여부 확인
def contains_abuse_word(sentence, abuse_words):
    for words in abuse_words.values():
        for word in words:
            if word in sentence:
                print(f"[INFO] 욕설 단어 발견: {word} -> {sentence}")
                return True
    return False


# 특정 기호('ㅋ', 'ㅎ') 포함 여부 확인
def contains_laughing_symbols(sentence):
    if "ㅋ" in sentence or "ㅎ" in sentence:
        print(
            f"[INFO] 특정 기호 발견: {'ㅋ' if 'ㅋ' in sentence else 'ㅎ'} -> {sentence}"
        )
        return True
    return False


# 감정 분석 함수 (1번째 코드와 동일하게 적용)
def predict_sentiment(model, tokenizer, text, device):
    model.eval()


    # 데이터 토크나이징
    inputs = tokenize_data(text, tokenizer)
    inputs = {key: val.to(device) for key, val in inputs.items()}


    # 모델 예측
    with torch.no_grad():
        outputs = model(**inputs)
        prediction = torch.argmax(outputs.logits, dim=-1).item()


    sentiment = "긍정" if prediction == 1 else "부정"
    print(f"[INFO] 문장 분석: {sentiment} -> {text}")
    return sentiment

# 데이터 토크나이징 함수 (1번째 코드와 동일하게 수정)
def tokenize_data(texts, tokenizer, max_len=128):
    inputs = tokenizer(
        texts, padding=True, truncation=True, max_length=max_len, return_tensors="pt"
    )
    return inputs

# 전체 처리 함수
def predict_with_cyberbullying_check(sentences, tokenizer, model, device):
    abuse_words = load_abuse_words()
    sentiments = []  # 각 문장의 긍/부정 결과를 저장할 리스트

    # 욕설 연속 카운터 초기화
    consecutive_abuse_count = 0

    for sentence in sentences:
        contains_abuse = contains_abuse_word(sentence, abuse_words)
        contains_laughing = contains_laughing_symbols(sentence)

        if contains_abuse or contains_laughing:
            consecutive_abuse_count += 1
            if consecutive_abuse_count >= 2:
                sentiment = "긍정"
                print(f"[INFO] 연속 욕설/웃음 기호 감지 -> 강제 긍정 처리: {sentence}")
            elif consecutive_abuse_count == 1:
                sentiment = "긍정"
                print(f"[INFO] 첫 욕설/웃음 기호 감지 -> 강제 긍정 처리: {sentence}")
            elif consecutive_abuse_count == 1:
                sentiment = "긍정"
                print(f"[INFO] 첫 욕설/웃음 기호 감지 -> 강제 긍정 처리: {sentence}")
            else:
                sentiment = predict_sentiment(model, tokenizer, sentence, device)
        else:
            consecutive_abuse_count = 0  # 연속 카운터 초기화
            sentiment = predict_sentiment(model, tokenizer, sentence, device)

        sentiments.append(sentiment)

    return check_cyberbullying(sentiments)

# 최종 판단 함수
def check_cyberbullying(sentiments):
    positive_count = sentiments.count("긍정")
    negative_count = sentiments.count("부정")
    total_count = len(sentiments)

    # 긍정 및 부정 비율 계산
    negative_ratio = negative_count / total_count if total_count > 0 else 0
    positive_ratio = positive_count / total_count if total_count > 0 else 0

    print(
        f"[DEBUG] 긍정 비율: {positive_ratio:.2f}, 부정 비율: {negative_ratio:.2f} (긍정 개수: {positive_count}, 부정 개수: {negative_count}, 총 문장 수: {total_count})"
    )

    # 사이버불링 조건
    is_cyberbullying = (
        negative_ratio > 0.6  # 부정 비율이 60% 이상
        or any(
            sentiments[i : i + 3] == ["부정", "부정", "부정"]
            for i in range(len(sentiments) - 2)
        )  # 부정이 연속 3회 이상 등장
        or (
            positive_ratio < 0.5 and positive_count < negative_count
        )  # 긍정 비율이 낮고 부정이 더 많음
    )

    result = "사이버불링" if is_cyberbullying else "사이버불링 아님"
    print(f"[RESULT] 최종 판단: {result}")
    return result

