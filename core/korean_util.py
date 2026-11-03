# -*- coding: utf-8 -*-
"""
Korean Artist and Title Localization Utilities.
Extracts and prefers Korean names over English/Romanized names.
"""
import re
from typing import Tuple

# 주요 한국 가수/아티스트 영문명 -> 표준 한글명 매핑 사전
KOREAN_ARTISTS_MAP = {
    # 힙합 / R&B
    'dynamicduo': '다이나믹 듀오',
    'dynamic duo': '다이나믹 듀오',
    'drunken tiger': '드렁큰 타이거',
    'epik high': '에픽하이',
    'leessang': '리쌍',
    'baechigi': '배치기',
    'supreme team': '슈프림팀',
    'kinetic flow': '키네틱 플로우',
    'mc mong': 'MC몽',
    'freestyle': '프리스타일',
    'primary': '프라이머리',
    'zion.t': '자이언티',
    'crush': '크러쉬',
    'heize': '헤이즈',
    'dean': '딘',
    'zico': '지코',
    'gray': '그레이',
    'loco': '로꼬',
    'simon dominic': '사이먼 도미닉',
    'beenzino': '빈지노',
    'dok2': '도끼',
    'the quiett': '더콰이엇',
    'giriboy': '기리보이',
    'changmo': '창모',
    'ash island': '애쉬 아일랜드',
    'paul blanco': '폴블랑코',
    'big naughty': '빅나티',
    'penomeco': '페노메코',
    'young jun': '영준',
    'jung in': '정인',
    'harim': '하림',

    # 밴드 / 록 / 인디
    'nell': '넬',
    'jannabi': '잔나비',
    'day6': '데이식스',
    'lucy': '루시',
    'ftisland': 'FT아일랜드',
    'cnblue': '씨엔블루',
    'silica gel': '실리카겔',
    'hyukoh': '혁오',
    'busker busker': '버스커 버스커',
    'jang beom june': '장범준',
    '10cm': '10cm',
    'standing egg': '스탠딩 에그',
    'bolbbalgan4': '볼빨간사춘기',
    'bol4': '볼빨간사춘기',
    'melomance': '멜로망스',
    'urban zakapa': '어반자카파',
    'akmu': '악뮤',
    'akdong musician': '악동뮤지션',
    'thornapple': '쏜애플',
    'guckkasten': '국카스텐',
    'yb': 'YB',
    'jaurim': '자우림',

    # K-POP / 아이돌
    'bts': '방탄소년단',
    'blackpink': '블랙핑크',
    'twice': '트와이스',
    'red velvet': '레드벨벳',
    'newjeans': '뉴진스',
    'aespa': '에스파',
    'ive': '아이브',
    'le sserafim': '르세라핌',
    'seventeen': '세븐틴',
    'stray kids': '스트레이 키즈',
    'exo': '엑소',
    'nct': 'NCT',
    'nct 127': 'NCT 127',
    'nct dream': 'NCT DREAM',
    'txt': '투모로우바이투게더',
    'tomorrow x together': '투모로우바이투게더',
    'enhypen': '엔하이픈',
    'itzy': '있지',
    'nmixx': '엔믹스',
    '(g)i-dle': '(여자)아이들',
    'gidle': '(여자)아이들',
    'stayc': '스테이씨',
    'kiss of life': '키스오브라이프',
    'girls\' generation': '소녀시대',
    'snsd': '소녀시대',
    'kara': '카라',
    'wonder girls': '원더걸스',
    '2ne1': '2NE1',
    'bigbang': '빅뱅',
    'big bang': '빅뱅',
    'super junior': '슈퍼주니어',
    'tvxq': '동방신기',
    'shinee': '샤이니',
    'infinite': '인피니트',
    'beast': '비스트',
    'btob': '비투비',
    'mamamoo': '마마무',
    'gfriend': '여자친구',
    'oh my girl': '오마이걸',
    'lovelyz': '러블리즈',
    'iz*one': '아이즈원',
    'izone': '아이즈원',
    'wanna one': '워너원',

    # 솔로 / 보컬
    'iu': '아이유',
    'taeyeon': '태연',
    'g-dragon': '지드래곤',
    'gd': '지드래곤',
    'taeyang': '태양',
    'daesung': '대성',
    'top': '탑',
    'chungha': '청하',
    'sunmi': '선미',
    'hyuna': '현아',
    'jessi': '제시',
    'hwayobi': '화요비',
    'gummy': '거미',
    'baek ji young': '백지영',
    'lyn': '린',
    'davichi': '다비치',
    'seeya': '씨야',
    'see ya': '씨야',
    'sg wannabe': 'SG워너비',
    'vibe': '바이브',
    'brown eyed soul': '브라운 아이드 소울',
    'brown eyed girls': '브라운 아이드 걸스',
    'noel': '노을',
    '4men': '포맨',
    '2am': '2AM',
    '2pm': '2PM',
    'k.will': '케이윌',
    'sung si kyung': '성시경',
    'park hyo shin': '박효신',
    'kim bum soo': '김범수',
    'naul': '나얼',
    'lee seung gi': '이승기',
    'yoonha': '윤하',
    'younha': '윤하',
    'lee seung chul': '이승철',
    'shin seung hun': '신승훈',
    'cho yong pil': '조용필',
    'lee moon sae': '이문세',
    'kim kwang seok': '김광석',
    'lim young woong': '임영웅',
    'young tak': '영탁',
    'lee chan won': '이찬원',
    'jeong dong won': '정동원',
    'kim ho joong': '김호중',
    'song ga in': '송가인',
    'jang min ho': '장민호',
    'ailee': '에일리',
}


