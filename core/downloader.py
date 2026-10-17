# -*- coding: utf-8 -*-
"""
yt-dlp Core Downloader and Processing Pipeline.
"""
import os
import re
import glob
import shutil
import urllib.request
from typing import Optional, List, Dict, Any, Callable
import yt_dlp

from .types import DownloadState, TrackMetadata, DownloadOptions, ProgressCallback
from .ffmpeg_finder import find_ffmpeg_binary
from .image_util import crop_image_to_square, process_cover_image
from .lyrics import resolve_lyrics
from .tagger import tag_audio_file
from .alsong import clean_search_term
from .metadata_resolver import resolve_album_metadata
from .cookie_util import strip_ansi_codes, is_browser_cookie_locked


def _format_friendly_error(err_str: str, browser_name: str) -> str:
    cleaned = strip_ansi_codes(err_str)
    err_lower = cleaned.lower()
    
    if "failed to decrypt with dpapi" in err_lower or "10927" in err_lower:
        b_display = browser_name.upper() if browser_name else "크롬/엣지"
        return (
            f"[최신 브라우저 보안 정책 안내]\n"
            f"최신 버전의 {b_display} 브라우저는 윈도우 보안 정책으로 인해 "
            f"외부 프로그램의 직접 쿠키 추출을 차단합니다.\n\n"
            f"💡 해결 방법 (아래 중 하나 선택):\n"
            f"1. [가장 추천] 상단의 [❓ 쿠키 추출 가이드]를 참고하여 [📋 쿠키 직접 붙여넣기 (F12)] 이용 (확장 프로그램 불필요, 10초 완료)\n"
            f"2. '로그인 없음 (기본 128~160kbps)' 모드로 즉시 다운로드\n"
            f"3. Firefox(파이어폭스) 브라우저 연동 또는 cookies.txt 파일 직접 선택"
        )
    
    if "cookie database" in err_lower or "permission denied" in err_lower or "cookieloaderror" in err_lower:
        b_display = browser_name.upper() if browser_name else "브라우저"
        return (
            f"선택하신 브라우저({b_display})가 현재 실행 중(백그라운드 포함)이어서 쿠키 파일이 잠겨 있습니다.\n"
            f"(Chromium 기반 브라우저는 실행 중일 때 외부의 쿠키 파일 접근을 차단합니다)\n\n"
            f"해결 방법:\n"
            f"1. 상단의 [📋 쿠키 직접 붙여넣기 (F12)] 이용 (브라우저를 끄지 않아도 즉시 적용)\n"
            f"2. {b_display} 브라우저를 완전히 종료 후 다시 시도\n"
            f"3. '로그인 없음 (기본 음질)' 모드로 변경 후 다운로드"
        )
    
    if "does not exist" in err_lower or "is private" in err_lower or "404" in err_lower or "400" in err_lower:
        return (
            "재생목록을 찾을 수 없거나 '비공개' 상태의 링크입니다.\n\n"
            "💡 점검 사항:\n"
            "1. 유튜브 재생목록 설정이 '일부 공개' 또는 '공개'로 되어 있는지 확인해 주세요.\n"
            "   (재생목록이 '비공개'로 되어 있으면 링크가 있어도 다운로드할 수 없습니다)\n"
            "2. 본인의 비공개 재생목록이거나 '좋아요 표시한 음악'인 경우,\n"
            "   상단의 [📋 쿠키 직접 붙여넣기 (F12)] 버튼을 눌러 로그인 쿠키를 먼저 등록해 주셔야 합니다."
        )

    return cleaned


def normalize_youtube_url(url: str) -> str:
    """
    유튜브 및 유튜브 뮤직 URL 정규화:
    1. 유튜브 뮤직 전용 VL 접두사 제거 (VLPL... -> PL...)
    2. music.youtube.com 도메인을 www.youtube.com으로 정규화하여 400/404 에러 방지
    3. watch?v=...&list=PL... 형태인 경우 재생목록 URL로 변환하여 전체 곡 스캔 지원
    """
    if not url:
        return ""
    clean_url = url.strip()

    # list 파라미터 검색
    list_match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', clean_url)
    if list_match:
        p_id = list_match.group(1)
        # 유튜브 뮤직의 내부 뷰 접두사(VL) 제거
        if p_id.startswith("VL") and len(p_id) > 4:
            p_id = p_id[2:]
        # 좋아요 표시한 음악(LM) 등은 그대로 유지하되 일반 재생목록(PL, OLAK 등) 정규화
        if not p_id.startswith("RD"):  # 라디오 믹스가 아닌 경우
            return f"https://www.youtube.com/playlist?list={p_id}"
        else:
            clean_url = re.sub(r'list=VL', 'list=', clean_url)

    if "music.youtube.com/playlist" in clean_url:
        clean_url = clean_url.replace("music.youtube.com/playlist", "www.youtube.com/playlist")

    return clean_url


