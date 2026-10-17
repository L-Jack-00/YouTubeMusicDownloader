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


if __name__ == '__main__':
    unittest.main()
