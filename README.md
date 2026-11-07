# ytmusic-dl (v1.3.6)

고음질 음원 스트림 추출, 정밀 메타데이터/싱크 가사 및 1:1 정방형 앨범 아트를 파일에 직접 심어주는 윈도우 데스크톱 오픈소스 아카이빙 프로그램입니다.

---

## 🌟 주요 기능

1. **최고 음질 및 무손실 스트림 추출**
   - **무손실 M4A (AAC)**: 원본 스트림을 재인코딩 손실 없이 그대로 복사하여 1초 만에 저장 (음질 0% 손실).
   - **고음질 MP3 (320kbps)**: 호환성이 필요한 차량용 오디오나 구형 MP3 플레이어를 위한 고음질 변환 지원.
2. **프리미엄 256kbps 최고 음질 연동**
   - 내 PC 브라우저(Chrome, Edge, Firefox) 로그인 정보를 원클릭으로 자동 연동.
   - `cookies.txt` 파일 직접 지정 및 F12 개발자 도구 헤더 간편 붙여넣기 지원.
3. **국적/언어 감지 기반 5계층 싱크 가사 엔진 및 로마자 차단 (v1.3.6 고도화)**
   - **한국 노래 한글 가사 최우선 & 로마자 발음 가사 원천 기각**:
     - 한국 노래에 외국 팬들이 등록한 로마자 발음 전사 가사(`saranghae...`)를 100% 감지하여 즉시 기각.
     - 알송(AlSong) ➔ 유튜브 공식/자동 한국어 자막(`ko`) ➔ 유튜브 설명란 한글 가사 ➔ LRCLIB(한글 필수) ➔ Musixmatch 순으로 정확한 한글 원문 가사 우선 매칭.
   - **해외 팝송 원문 싱크 가사 우선**:
     - 팝송은 LRCLIB ➔ Musixmatch ➔ 유튜브 원어 자막 순으로 원문 영어 싱크 가사 우선 매칭.
   - **전 계층 타임아웃 & 지수 백오프(Exponential Backoff) 방어 하네스**: 알송, LRCLIB, Musixmatch 전 구간에서 일시 과부하(HTTP 503/429/타임아웃) 시 지능형 대기 후 자동 재시도.
   - **음원 내부 태그 직결 내장**: M4A(`©lyr`) 및 MP3(`USLT`) 메타데이터에 `[mm:ss.xx]` 실시간 싱크 가사를 온전히 기본 내장하며, `.lrc` 별도 파일 저장 옵션은 기본 해제(OFF)되어 폴더가 깔끔하게 유지됩니다.
4. **Apple iTunes 공식 정규 장르(Genre) 자동 태깅 (v1.3.6 신규)**
   - 메타데이터 고도화 옵션 활성화 시, iTunes 정규 데이터로부터 `K-Pop`, `Pop`, `R&B/Soul`, `Rock` 등 정확한 공식 장르명을 M4A(`©gen`) 및 MP3(`TCON`) 태그에 자동 기록.
   - 스마트폰(삼성 뮤직, 애플 뮤직), foobar2000 및 차량용 오디오의 '장르별 모아보기' 완벽 지원.
5. **1:1 정방형 앨범 아트 자동 맞춤**
   - 16:9 와이드 썸네일을 음악 플레이어 규격인 1:1 정사각형으로 중앙 자동 크롭하여 내장.
6. **반응형 다크 모드 UI**
   - 대용량 재생목록 다운로드 중에도 UI가 멈추지 않는 비동기 처리.
   - 실시간 진행률, 상태 메시지 및 콘솔 로그 제공.
7. **다운로드 엔진 원클릭 업데이트**
   - 정책 변경 시 프로그램 내 [다운로드 엔진 업데이트] 버튼으로 최신 상태 유지 가능.

---

## 🚀 실행 방법

