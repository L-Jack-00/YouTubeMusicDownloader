# -*- coding: utf-8 -*-
"""
AlSong (알송) SOAP API Lyrics Search Client
"""
import re
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
import requests


ALSONG_ENDPOINT = "http://ws.altools.co.kr/Server/ALSongServer.asmx"


def clean_search_term(term: str) -> str:
    """
    검색 정확도를 높이기 위해 제목이나 아티스트명에서
    불필요한 특수문자, 괄호 태그([MV], (Official Audio), feat. 등)를 정제합니다.
    """
    if not term:
        return ""
    # 대괄호, 중괄호 내용 제거 ([MV], [Official], etc.)
    cleaned = re.sub(r'\[.*?\]', '', term)
    # 소괄호 내용 중 일반적인 태그 제거
    cleaned = re.sub(r'\((?:Official|Audio|Video|MV|Live|Remastered|feat\.?|ft\.?).*?\)', '', cleaned, flags=re.IGNORECASE)
    # 앞뒤 공백 및 연속 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or term.strip()


def parse_alsong_xml(xml_bytes: bytes) -> Optional[str]:
    """
    알송 응답 XML에서 strLyric 텍스트를 파싱하여 표준 줄바꿈으로 변환합니다.
    """
    try:
        root = ET.fromstring(xml_bytes)
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag_name == 'strLyric' and elem.text:
                raw_text = elem.text.strip()
                if raw_text:
                    # <br> 태그를 표준 줄바꿈으로 변환
                    formatted = raw_text.replace('<br>', '\n').replace('<BR>', '\n')
                    return formatted
    except Exception:
        pass
    return None


def fetch_alsong_lyrics(title: str, artist: str, timeout: int = 5) -> Optional[str]:
    """
    알송 서버에 곡명 및 아티스트명으로 싱크 가사를 요청합니다.
    성공 시 타임스탬프가 포함된 가사 문자열을 반환합니다.
    """
    c_title = clean_search_term(title)
    c_artist = clean_search_term(artist)

    # 1차 시도: 정제된 검색어 / 2차 시도: 원본 검색어
    search_pairs = [(c_title, c_artist)]
    if (c_title, c_artist) != (title.strip(), artist.strip()):
        search_pairs.append((title.strip(), artist.strip()))

    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "User-Agent": "ALSong",
    }

    for s_title, s_artist in search_pairs:
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <SearchLyric2 xmlns="http://tempuri.org/">
      <strTitle>{s_title}</strTitle>
      <strArtistName>{s_artist}</strArtistName>
      <nPageNum>0</nPageNum>
    </SearchLyric2>
  </soap12:Body>
</soap12:Envelope>"""

        try:
            response = requests.post(
                ALSONG_ENDPOINT,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=timeout
            )
            if response.status_code == 200:
                lyrics = parse_alsong_xml(response.content)
                if lyrics:
                    return lyrics
        except Exception:
            continue

    return None
