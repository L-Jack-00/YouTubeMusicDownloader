# -*- coding: utf-8 -*-
"""
Multi-Tier High-Precision Lyrics Engine with Language-Aware Routing & Romanization Filter.

Routing Policy:
  - Korean Track (국내 가요/K-POP):
      1. AlSong (알송 - 국내 최고 싱크 가사 DB)
      2. YouTube Subtitles (유튜브 공식/자동 한국어 자막)
      3. YouTube Description (유튜브 영상 설명란 공식 가사 블록)
      4. LRCLIB (한글 가사 필수 매칭)
      5. Musixmatch (한글 가사 필수 매칭)
      * 한글 발음을 영문으로 적은 로마자 가사(Romanized)는 100% 원천 기각(Reject).
  - Foreign Pop Track (해외 팝송):
      1. LRCLIB (원문 글로벌 싱크 가사 DB)
      2. Musixmatch (글로벌 최대 상용 싱크 가사 DB)
      3. YouTube Subtitles (원어/영문 공식 자막)
      4. AlSong (알송 폴백)
      5. YouTube Description (설명란 폴백)
"""
import re
from typing import Optional, Tuple
from .alsong import fetch_alsong_lyrics
from .lrclib import fetch_lrclib_lyrics, get_artist_search_candidates
from .musixmatch import fetch_musixmatch_lyrics
from .lyrics_detector import (
    is_romanized_korean_lyrics,
    is_korean_track,
    has_hangul
)


def parse_subtitles_to_lrc(sub_text: str) -> Tuple[Optional[str], bool, str]:
    """
    WebVTT, SRT 또는 텍스트 형식의 자막을 정밀 분석하여:
    1) 타임스탬프(싱크 정보)가 있으면 표준 [mm:ss.xx] 싱크 가사(LRC)로 변환
    2) 타임스탬프가 없으면 불필요한 메타데이터 헤더를 제거한 일반 줄글 가사로 변환
    반환값: (가사 텍스트, 싱크 가사 여부, 수집 출처)
    """
    if not sub_text or len(sub_text.strip()) < 5:
        return None, False, "None"

    # 타임스탬프 탐색 정규식:
    # 00:01:23.450 --> 00:01:25.000 또는 01:23.450 --> 01:25.000 (마침표 또는 쉼표)
    time_pattern = re.compile(
        r'(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{2,3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{2,3})'
    )

    lines = sub_text.splitlines()
    lrc_entries = []
    plain_entries = []
    current_time_tag = None

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # WEBVTT 메타데이터 라인 스킵
        if line_clean.startswith("WEBVTT") or line_clean.startswith("Kind:") or line_clean.startswith("Language:"):
            continue
        if line_clean.isdigit():  # SRT 숫자 번호 라인 스킵
            continue

        match = time_pattern.search(line_clean)
        if match:
            h_str, m_str, s_str, ms_str = match.group(1), match.group(2), match.group(3), match.group(4)
            hours = int(h_str) if h_str else 0
            minutes = int(m_str) + hours * 60
            seconds = int(s_str)
            ms = ms_str[:2].ljust(2, '0')
            current_time_tag = f"[{minutes:02d}:{seconds:02d}.{ms}]"
        else:
            # HTML 태그 제거 (<c>, </c>, <00:00:00>, <b>, <i> 등)
            text = re.sub(r'<[^>]+>', '', line_clean).strip()
            if not text:
                continue

            if current_time_tag:
                # 유튜브 롤링 캡션 중복 방지
                if lrc_entries and lrc_entries[-1][1] == text:
                    continue
                lrc_entries.append((current_time_tag, text))
                current_time_tag = None
            else:
                plain_entries.append(text)

    if lrc_entries:
        lrc_text = "\n".join(f"{tag} {txt}" for tag, txt in lrc_entries)
        if not is_romanized_korean_lyrics(lrc_text):
            return lrc_text, True, "YouTube Subtitles (Synced)"
    elif plain_entries:
        plain_text = "\n".join(plain_entries)
        if not is_romanized_korean_lyrics(plain_text):
            return plain_text, False, "YouTube Subtitles (Plain)"

    return None, False, "None"


def extract_lyrics_from_description(desc: str) -> Optional[str]:
    """
    영상 설명(Description)에 작성된 가사 텍스트를 추출하여 일반 줄글 가사로 변환합니다.
    """
    if not desc:
        return None

    # [가사], [Lyrics], 가사:, Lyrics: 블록 탐색
    m = re.search(
        r'(?:\[가사\]|\[Lyrics\]|가사\s*:|Lyrics\s*:)\s*\n+(.+?)(?=\n\s*(?:\[|\bCredit|\bComposed|\bArranged|\bLyrics by|\b작사|\b작곡|https?://|$))',
        desc,
        re.DOTALL | re.IGNORECASE
    )
    if m:
        extracted = m.group(1).strip()
        lines = [l.strip() for l in extracted.splitlines() if l.strip()]
        if len(lines) >= 3:
            candidate = "\n".join(lines)
            if not is_romanized_korean_lyrics(candidate):
                return candidate

    return None


