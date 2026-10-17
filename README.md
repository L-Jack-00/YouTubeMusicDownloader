# YouTube Music 고음질 다운로더 (v1.0.0)

유튜브(YouTube) 및 유튜브 뮤직(YouTube Music)의 단일 곡 및 재생목록을 최고 음질로 다운로드하고, 정밀 메타데이터와 싱크 가사, 1:1 정방형 앨범 아트를 파일에 직접 심어주는 윈도우 데스크톱 프로그램입니다.

---

## 🌟 주요 기능

1. **최고 음질 및 무손실 스트림 추출**
   - **무손실 M4A (AAC)**: 유튜브 원본 스트림을 재인코딩 손실 없이 그대로 복사하여 1초 만에 저장 (음질 0% 손실).
   - **고음질 MP3 (320kbps)**: 호환성이 필요한 차량용 오디오나 구형 MP3 플레이어를 위한 고음질 변환 지원.
2. **유튜브 프리미엄 256kbps 최고 음질 연동**
   - 내 PC의 브라우저(Chrome, Edge, Firefox) 로그인 정보를 원클릭으로 자동 연동.
   - `cookies.txt` 파일 직접 지정 지원.
3. **3단계 통합 가사 수집 파이프라인**
   - **1순위 유튜브 공식 자막**: 공식 가사 트랙 추출.
   - **2순위 알송(AlSong) SOAP API**: 국내 가요의 실시간 싱크 가사 자동 검색.
   - **3순위 LRCLIB API**: 해외 팝송, J-POP 등 글로벌 음원 가사 보완.
   - 음원 내부 가사 태그(ID3 USLT / MP4 lyrics) 삽입 및 옵션에 따른 `.lrc` 파일 별도 저장.
4. **1:1 정방형 앨범 아트 자동 맞춤**
   - 16:9 유튜브 썸네일을 음악 플레이어 규격인 1:1 정사각형으로 중앙 자동 크롭하여 내장.
5. **반응형 다크 모드 UI**
   - 대용량 재생목록 다운로드 중에도 UI가 멈추지 않는 비동기 처리.
   - 실시간 진행률, 상태 메시지 및 콘솔 로그 제공.
6. **다운로드 엔진 원클릭 업데이트**
   - 유튜브 정책 변경 시 프로그램 내 [다운로드 엔진 업데이트] 버튼으로 최신 상태 유지 가능.

---

## 🚀 실행 방법

### 1. 가상환경 또는 터미널에서 실행
```bash
# 프로젝트 디렉터리로 이동
cd C:\Users\SBK\.gemini\antigravity\scratch\ytmusic-downloader

# 프로그램 실행
python main.py
```

### 2. 필수 라이브러리
이미 설치되어 있으나, 다른 PC에서 실행 시 아래 명령어로 설치할 수 있습니다:
```bash
pip install PyQt6 yt-dlp mutagen Pillow requests imageio-ffmpeg
```

---

## 📁 프로젝트 구조

```text
ytmusic-downloader/
├── core/
│   ├── types.py           # 데이터 모델 및 작업 상태 정의
│   ├── ffmpeg_finder.py   # 내장/시스템 FFmpeg 바이너리 자동 탐색기
│   ├── alsong.py          # 알송 SOAP API 가사 검색 엔진
│   ├── lrclib.py          # LRCLIB REST API 가사 검색 엔진
│   ├── lyrics.py          # 3단계 우선순위 가사 수집 엔진
│   ├── image_util.py      # Pillow 1:1 정방형 앨범아트 크롭기
│   ├── tagger.py          # MP3 / M4A ID3 및 MP4 메타데이터 기록기
│   ├── downloader.py      # yt-dlp 기반 다운로드 및 태깅 파이프라인
│   └── updater.py         # yt-dlp 최신 버전 확인 및 업데이트 도구
├── gui/
│   ├── styles.py          # YouTube Red 모던 다크 테마 QSS
│   ├── worker.py          # 비동기 백그라운드 다운로드 작업자
│   └── main_window.py     # PyQt6 메인 그래픽 윈도우
├── tests/
│   ├── test_lyrics.py     # 가사 검색 및 텍스트 정제 검증
│   ├── test_image_util.py # 1:1 크롭 규격 검증
│   ├── test_tagger.py     # ID3/MP4 태그 및 LRC 파일 검증
│   ├── test_fsm_and_worker.py # 상태 관리 및 취소 동작 검증
│   └── run_headless_tests.py  # 헤드리스 테스트 러너
├── main.py                # 프로그램 시작점
└── README.md              # 사용자 안내서
```

---

## ⚖️ 법적 고지 및 면책 조항 (Legal Disclaimer)

1. **목적의 한정**: 본 소프트웨어는 개인적인 연구, 교육 및 개인 소장(Private Fair Use) 목적을 위해 개발된 오픈소스 도구입니다.
2. **저작권 준수**: 다운로드한 모든 음원 및 콘텐츠의 저작권은 원저작권자에게 있으며, 저작권자의 허가 없이 음원을 영리 목적으로 재배포, 공유, 판매하는 행위는 관련 법률에 의해 엄격히 금지됩니다.
3. **서비스 약관(ToS)**: 유튜브 및 유튜브 뮤직의 서비스 이용약관을 준수할 책임은 전적으로 사용자 본인에게 있으며, 개발자는 사용자의 부적절하거나 불법적인 사용으로 인해 발생하는 어떠한 민·형사상 문제에 대해서도 법적 책임을 지지 않습니다.
4. **개인정보 보호**: 본 프로그램은 사용자의 계정 정보나 세션 쿠키를 외부 서버로 전송하지 않으며, 모든 인증 데이터는 로컬 환경에만 머무릅니다.

---

## 📜 라이선스 (License)

본 프로젝트는 오픈소스 라이선스에 따라 자유롭게 학습 및 개선할 수 있습니다.
- 코어 다운로드 엔진: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (The Unlicense)
- 미디어 프로세싱 엔진: [FFmpeg](https://ffmpeg.org/) (LGPL/GPL)
- 오디오 태깅 라이브러리: [Mutagen](https://github.com/quodlibet/mutagen) (GPLv2+)