def ensure_js_runtime():
    """Deno 또는 Node.js 자바스크립트 런타임 경로를 탐색하여 환경 변수에 자동 바인딩합니다."""
    if shutil.which("deno") or shutil.which("node"):
        return
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates = glob.glob(os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "DenoLand.Deno*"))
        for c in candidates:
            if os.path.isfile(os.path.join(c, "deno.exe")):
                os.environ["PATH"] = c + os.pathsep + os.environ.get("PATH", "")
                return


def sanitize_filename(name: str) -> str:
    """Windows 파일시스템에서 허용되지 않는 특수문자 제거"""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = cleaned.strip(". ")
    return cleaned or "track"


def format_track_filename(naming_format: str, meta: TrackMetadata, track_index: int, ext: str) -> str:
    """
    선택된 파일 이름 저장 옵션에 따라 안전한 파일명을 생성합니다.
    - artist_title: 아티스트 - 곡명 (기본값)
    - title_artist: 곡명 - 아티스트
    - title_only: 곡명 단독
    - num_artist_title: 01. 아티스트 - 곡명
    - num_title: 01. 곡명
    """
    clean_title = sanitize_filename(meta.title or "Track")
    clean_artist = sanitize_filename(meta.artist or "")
    if clean_artist == "Unknown Artist":
        clean_artist = ""

    ext = ext.lstrip(".")

    # 트랙 번호: 원본 앨범 트랙 번호 우선, 없으면 track_index 사용
    t_num = meta.track_number if meta.track_number is not None else track_index

    if naming_format == "title_artist":
        base = f"{clean_title} - {clean_artist}" if clean_artist else clean_title
    elif naming_format == "title_only":
        base = clean_title
    elif naming_format == "num_artist_title":
        base = f"{t_num:02d}. {clean_artist} - {clean_title}" if clean_artist else f"{t_num:02d}. {clean_title}"
    elif naming_format == "num_title":
        base = f"{t_num:02d}. {clean_title}"
    else:
        # artist_title (기본값)
        base = f"{clean_artist} - {clean_title}" if clean_artist else clean_title

    return f"{base}.{ext}"


