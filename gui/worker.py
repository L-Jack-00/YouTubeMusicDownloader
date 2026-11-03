# -*- coding: utf-8 -*-
"""
Asynchronous background download worker using PyQt6 QThread.
Includes automated retry pass for failed playlist items.
"""
import time
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtCore import QThread, pyqtSignal

from core.types import DownloadState, DownloadOptions
from core.downloader import YoutubeMusicDownloader


class DownloadWorker(QThread):
    """
    UI 멈춤 방지를 위한 비동기 백그라운드 다운로드 작업자
    """
    # 시그널 정의
    progress_changed = pyqtSignal(str, float, str)  # 상태, 퍼센트, 세부 안내
    log_emitted = pyqtSignal(str)                   # 로그 텍스트
    track_completed = pyqtSignal(str, str)          # 제목, 파일 경로
    batch_finished = pyqtSignal(int, int)           # 성공 수, 전체 수
    work_cancelled = pyqtSignal()                   # 취소 완료
    error_occurred = pyqtSignal(str)                # 오류 메시지

    def __init__(self, url: str, options: DownloadOptions, parent=None):
        super().__init__(parent)
        self.url = url
        self.options = options
        self.downloader = YoutubeMusicDownloader(options)
        self._is_stopped = False

    def stop(self):
        """작업 안전 중지"""
        self._is_stopped = True
        self.downloader.cancel()

    def run(self):
        """스레드 메인 루프 실행"""
        try:
            self.progress_changed.emit("정보 분석 중", 5.0, "입력된 링크의 음원 및 재생목록 정보를 조회하고 있습니다...")
            self.log_emitted.emit(f"[*] 링크 분석 시작: {self.url}")
            self.log_emitted.emit("[*] 재생목록 규모에 따라 전체 곡 목록을 불러오는 데 수십 초가 걸릴 수 있습니다. 잠시만 기다려 주세요...")

            # 1. 메타데이터 사전 스캔
            tracks: List[Dict[str, Any]] = self.downloader.scan_url(self.url)
            if not tracks:
                self.error_occurred.emit("음원 정보를 찾을 수 없거나 접근이 제한된 링크입니다.")
                return

            total_count = len(tracks)
            self.log_emitted.emit(f"[*] 총 {total_count}개의 음원을 확인했습니다.")

            succeeded_count = 0
            failed_tracks: List[Tuple[int, Dict[str, Any]]] = []

            # 2. 개별 음원 순차 다운로드
            for idx, track_info in enumerate(tracks, start=1):
                if self._is_stopped:
                    self.log_emitted.emit("[-] 사용자에 의해 작업이 취소되었습니다.")
                    self.work_cancelled.emit()
                    return

                track_title = track_info.get('title') or f"Track {idx}"
                track_url = track_info.get('url') or self.url

                self.log_emitted.emit(f"\n--- [{idx}/{total_count}] {track_title} 처리 시작 ---")

                def inner_cb(state: DownloadState, pct: float, msg: str):
                    if self._is_stopped:
                        return
                    # 전체 배치 진행률 계산
                    base_pct = ((idx - 1) / total_count) * 100.0
                    track_contribution = (pct / 100.0) * (100.0 / total_count)
                    total_pct = min(100.0, base_pct + track_contribution)
                    self.progress_changed.emit(state.value, total_pct, msg)

                saved_path = self.downloader.download_track(
                    url=track_url,
                    track_index=idx,
                    total_tracks=total_count,
                    is_album=track_info.get('is_album', False),
                    progress_cb=inner_cb
                )

                if self._is_stopped:
                    self.work_cancelled.emit()
                    return

                if saved_path:
                    succeeded_count += 1
                    self.track_completed.emit(track_title, saved_path)
                    self.log_emitted.emit(f"[+] 다운로드 및 태깅 완료: {saved_path}")
                else:
                    failed_tracks.append((idx, track_info))
                    self.log_emitted.emit(f"[!] '{track_title}' 다운로드 실패 (마지막에 자동 재시도 예정)")

            # 3. 실패한 음원 자동 재시도 단계 (네트워크 지연, 일시적 오류 자동 복구)
            if failed_tracks and not self._is_stopped:
                retry_total = len(failed_tracks)
                self.log_emitted.emit("\n" + "=" * 55)
                self.log_emitted.emit(f"[*] 다운로드되지 않은 {retry_total}개 음원에 대한 자동 재시도를 준비합니다.")
                self.log_emitted.emit("[*] 유튜브 요청 제한(Rate Limit) 해제를 위해 15초간 대기(쿨다운)합니다...")
                self.log_emitted.emit("=" * 55)

                # 15초 쿨다운 카운트다운 (1초마다 취소 상태 체크)
                for remaining in range(15, 0, -1):
                    if self._is_stopped:
                        self.work_cancelled.emit()
                        return
                    self.progress_changed.emit(
                        "재시도 쿨다운",
                        93.0,
                        f"유튜브 요청 제한 해제 대기 중... ({remaining}초)"
                    )
                    time.sleep(1.0)

                if self._is_stopped:
                    self.work_cancelled.emit()
                    return

                self.log_emitted.emit("[*] 쿨다운 완료! 실패 음원 재다운로드를 시작합니다.\n")

                remaining_failed = []

                for retry_idx, (orig_idx, track_info) in enumerate(failed_tracks, start=1):
                    if self._is_stopped:
                        self.work_cancelled.emit()
                        return

                    track_title = track_info.get('title') or f"Track {orig_idx}"
                    track_url = track_info.get('url') or self.url

                    self.log_emitted.emit(f"\n[재시도 {retry_idx}/{retry_total}] {track_title}")
                    self.progress_changed.emit(
                        f"재시도 ({retry_idx}/{retry_total})",
                        95.0,
                        f"[{retry_idx}/{retry_total}] '{track_title}' 재다운로드 시도 중..."
                    )

                    # 각 재시도 곡 사이 1.5초 안정 간격
                    time.sleep(1.5)

                    def retry_cb(state: DownloadState, pct: float, msg: str):
                        if self._is_stopped:
                            return
                        self.progress_changed.emit(f"재시도 ({retry_idx}/{retry_total})", 95.0, f"'{track_title}': {msg}")

                    saved_path = self.downloader.download_track(
                        url=track_url,
                        track_index=orig_idx,
                        total_tracks=total_count,
                        is_album=track_info.get('is_album', False),
                        progress_cb=retry_cb
                    )

                    if self._is_stopped:
                        self.work_cancelled.emit()
                        return

                    if saved_path:
                        succeeded_count += 1
                        self.track_completed.emit(track_title, saved_path)
                        self.log_emitted.emit(f"[+] 재시도 성공: {saved_path}")
                    else:
                        remaining_failed.append(track_title)
                        self.log_emitted.emit(f"[-] 최종 실패: '{track_title}'")

                if remaining_failed:
                    self.log_emitted.emit(f"\n[안내] 최종 다운로드 실패 음원 ({len(remaining_failed)}개):")
                    for rf in remaining_failed:
                        self.log_emitted.emit(f"  - {rf}")

            # 4. 전체 완료 보고
            self.progress_changed.emit("완료", 100.0, f"총 {succeeded_count}/{total_count}개 음원 처리 완료!")
            self.batch_finished.emit(succeeded_count, total_count)
            self.log_emitted.emit(f"\n[완료] 총 {succeeded_count}/{total_count}개의 음원이 저장되었습니다.")

        except Exception as e:
            from core.cookie_util import strip_ansi_codes
            cleaned_err = strip_ansi_codes(str(e))
            self.error_occurred.emit(cleaned_err)
            self.log_emitted.emit(f"[오류] {cleaned_err}")
