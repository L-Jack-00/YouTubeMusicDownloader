# -*- coding: utf-8 -*-
"""
Headless unit tests for Pillow 1:1 square image cropping.
"""
import io
import unittest
from PIL import Image
from core.image_util import crop_image_to_square


class TestImageUtil(unittest.TestCase):

    def test_crop_16_to_9_to_square(self):
        # 1280x720 16:9 합성 이미지 생성
        src_img = Image.new("RGB", (1280, 720), color=(255, 50, 50))
        buf = io.BytesIO()
        src_img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        # 800x800 정사각형 크롭 수행
        cropped_bytes = crop_image_to_square(raw_bytes, target_size=800)
        self.assertIsNotNone(cropped_bytes)

        # 결과 검증
        result_img = Image.open(io.BytesIO(cropped_bytes))
        self.assertEqual(result_img.size, (800, 800))
        self.assertEqual(result_img.format, "JPEG")

    def test_crop_rgba_image_preserves_colors_and_converts_to_rgb(self):
        # RGBA 이미지 생성
        src_img = Image.new("RGBA", (500, 1000), color=(0, 200, 100, 255))
        buf = io.BytesIO()
        src_img.save(buf, format="PNG")

        cropped_bytes = crop_image_to_square(buf.getvalue(), target_size=500)
        self.assertIsNotNone(cropped_bytes)

        result_img = Image.open(io.BytesIO(cropped_bytes))
        self.assertEqual(result_img.size, (500, 500))
        self.assertEqual(result_img.mode, "RGB")

    def test_process_cover_image_without_square_crop_preserves_aspect_ratio(self):
        from core.image_util import process_cover_image
        src_img = Image.new("RGB", (600, 400), color=(100, 150, 200))
        buf = io.BytesIO()
        src_img.save(buf, format="WEBP")

        # crop_to_square=False 시 원본 비율 유지하면서 JPEG 변환
        jpeg_bytes = process_cover_image(buf.getvalue(), crop_to_square=False)
        self.assertIsNotNone(jpeg_bytes)

        result_img = Image.open(io.BytesIO(jpeg_bytes))
        self.assertEqual(result_img.size, (600, 400))
        self.assertEqual(result_img.format, "JPEG")

    def test_detect_and_trim_black_bars_on_4_3_thumbnail(self):
        from core.image_util import detect_and_trim_black_bars
        # 640x480 4:3 썸네일에 상/하단 60px 블랙바 추가 (유튜브 hqdefault/sddefault 규격)
        src_img = Image.new("RGB", (640, 480), color=(0, 0, 0))
        # 중앙 16:9 영역(640x360)에 유효 색상 채우기
        center_content = Image.new("RGB", (640, 360), color=(200, 100, 50))
        src_img.paste(center_content, (0, 60))

        trimmed = detect_and_trim_black_bars(src_img)
        self.assertEqual(trimmed.size, (640, 360))

    def test_crop_letterboxed_thumbnail_to_pure_square(self):
        from core.image_util import process_cover_image
        # 640x480 블랙바 썸네일 생성 후 정방형 크롭 시 블랙바 없이 정사각형(800x800) 추출
        src_img = Image.new("RGB", (640, 480), color=(0, 0, 0))
        center_content = Image.new("RGB", (640, 360), color=(200, 100, 50))
        src_img.paste(center_content, (0, 60))

        buf = io.BytesIO()
        src_img.save(buf, format="JPEG")

        jpeg_bytes = process_cover_image(buf.getvalue(), crop_to_square=True, target_size=800)
        self.assertIsNotNone(jpeg_bytes)

        result_img = Image.open(io.BytesIO(jpeg_bytes))
        self.assertEqual(result_img.size, (800, 800))
        # 상단 코너가 검은색이 아니라 중앙 콘텐츠 색상(200, 100, 50)이어야 함
        corner_pixel = result_img.getpixel((0, 0))
        self.assertGreater(corner_pixel[0], 50)

    def test_square_image_does_not_trim_dark_borders(self):
        from core.image_util import detect_and_trim_black_bars
        # 이미 500x500 정사각형인 이미지는 어두운 배경이 있더라도 잘리지 않고 보존되어야 함
        src_img = Image.new("RGB", (500, 500), color=(0, 0, 0))
        inner = Image.new("RGB", (300, 300), color=(255, 255, 255))
        src_img.paste(inner, (100, 100))

        result = detect_and_trim_black_bars(src_img)
        self.assertEqual(result.size, (500, 500))


if __name__ == '__main__':
    unittest.main()