def has_hangul(text: str) -> bool:
    """텍스트에 한글 음절이 포함되어 있는지 여부를 반환합니다."""
    return bool(re.search(r'[가-힣]', text or ''))


def prefer_korean_single_token(token: str) -> str:
    """단일 아티스트 토큰에서 한글 이름을 우선 추출합니다."""
    t = token.strip()
    if not t:
        return ''

    # 1. 사전 매핑 확인 (소문자 기준)
    t_lower = t.lower()
    if t_lower in KOREAN_ARTISTS_MAP:
        return KOREAN_ARTISTS_MAP[t_lower]

    # 2. 한글 (English) 형태 -> 한글만 추출 (예: '에픽하이 (Epik High)' -> '에픽하이')
    m_ko_en = re.match(r'^([가-힣0-9\s]+?)\s*\([A-Za-z0-9\s\.\,\'\&\-_]+\)$', t)
    if m_ko_en and m_ko_en.group(1).strip():
        return m_ko_en.group(1).strip()

    # 3. English (한글) 형태 -> 한글만 추출 (예: 'Young Jun (영준)' -> '영준')
    m_en_ko = re.match(r'^[A-Za-z0-9\s\.\,\'\&\-_]+\s*\(([가-힣0-9\s]+?)\)$', t)
    if m_en_ko and m_en_ko.group(1).strip():
        return m_en_ko.group(1).strip()

    # 4. 한글 English 공백 연결 형태 -> 한글만 추출 (예: '에픽하이 Epik High' -> '에픽하이')
    m_adj = re.match(r'^([가-힣]{2,}(?:\s+[가-힣]+)*)\s+[A-Za-z0-9\s\.\,\'\&\-_]+$', t)
    if m_adj and m_adj.group(1).strip():
        return m_adj.group(1).strip()

    return t