class YoutubeMusicDownloader:
    """
    유튜브 및 유튜브 뮤직 오디오 다운로드 및 메타데이터 후처리 엔진
    """

    def __init__(self, options: DownloadOptions):
        ensure_js_runtime()
        self.options = options
        self._is_cancelled = False
        self.ffmpeg_path = find_ffmpeg_binary()

    def cancel(self):
        """작업 취소 플래그 설정"""
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def scan_url(self, url: str) -> List[Dict[str, Any]]:
        """
        URL을 분석하여 단일 곡 또는 재생목록의 곡 정보 목록을 추출합니다 (다운로드 없음).
        """
        target_url = normalize_youtube_url(url)
        ydl_opts: Dict[str, Any] = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'remote_components': ['ejs:github'],
        }
        self._apply_cookie_opts(ydl_opts)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
        except Exception as e:
            friendly_msg = _format_friendly_error(str(e), self.options.browser_name)
            raise RuntimeError(friendly_msg) from e

        if not info:
            return []

        if 'entries' in info and info['entries'] is not None:
            # 재생목록인 경우
            entries_list = [e for e in info['entries'] if e]
            total_count = len(entries_list)
            is_album = bool("olak5uy_" in target_url.lower() or 'album' in str(info.get('title', '')).lower())
            tracks = []
            for idx, entry in enumerate(entries_list, start=1):
                tracks.append({
                    'title': entry.get('title') or f"Track {idx}",
                    'artist': entry.get('artist') or entry.get('uploader') or "",
                    'album': entry.get('album') or info.get('title') or "",
                    'duration': entry.get('duration'),
                    'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                    'index': idx,
                    'total': total_count,
                    'is_album': is_album,
                    'thumbnail': entry.get('thumbnail') or (entry.get('thumbnails')[-1]['url'] if entry.get('thumbnails') else None),
                })
            return tracks
        else:
            # 단일 곡인 경우
            return [{
                'title': info.get('title') or "Unknown Track",
                'artist': info.get('artist') or info.get('uploader') or "",
                'album': info.get('album') or "",
                'duration': info.get('duration'),
                'url': url,
                'index': 1,
                'total': 1,
                'is_album': False,
                'thumbnail': info.get('thumbnail') or (info.get('thumbnails')[-1]['url'] if info.get('thumbnails') else None),
            }]

    def download_track(
        self,
        url: str,
        track_index: int = 1,
        total_tracks: int = 1,
        is_album: bool = False,
        progress_cb: Optional[ProgressCallback] = None
    ) -> Optional[str]:
        """
        단일 트랙을 다운로드하고 가사/앨범아트/메타데이터를 태깅합니다.
        고유 temp_prefix 격리를 통해 트랙 간 메타데이터 및 에셋 혼선을 완전히 방지합니다.
        완료된 파일 경로를 반환합니다.
        """
        if self._is_cancelled:
            if progress_cb:
                progress_cb(DownloadState.CANCELLED, 0.0, "작업이 취소되었습니다.")
            return None

        os.makedirs(self.options.output_dir, exist_ok=True)

        if progress_cb:
            progress_cb(DownloadState.SCANNING, 5.0, f"[{track_index}/{total_tracks}] 음원 정보 확인 중...")

        # 고유 트랙 ID 생성 (동시 다운로드 및 폴더 내 파일 혼선 완전 차단)
        id_match = re.search(r'[?&]v=([a-zA-Z0-9_-]+)', url)
        video_id = id_match.group(1) if id_match else f"{track_index}_{os.getpid()}"
        temp_prefix = f"_ytm_{video_id}"

        # yt-dlp 옵션 구성 (전용 temp_prefix로 격리 다운로드)
        out_tmpl = os.path.join(self.options.output_dir, f"{temp_prefix}.%(ext)s")
        ydl_opts: Dict[str, Any] = {
            'outtmpl': out_tmpl,
            'writethumbnail': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ko', 'en'],
            'quiet': True,
            'no_warnings': True,
            'remote_components': ['ejs:github'],
        }

        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path

        self._apply_cookie_opts(ydl_opts)

        # 오디오 포맷 및 사후 처리기 설정
        if self.options.audio_format == "mp3":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self.options.mp3_bitrate.replace('k', ''),
            }]
        else:
            # m4a (AAC) 다이렉트 추출 우선
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]

        # 다운로드 진행률 콜백 후크
        def ydl_progress_hook(d):
            if self._is_cancelled:
                raise yt_dlp.utils.DownloadCancelled("사용자에 의해 다운로드가 취소되었습니다.")
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes') or 0
                if total_bytes > 0:
                    pct = 10.0 + (downloaded / total_bytes) * 50.0
                else:
                    pct = 30.0
                if progress_cb:
                    progress_cb(DownloadState.DOWNLOADING, pct, f"[{track_index}/{total_tracks}] 스트림 다운로드 중 ({pct:.1f}%)")
            elif d['status'] == 'finished':
                if progress_cb:
                    progress_cb(DownloadState.CONVERTING, 65.0, f"[{track_index}/{total_tracks}] 음원 파일 변환 중...")

        ydl_opts['progress_hooks'] = [ydl_progress_hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadCancelled:
            if progress_cb:
                progress_cb(DownloadState.CANCELLED, 0.0, "작업이 취소되었습니다.")
            return None
        except Exception as e:
            friendly_msg = _format_friendly_error(str(e), self.options.browser_name)
            if progress_cb:
                progress_cb(DownloadState.ERROR, 0.0, f"다운로드 오류: {friendly_msg}")
            return None

        if self._is_cancelled:
            self._cleanup_temp_files(self.options.output_dir, temp_prefix)
            return None

        # 결과 파일 탐색 (현재 트랙의 temp_prefix와 정확히 일치하는 파일만 탐색)
        target_ext = f".{self.options.audio_format}"
        audio_file = None
        if 'requested_downloads' in info:
            for req in info['requested_downloads']:
                fp = req.get('filepath')
                if fp and os.path.isfile(fp):
                    audio_file = fp
                    break

        if not audio_file or not os.path.isfile(audio_file):
            candidate = os.path.join(self.options.output_dir, f"{temp_prefix}{target_ext}")
            if os.path.isfile(candidate):
                audio_file = candidate
            else:
                for f in glob.glob(os.path.join(self.options.output_dir, f"{temp_prefix}*")):
                    if f.lower().endswith(target_ext):
                        audio_file = f
                        break

        if not audio_file or not os.path.isfile(audio_file):
            if progress_cb:
                progress_cb(DownloadState.ERROR, 0.0, "생성된 오디오 파일을 찾을 수 없습니다.")
            self._cleanup_temp_files(self.options.output_dir, temp_prefix)
            return None

        # 메타데이터 구성 (원본 앨범 트랙 정보 조회 보강)
        meta = self._extract_metadata(info, track_index, total_tracks, is_album_playlist=is_album)

        # 앨범 커버 수집 (현재 트랙의 전용 임시 파일에서만 탐색하여 이미지 섞임 완전 차단)
        cover_bytes = None
        thumb_candidates = (
            glob.glob(os.path.join(self.options.output_dir, f"{temp_prefix}*.jpg")) +
            glob.glob(os.path.join(self.options.output_dir, f"{temp_prefix}*.webp")) +
            glob.glob(os.path.join(self.options.output_dir, f"{temp_prefix}*.png"))
        )
        selected_thumb_file = None
        for t in thumb_candidates:
            if os.path.isfile(t):
                selected_thumb_file = t
                break

        if selected_thumb_file:
            try:
                with open(selected_thumb_file, "rb") as tf:
                    thumb_data = tf.read()
                cover_bytes = process_cover_image(
                    thumb_data,
                    crop_to_square=self.options.crop_square_cover
                )
            except Exception:
                pass
            try:
                os.remove(selected_thumb_file)
            except Exception:
                pass
        elif meta.thumbnail_url:
            try:
                req = urllib.request.Request(meta.thumbnail_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    t_data = resp.read()
                    cover_bytes = process_cover_image(
                        t_data,
                        crop_to_square=self.options.crop_square_cover
                    )
            except Exception:
                pass

        # 자막/가사 확인 (현재 트랙 전용 자막 파일만 탐색)
        embedded_sub_text = self._read_subtitle_files(self.options.output_dir, temp_prefix)

        # 가사 수집 (3단계 파이프라인)
        if self.options.embed_lyrics or self.options.save_lrc_file:
            if progress_cb:
                progress_cb(DownloadState.FETCHING_LYRICS, 75.0, f"[{track_index}/{total_tracks}] 가사 검색 중 (알송/LRCLIB)...")

            lyrics_text, is_synced, source_name = resolve_lyrics(
                title=meta.title,
                artist=meta.artist,
                album=meta.album,
                duration_seconds=meta.duration_seconds,
                embedded_subtitles=embedded_sub_text
            )
            meta.lyrics = lyrics_text
            meta.is_synced_lyrics = is_synced

        # 파일 이름 형식 적용 및 이름 변경
        naming_fmt = getattr(self.options, 'naming_format', 'artist_title')
        target_name = format_track_filename(
            naming_fmt,
            meta,
            track_index,
            self.options.audio_format
        )
        target_file_path = os.path.join(self.options.output_dir, target_name)

        if os.path.abspath(audio_file) != os.path.abspath(target_file_path):
            if os.path.isfile(target_file_path):
                try:
                    os.remove(target_file_path)
                except Exception:
                    pass
            try:
                os.rename(audio_file, target_file_path)
                audio_file = target_file_path
            except Exception:
                pass

        # 태깅 적용
        if progress_cb:
            progress_cb(DownloadState.TAGGING, 90.0, f"[{track_index}/{total_tracks}] 메타데이터 및 앨범아트 기록 중...")

        tag_audio_file(
            audio_file_path=audio_file,
            metadata=meta,
            cover_image_bytes=cover_bytes,
            save_lrc_file=self.options.save_lrc_file
        )

        # 현재 트랙의 잔여 임시 파일 정리
        self._cleanup_temp_files(self.options.output_dir, temp_prefix)

        if progress_cb:
            progress_cb(DownloadState.COMPLETED, 100.0, f"[{track_index}/{total_tracks}] 저장 완료: {os.path.basename(audio_file)}")

        return audio_file

    def _apply_cookie_opts(self, ydl_opts: Dict[str, Any]):
        """쿠키 옵션 적용"""
        if self.options.cookie_mode == "browser" and self.options.browser_name:
            ydl_opts['cookiesfrombrowser'] = (self.options.browser_name.lower(), )
        elif self.options.cookie_mode == "file" and self.options.cookie_file_path:
            if os.path.isfile(self.options.cookie_file_path):
                ydl_opts['cookiefile'] = self.options.cookie_file_path

    def _extract_metadata(
        self,
        info: Dict[str, Any],
        track_index: int,
        total_tracks: int,
        is_album_playlist: bool = False
    ) -> TrackMetadata:
        """yt-dlp 정보 및 iTunes 메타데이터 조회를 결합하여 원본 앨범의 정확한 곡 정보 구성"""
        raw_title = info.get('title') or ""
        artist = info.get('artist') or info.get('creator') or info.get('uploader') or ""
        album = info.get('album') or ""

        # 아티스트 - 제목 형태 분리 시도
        clean_title = raw_title
        if " - " in raw_title and not info.get('artist'):
            parts = raw_title.split(" - ", 1)
            artist = parts[0].strip()
            clean_title = parts[1].strip()

        clean_title = clean_search_term(clean_title)
        artist = clean_search_term(artist)

        release_year = None
        if info.get('release_year'):
            release_year = str(info.get('release_year'))
        elif info.get('upload_date') and len(str(info.get('upload_date'))) >= 4:
            release_year = str(info.get('upload_date'))[:4]

        thumb_url = info.get('thumbnail')
        if not thumb_url and info.get('thumbnails'):
            thumb_url = info['thumbnails'][-1].get('url')

        # 원본 앨범 트랙 정보 조회 (재생목록 순번이 아닌 원본 앨범 트랙 번호 수집)
        orig_track_number = info.get('track_number')
        orig_total_tracks = info.get('track_count')

        # yt-dlp에 원본 앨범 트랙 번호가 없거나 앨범명이 누락된 경우 정밀 보강
        resolved = resolve_album_metadata(
            title=clean_title or raw_title,
            artist=artist,
            album=album
        )
        if resolved:
            if not orig_track_number and resolved.get('track_number'):
                orig_track_number = resolved['track_number']
            if not orig_total_tracks and resolved.get('total_tracks'):
                orig_total_tracks = resolved['total_tracks']
            if (not album or album == clean_title) and resolved.get('album'):
                album = resolved['album']
            if (not artist or artist == "Unknown Artist") and resolved.get('artist'):
                artist = resolved['artist']
            if not release_year and resolved.get('release_year'):
                release_year = resolved['release_year']

        # 만약 원본 앨범 조회가 불가능한 경우:
        # 재생목록이 원본 앨범 자체(OLAK5uy_ 등)인 경우에만 track_index 적용,
        # 일반 재생목록(Liked Music, 임의 재생목록)에서는 엉뚱한 재생목록 순번을 앨범 트랙 번호로 넣지 않음
        if orig_track_number is None and is_album_playlist:
            orig_track_number = track_index
            orig_total_tracks = total_tracks

        return TrackMetadata(
            title=clean_title or raw_title,
            artist=artist or "Unknown Artist",
            album=album or clean_title or raw_title,
            release_year=release_year,
            track_number=orig_track_number,
            total_tracks=orig_total_tracks,
            duration_seconds=info.get('duration'),
            thumbnail_url=thumb_url,
            source_url=info.get('webpage_url') or ""
        )

    def _read_subtitle_files(self, directory: str, prefix: str) -> Optional[str]:
        """다운로드된 자막 파일 중 해당 트랙 prefix와 일치하는 파일만 읽어 반환합니다."""
        patterns = [f"{prefix}*.ko.vtt", f"{prefix}*.en.vtt", f"{prefix}*.vtt", f"{prefix}*.srt", f"{prefix}*.lrc"]
        for p in patterns:
            for sf in glob.glob(os.path.join(directory, p)):
                try:
                    with open(sf, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if content and len(content.strip()) > 20:
                            return content
                except Exception:
                    pass
        return None

    def _cleanup_temp_files(self, directory: str, prefix: str):
        """해당 트랙과 관련된 모든 잔여 임시 파일(_ytm_... 자막/썸네일 등) 안전 정리"""
        for f in glob.glob(os.path.join(directory, f"{prefix}*")):
            try:
                os.remove(f)
            except Exception:
                pass
