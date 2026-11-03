# -*- coding: utf-8 -*-
"""
Google CDN & YouTube Native Subtitles / TimedText Lyrics Resolver.
Third-party dependency-free (0% 503 error) high-speed lyrics engine.
"""
import re
from typing import Optional, Tuple


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
        return lrc_text, True, "YouTube Subtitles (Synced)"
    elif plain_entries:
        plain_text = "\n".join(plain_entries)
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
            return "\n".join(lines)

    return None


def resolve_lyrics(
    title: str = "",
    artist: str = "",
    album: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    embedded_subtitles: Optional[str] = None,
    description: Optional[str] = None
) -> Tuple[Optional[str], bool, str]:
    """
    Google CDN & 유튜브 네이티브 가사 수집 엔진:
    - 외부 서드파티 API(알송, LRCLIB 등)의 503 에러나 레이트리밋 없이,
      구글 초고속 CDN에서 직접 음원 영상의 자막/텍스트를 밀리초 단위로 수집합니다.
    - 타임스탬프(싱크 정보)가 있는 경우: [mm:ss.xx] 표준 싱크 가사(LRC)로 변환 (is_synced = True)
    - 타임스탬프가 없는 경우: 정제된 일반 줄글 가사로 변환 (is_synced = False)

    반환값: (가사 내용, 싱크 가사 여부, 제공 출처)
    """
    # 1순위: 구글 CDN에서 다운로드된 유튜브 공식/자동 자막 변환
    if embedded_subtitles and len(embedded_subtitles.strip()) > 10:
        lrc_text, is_synced, source = parse_subtitles_to_lrc(embedded_subtitles)
        if lrc_text:
            return (lrc_text, is_synced, source)

    # 2순위: 영상 설명란(Description) 내 공식 가사 블록 추출 (일반 가사)
    if description:
        desc_lyrics = extract_lyrics_from_description(description)
        if desc_lyrics:
            return (desc_lyrics, False, "YouTube Description (Plain)")

    return (None, False, "None")