def prefer_korean_artist(artist_str: str) -> str:
    """
    아티스트 문자열(다중 아티스트 포함)에서 영문명이 아닌 한글 이름을 우선 추출합니다.
    (예: 'Dynamicduo, DJ Premier' -> '다이나믹 듀오, DJ Premier')
    (예: '리쌍 LeeSsang, 정인 Jung In' -> '리쌍, 정인')
    """
    if not artist_str:
        return ''

    # 쉼표, 슬래시, &, feat. 구분자로 분리
    delims = r'([,\&/]| feat\.? | ft\.? )'
    parts = re.split(delims, artist_str, flags=re.IGNORECASE)

    res_parts = []
    for p in parts:
        p_clean = p.strip()
        if not p_clean:
            continue
        # 구분자인 경우 표준 공백 처리
        if re.match(r'^([,\&/]|feat\.?|ft\.?)$', p_clean, re.IGNORECASE):
            if p_clean == ',':
                res_parts.append(', ')
            elif p_clean == '&':
                res_parts.append(' & ')
            elif p_clean == '/':
                res_parts.append(' / ')
            else:
                res_parts.append(f' {p_clean} ')
        else:
            res_parts.append(prefer_korean_single_token(p_clean))

    result = ''.join(res_parts).strip()
    return result or artist_str.strip()


def prefer_korean_title(title_str: str) -> str:
    """
    곡 제목에서 영문명이 아닌 한글 제목을 우선 추출합니다.
    (예: 'Then Then Then (그땐 그땐 그땐)' -> '그땐 그땐 그땐')
    (예: '소년이여 (A Boy)' -> '소년이여')
    (예: '땡땡땡 Dang Dang Dang' -> '땡땡땡')
    """
    if not title_str:
        return ''

    t = title_str.strip()

    # 1. English (한글) 형태 -> 한글 우선 추출 (예: 'Then Then Then (그땐 그땐 그땐)')
    m1 = re.match(r'^[A-Za-z0-9\s\.\,\!\?\~\'\"]+\s*\(([가-힣0-9\s\.\,\!\?\~\'\"]+)\)$', t)
    if m1 and len(m1.group(1).strip()) >= 2:
        return m1.group(1).strip()

    # 2. 한글 (English) 형태 -> 한글 우선 추출 (예: '소년이여 (A Boy)')
    m2 = re.match(r'^([가-힣0-9\s\.\,\!\?\~\'\"]+)\s*\([A-Za-z0-9\s\.\,\!\?\~\'\"]+\)$', t)
    if m2 and len(m2.group(1).strip()) >= 2:
        return m2.group(1).strip()

    # 3. 한글 English 연속 형태 -> 한글 우선 추출 (예: '땡땡땡 Dang Dang Dang')
    m3 = re.match(r'^([가-힣]{2,}(?:\s+[가-힣]+)*)\s+[A-Za-z0-9\s\.\,\!\?\~\'\"]+$', t)
    if m3 and m3.group(1).strip():
        return m3.group(1).strip()

    return t


def refine_korean_metadata(raw_title: str, artist: str, clean_title: str) -> Tuple[str, str]:
    """
    원본 영상 제목과 아티스트, 정제 제목을 종합하여
    가수 및 곡명이 영문명이 아닌 한글 이름으로 우선 저장되도록 조정합니다.
    """
    eff_artist = artist or ""
    eff_title = clean_title or raw_title or ""

    # 영상 제목이 '가수 - 노래' 형태인 경우
    if " - " in raw_title:
        parts = raw_title.split(" - ", 1)
        left_raw = parts[0].strip()
        right_raw = parts[1].strip()

        # 왼쪽 파트에 한글이 있고 현재 아티스트에는 한글이 없는 경우 (예: raw_title='다이나믹 듀오 - Go Back', artist='Dynamicduo')
        if has_hangul(left_raw) and not has_hangul(eff_artist):
            eff_artist = left_raw
        # 왼쪽 파트에 피처링/협업 아티스트가 더 온전하게 포함되어 있는 경우 (예: raw_title='Supreme Team, Young Jun - ...', artist='Supreme Team')
        elif eff_artist and eff_artist.lower() in left_raw.lower() and len(left_raw) > len(eff_artist):
            eff_artist = left_raw
        elif not eff_artist and left_raw:
            eff_artist = left_raw

        # 오른쪽 파트에 한글이 있고 제목에는 한글이 없는 경우
        if has_hangul(right_raw) and not has_hangul(eff_title):
            eff_title = right_raw

    # 아티스트 및 제목 한글 선호 처리
    final_artist = prefer_korean_artist(eff_artist)
    final_title = prefer_korean_title(eff_title)

    return final_artist, final_title
