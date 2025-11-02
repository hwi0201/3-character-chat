# Story Images Directory

이 디렉토리는 3-character-chat 애플리케이션의 스토리 관련 이미지를 저장합니다.

## 현재 이미지

### placeholder.png
- **용도**: 개발 단계에서 사용하는 임시 이미지
- **크기**: 1920x1080 (16:9 aspect ratio)
- **설명**: "Placeholder Image" 텍스트가 중앙에 배치된 보라색 배경 이미지
- **생성 날짜**: 2025-11-02

## 이미지 사양

| 파일명 | 해상도 | 종횡비 | 용도 |
|--------|--------|--------|------|
| placeholder.png | 1920x1080 | 16:9 | 개발 및 테스트용 이미지 |

## 추가 예정 이미지

개발 단계에서 필요한 다른 스토리 이미지들이 여기에 추가될 예정입니다.

## 생성 방법

Pillow(PIL) 라이브러리를 사용하여 생성합니다:

```python
from PIL import Image, ImageDraw, ImageFont

# 이미지 생성
img = Image.new('RGB', (1920, 1080), color=(102, 126, 234))
draw = ImageDraw.Draw(img)

# 텍스트 추가
text = "Placeholder Image"
font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 80)

# 중앙 정렬
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (1920 - text_width) // 2
y = (1080 - text_height) // 2

draw.text((x, y), text, fill=(255, 255, 255), font=font)

# 저장
img.save("placeholder.png")
```

## 필수 라이브러리

- Pillow >= 12.0.0
