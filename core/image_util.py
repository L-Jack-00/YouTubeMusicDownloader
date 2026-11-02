# -*- coding: utf-8 -*-
"""
Image processing utilities for album art cropping and optimization.
"""
import io
from typing import Optional, Union
from PIL import Image


def detect_and_trim_black_bars(img: Image.Image, tolerance: int = 25) -> Image.Image:
    """
    유튜브 4:3 썸네일(hqdefault, sddefault)의 상/하단 레터박스 블랙바 및
    필러박스 블랙바를 정밀 감지하여 잘라냅니다.
    이미 1:1 정방형인 이미지나 유효한 콘텐츠는 보호됩니다.
    """
    w, h = img.size
    # 이미 정방형에 가까운 경우(앨범아트 원본 등) 블랙바 탐색을 건너뜀
    if abs(w - h) <= 5:
        return img

    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 1. 상단 블랙바 검사 (최대 높이의 25%까지 탐색)
    top = 0
    max_top_search = int(h * 0.25)
    step_x = max(1, w // 50)
    for y in range(max_top_search):
        is_row_black = all(
            all(c <= tolerance for c in img.getpixel((x, y)))
            for x in range(0, w, step_x)
        )
        if is_row_black:
            top = y + 1
        else:
            break

    # 2. 하단 블랙바 검사 (최대 높이의 25%까지 탐색)
    bottom = h
    min_bottom_search = int(h * 0.75)
    for y in range(h - 1, min_bottom_search, -1):
        is_row_black = all(
            all(c <= tolerance for c in img.getpixel((x, y)))
            for x in range(0, w, step_x)
        )
        if is_row_black:
            bottom = y
        else:
            break

    # 3. 좌측 필러박스 검사 (최대 너비의 25%까지 탐색)
    left = 0
    max_left_search = int(w * 0.25)
    step_y = max(1, h // 50)
    for x in range(max_left_search):
        is_col_black = all(
            all(c <= tolerance for c in img.getpixel((x, y)))
            for y in range(top, bottom, step_y)
        )
        if is_col_black:
            left = x + 1
        else:
            break

    # 4. 우측 필러박스 검사 (최대 너비의 25%까지 탐색)
    right = w
    min_right_search = int(w * 0.75)
    for x in range(w - 1, min_right_search, -1):
        is_col_black = all(
            all(c <= tolerance for c in img.getpixel((x, y)))
            for y in range(top, bottom, step_y)
        )
        if is_col_black:
            right = x
        else:
            break

    # 유효 영역 검증 후 크롭
    new_w = right - left
    new_h = bottom - top
    if new_w >= 50 and new_h >= 50:
        if top > 5 or bottom < h - 5 or left > 5 or right < w - 5:
            return img.crop((left, top, right, bottom))
    return img


def process_cover_image(
    image_input: Union[str, bytes],
    crop_to_square: bool = True,
    target_size: int = 800,
    jpeg_quality: int = 90
) -> Optional[bytes]:
    """
    이미지(WEBP, PNG, JPEG 등)를 읽어 레터박스 블랙바를 정밀 보정하고,
    정방형 크롭 또는 원본 비율을 유지하며 표준 고품질 JPEG 바이트로 변환합니다.
    """
    try:
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        else:
            img = Image.open(image_input)

        # RGBA나 P 모드일 경우 RGB로 변환 (흰색/투명도 보정)
        if img.mode in ("RGBA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                rgb_img.paste(img, mask=img.split()[3])
            else:
                rgb_img.paste(img.convert("RGBA"))
            img = rgb_img
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 유튜브 4:3 썸네일 등 레터박스/필러박스 블랙바 자동 감지 및 제거
        img = detect_and_trim_black_bars(img)

        if crop_to_square:
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim) // 2
            top = (h - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            img = img.crop((left, top, right, bottom))
            if min_dim != target_size:
                img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        else:
            w, h = img.size
            max_dim = max(w, h)
            if max_dim > 1000:
                scale = 1000.0 / max_dim
                img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
        return out_buffer.getvalue()
    except Exception:
        return None


def crop_image_to_square(
    image_input: Union[str, bytes],
    target_size: int = 800,
    jpeg_quality: int = 90
) -> Optional[bytes]:
    """
    이미지를 1:1 정사각형 중앙 크롭하고 최적화된 JPEG 바이트로 변환합니다.
    """
    return process_cover_image(
        image_input,
        crop_to_square=True,
        target_size=target_size,
        jpeg_quality=jpeg_quality
    )


def crop_image_file_in_place(file_path: str, target_size: int = 800) -> bool:
    """
    지정된 이미지 파일을 읽어 1:1 정방형으로 크롭 후 덮어씁니다.
    """
    try:
        data = crop_image_to_square(file_path, target_size=target_size)
        if data:
            with open(file_path, "wb") as f:
                f.write(data)
            return True
    except Exception:
        pass
    return False
