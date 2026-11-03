# -*- coding: utf-8 -*-
"""
Image processing utilities for album art cropping and optimization.
"""
import io
from typing import Optional, Union
from PIL import Image


def detect_and_trim_black_bars(img: Image.Image, tolerance: int = 25) -> Image.Image:
    """
    유튜브 썸네일의 상/하단 레터박스 및 좌/우 필러박스 블랙바를 정밀 감지하여 잘라냅니다.
    이미 1:1 정방형인 이미지나 원본 앨범아트는 손상 없이 보호됩니다.
    """
    w, h = img.size
    # 이미 정방형에 가까운 경우(앨범아트 원본 등) 블랙바 탐색을 건너뜀
    if abs(w - h) <= 5:
        return img

    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 그레이스케일 변환 및 블랙 임계값 필터링 (압축 노이즈 필터링)
    gray = img.convert('L')
    lut = [0 if i <= tolerance else 255 for i in range(256)]
    bw = gray.point(lut, mode='L')
    bbox = bw.getbbox()

    if not bbox:
        return img

    left, top, right, bottom = bbox
    new_w = right - left
    new_h = bottom - top

    # 최소 80x80 이상의 유효 콘텐츠가 있고 가장자리에 유의미한 블랙바가 있는 경우 크롭
    if new_w >= 80 and new_h >= 80:
        if top > 5 or (h - bottom) > 5 or left > 5 or (w - right) > 5:
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