def resolve_lyrics(
    title: str = "",
    artist: str = "",
    album: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    embedded_subtitles: Optional[str] = None,
    description: Optional[str] = None,
    channel: Optional[str] = None
) -> Tuple[Optional[str], bool, str]:
    """
    곡 언어/국적 감지 및 5계층 동적 라우팅 가사 수집 파이프라인:

    [한국 곡 모드 - KR Track]
      1순위: 알송 (AlSong - 국내 정식 한글 싱크 가사)
      2순위: YouTube Subtitles (유튜브 공식/자동 한국어 자막)
      3순위: YouTube Description (영상 설명란 공식 한글 가사)
      4순위: LRCLIB (한글 가사 필수 매칭)
      5순위: Musixmatch (한글 가사 필수 매칭)
      * 로마자 발음 가사(Romanized Korean)는 100% 감지 및 원천 배제.

    [해외 팝송 모드 - Foreign Pop Track]
      1순위: LRCLIB (글로벌 원문 싱크 가사 DB)
      2순위: Musixmatch (글로벌 싱크 가사 DB)
      3순위: YouTube Subtitles (영문/원어 자막)
      4순위: 알송 (AlSong 해외곡 싱크 가사 폴백)
      5순위: YouTube Description

    반환값: (가사 내용, 싱크 가사 여부, 제공 출처)
    """
    is_kr = is_korean_track(
        title=title,
        artist=artist,
        album=album,
        channel=channel,
        description=description,
        embedded_subtitles=embedded_subtitles
    )

    if is_kr:
        # ==========================================
        # [A] 한국 곡 처리 파이프라인 (한글 가사 최우선)
        # ==========================================
        hangul_plain_fallback: Optional[Tuple[str, str]] = None
        foreign_synced_fallback: Optional[Tuple[str, str]] = None
        foreign_plain_fallback: Optional[Tuple[str, str]] = None

        # 1순위: 알송 (AlSong) 싱크 가사 조회
        if title:
            try:
                alsong_res = fetch_alsong_lyrics(title=title, artist=artist, timeout=4)
                if alsong_res:
                    alsong_text, alsong_synced = alsong_res
                    if not is_romanized_korean_lyrics(alsong_text):
                        if has_hangul(alsong_text):
                            if alsong_synced:
                                return (alsong_text, True, "AlSong (Synced)")
                            elif not hangul_plain_fallback:
                                hangul_plain_fallback = (alsong_text, "AlSong (Plain)")
                        else:
                            # 한국 가수의 영문 곡(예: Dynamite 등)에 대비한 백업
                            if alsong_synced and not foreign_synced_fallback:
                                foreign_synced_fallback = (alsong_text, "AlSong (Synced)")
            except Exception:
                pass

        # 2순위: 구글 CDN 유튜브 공식/자동 한국어 자막
        if embedded_subtitles and len(embedded_subtitles.strip()) > 10:
            sub_text, sub_synced, sub_source = parse_subtitles_to_lrc(embedded_subtitles)
            if sub_text and not is_romanized_korean_lyrics(sub_text):
                if has_hangul(sub_text):
                    if sub_synced:
                        return (sub_text, True, sub_source)
                    elif not hangul_plain_fallback:
                        hangul_plain_fallback = (sub_text, sub_source)
                elif sub_synced and not foreign_synced_fallback:
                    foreign_synced_fallback = (sub_text, sub_source)

        # 3순위: 영상 설명란(Description) 공식 가사 텍스트 블록
        if description:
            desc_lyrics = extract_lyrics_from_description(description)
            if desc_lyrics and not is_romanized_korean_lyrics(desc_lyrics):
                if has_hangul(desc_lyrics) and not hangul_plain_fallback:
                    hangul_plain_fallback = (desc_lyrics, "YouTube Description (Plain)")

        # 4순위: LRCLIB (한국어 가사 엄격 매칭)
        if title:
            try:
                lrclib_res = fetch_lrclib_lyrics(
                    title=title,
                    artist=artist,
                    album=album,
                    duration_seconds=duration_seconds,
                    timeout=4,
                    require_korean=True
                )
                if lrclib_res:
                    lrclib_text, lrclib_synced = lrclib_res
                    if has_hangul(lrclib_text) and not is_romanized_korean_lyrics(lrclib_text):
                        if lrclib_synced:
                            return (lrclib_text, True, "LRCLIB (Synced)")
                        elif not hangul_plain_fallback:
                            hangul_plain_fallback = (lrclib_text, "LRCLIB (Plain)")
            except Exception:
                pass

        # 5순위: Musixmatch (한국어 가사 엄격 매칭)
        if title:
            try:
                mxm_res = fetch_musixmatch_lyrics(
                    title=title,
                    artist=artist,
                    album=album,
                    duration_seconds=duration_seconds,
                    timeout=4,
                    require_korean=True
                )
                if mxm_res:
                    mxm_text, mxm_synced = mxm_res
                    if has_hangul(mxm_text) and not is_romanized_korean_lyrics(mxm_text):
                        if mxm_synced:
                            return (mxm_text, True, "Musixmatch (Synced)")
                        elif not hangul_plain_fallback:
                            hangul_plain_fallback = (mxm_text, "Musixmatch (Plain)")
            except Exception:
                pass

        # 한국어 싱크 가사를 못 찾았으나 상위 단계에서 한글 줄글 가사를 찾은 경우 반환
        if hangul_plain_fallback:
            return (hangul_plain_fallback[0], False, hangul_plain_fallback[1])

        # 한국 곡이지만 전곡 영어 가사곡(예: BTS 'Dynamite', Rosé 'APT.' 등)인 경우 영문 가사 조회
        if title:
            try:
                lrclib_en = fetch_lrclib_lyrics(
                    title=title,
                    artist=artist,
                    album=album,
                    duration_seconds=duration_seconds,
                    timeout=4,
                    require_korean=False
                )
                if lrclib_en:
                    en_text, en_synced = lrclib_en
                    # 로마자 가사가 아닐 때만 정식 영어 가사로 채택
                    if not is_romanized_korean_lyrics(en_text):
                        if en_synced:
                            return (en_text, True, "LRCLIB (Synced)")
                        elif not foreign_plain_fallback:
                            foreign_plain_fallback = (en_text, "LRCLIB (Plain)")
            except Exception:
                pass

        if foreign_synced_fallback:
            return (foreign_synced_fallback[0], True, foreign_synced_fallback[1])
        if foreign_plain_fallback:
            return (foreign_plain_fallback[0], False, foreign_plain_fallback[1])

    else:
        # ==========================================
        # [B] 해외 팝송 처리 파이프라인 (원문 싱크 가사 우선)
        # ==========================================
        plain_fallback: Optional[Tuple[str, str]] = None

        # 1순위: LRCLIB (글로벌 오픈소스 싱크 가사 DB)
        if title:
            try:
                lrclib_res = fetch_lrclib_lyrics(
                    title=title,
                    artist=artist,
                    album=album,
                    duration_seconds=duration_seconds,
                    timeout=4,
                    require_korean=False
                )
                if lrclib_res:
                    lrclib_text, lrclib_synced = lrclib_res
                    if not is_romanized_korean_lyrics(lrclib_text):
                        if lrclib_synced:
                            return (lrclib_text, True, "LRCLIB (Synced)")
                        elif not plain_fallback:
                            plain_fallback = (lrclib_text, "LRCLIB (Plain)")
            except Exception:
                pass

        # 2순위: Musixmatch 글로벌 싱크 가사 조회
        if title:
            try:
                mxm_res = fetch_musixmatch_lyrics(
                    title=title,
                    artist=artist,
                    album=album,
                    duration_seconds=duration_seconds,
                    timeout=4,
                    require_korean=False
                )
                if mxm_res:
                    mxm_text, mxm_synced = mxm_res
                    if not is_romanized_korean_lyrics(mxm_text):
                        if mxm_synced:
                            return (mxm_text, True, "Musixmatch (Synced)")
                        elif not plain_fallback:
                            plain_fallback = (mxm_text, "Musixmatch (Plain)")
            except Exception:
                pass

        # 3순위: 구글 CDN 유튜브 공식 자막 변환
        if embedded_subtitles and len(embedded_subtitles.strip()) > 10:
            sub_text, sub_synced, sub_source = parse_subtitles_to_lrc(embedded_subtitles)
            if sub_text and not is_romanized_korean_lyrics(sub_text):
                if sub_synced:
                    return (sub_text, True, sub_source)
                elif not plain_fallback:
                    plain_fallback = (sub_text, sub_source)

        # 4순위: 알송 (AlSong) 싱크 가사 폴백
        if title:
            try:
                alsong_res = fetch_alsong_lyrics(title=title, artist=artist, timeout=4)
                if alsong_res:
                    alsong_text, alsong_synced = alsong_res
                    if not is_romanized_korean_lyrics(alsong_text):
                        if alsong_synced:
                            return (alsong_text, True, "AlSong (Synced)")
                        elif not plain_fallback:
                            plain_fallback = (alsong_text, "AlSong (Plain)")
            except Exception:
                pass

        # 5순위: 영상 설명란(Description) 내 공식 가사 블록 추출
        if description:
            desc_lyrics = extract_lyrics_from_description(description)
            if desc_lyrics and not is_romanized_korean_lyrics(desc_lyrics) and not plain_fallback:
                plain_fallback = (desc_lyrics, "YouTube Description (Plain)")

        if plain_fallback:
            return (plain_fallback[0], False, plain_fallback[1])

    return (None, False, "None")
