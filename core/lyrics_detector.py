# -*- coding: utf-8 -*-
"""
Lyrics Language & Romanization Detection Engine.
Identifies Korean tracks and detects/filters out Romanized Korean lyrics (한글 독음 영어 가사).
"""
import re
from typing import Optional, Set


# 로마자 가사 명시적 식별 태그/키워드 정규식
ROMANIZED_KEYWORDS = re.compile(
    r'\b(romanized|romanization|romaja)\b|^\s*Rom\s*:',
    re.IGNORECASE | re.MULTILINE
)

# 한국어 고유 로마자 표기 어휘 (영단어에는 존재하지 않는 한국어 대명사, 조사, 감탄사, 주요 동사)
ROMANIZED_WORDS = [
    # 대명사 및 조사
    'neoreul', 'nareul', 'neoege', 'naege', 'geudae', 'geudaega', 'geudael', 'geudaewa',
    'neowa', 'nawa', 'uri', 'uriga', 'urineun', 'neoneun', 'naneun', 'naega', 'neoga',
    'geunyang', 'geureohge', 'ireohge', 'jeoreohge', 'geunde', 'geureonde',
    # 동사 및 형용사 어간/표현
    'sarang', 'saranghae', 'saranghaeyo', 'saranghanda', 'saranghaess', 'sarangiran',
    'bogosipeo', 'bogo sipeo', 'bogo sipeunde', 'bogosipda', 'bogo sipda',
    'isseo', 'isseoyo', 'eopseo', 'eopseoyo', 'eobseo', 'eobseoyo',
    'haesseo', 'haessdeon', 'haessjanha', 'haessda',
    'hajima', 'haji ma', 'annyeong', 'jinjja', 'jeongmal',
    'eotteohke', 'eotteoke', 'eojjeoda', 'mollayo', 'molla',
    'maeum', 'maeumi', 'mami', 'sesang', 'sesange', 'sesangeun',
    'oneul', 'naeill', 'hamkke', 'dasin', 'gaseum', 'gaseumi',
    'nunmul', 'nunmuri', 'jigeum', 'chueok', 'gidaryeo', 'sigani',
    'gomawo', 'gomawoss', 'oppa', 'daebak', 'gajima', 'kajima',
    'mianhae', 'mianhaeyo', 'yepposseo', 'yeppeo', 'gwaenchanha', 'gwaenchana',
    'aljanha', 'aljana', 'dagawa', 'majimag', 'majimak', 'barabwa',
    'yeongwonhi', 'gieokhae', 'haruharu', 'malhaejwo', 'malhae'
]

ROMANIZED_REGEX = re.compile(r'\b(' + '|'.join(ROMANIZED_WORDS) + r')\b', re.IGNORECASE)

# 한국어 로마자 특유의 서술격/연결 어미 패턴 (-seumnida, -hamnida, -haesseo, -janha 등)
ROMAN_SUFFIX = re.compile(
    r'\b[a-z]+(?:haesseo|haessda|haessdeon|eossda|issda|seumnida|seupnida|hamnida|hapnida|janha|kkayo)\b',
    re.IGNORECASE
)

# 영문 표기 대표 K-POP 아티스트 목록 (한글명이 없는 메타데이터에서도 한국 곡으로 정확히 판정)
KPOP_ENGLISH_ARTISTS: Set[str] = {
    "bts", "blackpink", "newjeans", "aespa", "ive", "le sserafim",
    "seventeen", "stray kids", "nct", "nct 127", "nct dream", "enhypen",
    "txt", "tomorrow x together", "itzy", "red velvet", "exo", "shinee",
    "iu", "akmu", "day6", "babymonster", "kiss of life", "boynextdoor",
    "tws", "riize", "zerobaseone", "stayc", "nmixx", "twice", "monsta x",
    "ateez", "the boyz", "treasure", "got7", "mamamoo", "btob", "winner",
    "ikon", "highlight", "infinite", "super junior", "girls generation",
    "snsd", "2ne1", "bigbang", "tvxq", "kara", "t ara", "wonder girls",
    "sistar", "apink", "gfriend", "loona", "kep1er", "izone", "triple s",
    "illit", "qwer", "fromis 9", "lucy", "woodz", "taeyeon", "jungkook",
    "jimin", "v", "suga", "j hope", "rm", "jin", "jennie", "rose", "lisa", "jisoo"
}


def has_hangul(text: Optional[str]) -> bool:
    """텍스트에 완성형 한글이 한 글자라도 포함되어 있는지 확인"""
    if not text:
        return False
    return any('\uac00' <= c <= '\ud7a3' for c in text)


def count_hangul(text: Optional[str]) -> int:
    """텍스트 내 완성형 한글 글자 수 계산"""
    if not text:
        return 0
    return sum(1 for c in text if '\uac00' <= c <= '\ud7a3')


def is_romanized_korean_lyrics(text: Optional[str]) -> bool:
    """
    가사 텍스트가 한글 원문이 아닌 '한글 음을 알파벳으로 전사한 로마자 가사(Romanized)'인지 판별합니다.
    - 정식 한글 가사(Hangul)가 충분히 포함되어 있으면 False 반환
    - (Romanized) 태그가 있거나 고유 로마자 어휘/어미가 2개 이상 검출되면 True 반환
    """
    if not text or len(text.strip()) < 10:
        return False

    # 이미 본문에 한글이 15글자 이상 포함되어 있으면 정상 한국어 가사로 판정
    if count_hangul(text) >= 15:
        return False

    # 1. 명시적 로마자 태그 검사 ([Romanized], (Romanization), Rom: 등)
    if ROMANIZED_KEYWORDS.search(text):
        return True

    # 2. 로마자 한국어 고유 어휘 및 어미 검출
    matches = set(m.lower() for m in ROMANIZED_REGEX.findall(text))
    suffix_matches = set(m.lower() for m in ROMAN_SUFFIX.findall(text))
    total_hits = len(matches | suffix_matches)

    return total_hits >= 2


def is_korean_track(
    title: str = "",
    artist: str = "",
    album: Optional[str] = None,
    channel: Optional[str] = None,
    description: Optional[str] = None,
    embedded_subtitles: Optional[str] = None
) -> bool:
    """
    곡 메타데이터 및 부가 정보를 분석하여 한국 곡(국내 가요, K-POP, 인디 등) 여부를 판정합니다.
    """
    # 1. 제목, 아티스트, 앨범에 한글 포함 여부
    meta_str = f"{title} {artist} {album or ''} {channel or ''}"
    if has_hangul(meta_str):
        return True

    # 2. 영문 표기 대표 K-POP 아티스트 감지
    clean_a = re.sub(r'[\W_]+', '', (artist or '').lower())
    for ka in KPOP_ENGLISH_ARTISTS:
        if re.sub(r'[\W_]+', '', ka) == clean_a:
            return True

    # 3. 유튜브 설명란 내 한글 가사/크레딧 여부 (10자 이상의 한글)
    if description and count_hangul(description) >= 10:
        return True

    # 4. 다운로드된 자막에 한글 포함 여부
    if embedded_subtitles and count_hangul(embedded_subtitles) >= 10:
        return True

    return False
