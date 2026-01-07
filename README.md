# Greeni AI Service – 실행 방법

1) 가상환경 생성

``python -m venv .venv``

2) 가상환경 활성화

Git Bash:

``source .venv/Scripts/activate``


PowerShell:

``.venv\Scripts\activate``

3) 패키지 설치

``pip install -r requirements.txt``

4) 환경 변수 설정

.env.example을 복사해 .env 생성:

``APP_NAME=Greeni
OPENAI_API_KEY=...
CLOVA_API_KEY_ID=...
CLOVA_API_KEY=...
BASE_URL=http://localhost:8000``

5) 서버 실행

``python main.py``

6) API 문서

### Swagger UI:

http://localhost:8000/docs


### ReDoc:

http://localhost:8000/redoc


### Health check:

http://localhost:8000/health