### 1. 가상환경 또는 터미널에서 실행
```bash
# 저장소 클론 및 이동
git clone https://github.com/L-Jack-00/ytmusic-dl.git
cd ytmusic-dl

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
ytmusic-dl/
├── core/
│   ├── types.py           # 데이터 모델 및 작업 상태 정의
│   ├── ffmpeg_finder.py   # 내장/시스템 FFmpeg 바이너리 자동 탐색기
│   ├── alsong.py          # 알송 SOAP 1.2 RSA-1024 싱크 가사 엔진
│   ├── lrclib.py          # LRCLIB REST API 싱크 가사 엔진 (503 백오프 하네스)
│   ├── musixmatch.py      # Musixmatch 상용 싱크 가사 클라이언트
│   ├── lyrics_detector.py # 언어 감지 및 로마자 발음 가사 필터링 엔진
│   ├── lyrics.py          # 5계층 동적 라우팅 가사 수집 파이프라인
│   ├── image_util.py      # Pillow 1:1 정방형 앨범아트 크롭기
│   ├── tagger.py          # MP3 / M4A ID3, 장르, 가사 및 MP4 메타데이터 기록기
│   ├── downloader.py      # yt-dlp 기반 다운로드 및 태깅 파이프라인
│   └── updater.py         # yt-dlp 최신 버전 확인 및 업데이트 도구
├── gui/
│   ├── styles.py          # 모던 다크 테마 QSS
│   ├── worker.py          # 비동기 백그라운드 다운로드 작업자
│   └── main_window.py     # PyQt6 메인 그래픽 윈도우
├── tests/
│   ├── test_lyrics.py     # 가사 API 및 지수 백오프 하네스 검증
│   ├── test_lyrics_detector.py # 언어 감지 및 로마자 필터 검증
│   ├── test_image_util.py # 1:1 크롭 규격 검증
│   ├── test_tagger.py     # ID3/MP4 태그 및 장르 기록 검증
│   ├── test_fsm_and_worker.py # 상태 관리 및 취소 동작 검증
│   └── run_headless_tests.py  # 헤드리스 테스트 러너
├── main.py                # 프로그램 시작점
└── README.md              # 사용자 안내서
```

---

## ⚖️ 법적 고지 및 면책 조항 (Legal Disclaimer)

1. **목적의 한정**: 본 소프트웨어는 개인적인 연구, 교육 및 개인 소장(Private Fair Use) 목적을 위해 개발된 오픈소스 도구입니다.
2. **저작권 준수**: 다운로드한 모든 음원 및 콘텐츠의 저작권은 원저작권자에게 있으며, 저작권자의 허가 없이 음원을 영리 목적으로 재배포, 공유, 판매하는 행위는 관련 법률에 의해 엄격히 금지됩니다.
3. **서비스 약관(ToS)**: 서비스 이용약관을 준수할 책임은 전적으로 사용자 본인에게 있으며, 개발자는 사용자의 부적절하거나 불법적인 사용으로 인해 발생하는 어떠한 민·형사상 문제에 대해서도 법적 책임을 지지 않습니다.
4. **개인정보 보호**: 본 프로그램은 사용자의 계정 정보나 세션 쿠키를 외부 서버로 전송하지 않으며, 모든 인증 데이터는 로컬 환경에만 머무릅니다.
5. **상표권 고지**: `ytmusic-dl`은 YouTube 또는 Google LLC와 제휴, 보증 또는 관련이 없는 독립적인 서드파티 오픈소스 아카이빙 소프트웨어입니다.

---

## 📜 라이선스 (License)

본 프로젝트는 오픈소스 라이선스에 따라 자유롭게 학습 및 개선할 수 있습니다.
- 코어 다운로드 엔진: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (The Unlicense)
- 미디어 프로세싱 엔진: [FFmpeg](https://ffmpeg.org/) (LGPL/GPL)
- 오디오 태깅 라이브러리: [Mutagen](https://github.com/quodlibet/mutagen) (GPLv2+)
