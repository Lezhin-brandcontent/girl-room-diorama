# 소녀 방 아이소메트릭 디오라마

웹툰·웹소설 소개용 인터랙티브 마이크로사이트 시안. Blender로 방을 **스크립트 모델링**하고, 웹(Three.js)에서 돌려 보며 소품을 눌러 작품·영상·사이트로 연결한다.

> 상태: 사내 테스트 버전. 레진 작품 표지, 액자 이미지, 레진·봄툰 로고, 봄툰 소설 표지·줄거리, 유튜브 영상은 **외부 공개 전 권리 확인 필요**.

## 폴더 구조

| 경로 | 내용 |
| --- | --- |
| `diorama/build_diorama.py` | Blender 모델 생성 스크립트 (방·가구 전부 코드로 생성) |
| `diorama/girl_room.blend` | 스크립트 실행 결과 Blender 파일 |
| `web/diorama.html` | 웹 뷰어 (Three.js r160 + GSAP, CDN 로드) |
| `web/diorama/` | `girl_room.glb`(모델), 벽지·러그·액자·모니터·책 표지 이미지, `books/`(레진 작품), `novels/`(봄툰 소설), `videos.json`(유튜브) |
| `references/` | 작업에 사용한 레퍼런스 이미지 |
| `tools/` | 작품 데이터 수집, 레이아웃 확인, 브라우저 테스트 스크립트 |

## 실행

```bash
# 1) 모델 다시 만들기 (Blender 4.5)
cd diorama
"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b --python build_diorama.py -- render
cp girl_room.glb ../web/diorama/          # 웹에서 쓰는 모델 갱신 (preview.png 는 미리보기 렌더)

# 2) 웹 보기 (file:// 로는 안 열림 → 로컬 서버 필요)
cd ../web
python -m http.server 8765
# → http://127.0.0.1:8765/diorama.html
```

## 좌표 규칙

- Blender 좌표: 바닥 x,y ∈ [-2, 2], 왼쪽 벽 x = -2, 뒷벽 y = +2, 카메라는 (+x, -y, +z) 방향
- three.js 변환: Blender (x, y, z) → three (x, z, -y)
- 클릭 소품은 `prop_<id>` Empty 아래에 부품을 묶는다. 웹은 이 이름으로 소품을 판정한다 (`INFO` 객체에 동작 정의)
- 뒷벽 가구 간격은 약 0.21로 같게 맞춤: 왼벽 | 책장(`kx`) | 수납장+TV(`CX`) | 책상(`dx`) | 바닥 끝

## 소품 동작 (`web/diorama.html` 의 `INFO`)

| 소품 | 동작 |
| --- | --- |
| TV | 정면 이동 → 영상 목록 + TV 화면 위에 유튜브 재생 (`videos.json`) |
| 책장 | 패널 없이 정면 확대 → 책(레진 작품 6권 랜덤)을 누르면 작품 카드. 어떤 책이든 같은 시점 유지 |
| 액자 | 정면 이동 → 공지 카드 |
| 컴퓨터 | 모니터 정면 이동 → "사이트 들어가기" (레진코믹스) |
| 스툴 위 책 | 다가가며 표지가 펼쳐짐 → 봄툰 소설 랜덤 1편 + "작품 보러가기" |
| 스탠드 | 켜기/끄기 (방 분위기 전환) |
| 미니전구 | 켜기/끄기 (켜면 방 전체 저녁 톤) |

## 작품 데이터 갱신

목록은 수집 시점의 스냅샷이며 자동 갱신되지 않는다. 성인 작품은 상세 페이지에서 확인 후 제외한다.

```bash
# 레진: 메인 HTML 저장 후 N권 수집
curl -sL https://www.lezhin.com/ko -o lezhin_home.html
python tools/fetch_lezhin.py lezhin_home.html web/diorama/books 18

# 봄툰 소설: 메인 HTML 저장 후 수집 (e북 중복 정리는 수동)
curl -sL https://www.bomtoon.com/bom/novel/main -o bomtoon_main.html
python tools/fetch_bomtoon.py web/diorama/novels bomtoon_main.html
```

## 테스트

- `tools/check_book.py`: Playwright 로 책 펼치기·버튼·새 탭 열림을 확인하는 예시 (서버 실행 후 `python tools/check_book.py`, 스크린샷은 `bedshot/` 에 저장)
- `tools/bbox.py`: 가구 영역(bounding box) 출력 → `blender -b diorama/girl_room.blend --python tools/bbox.py`

## 알려진 한계

- 벽지가 이음매 없는 타일이 아니라 반전 반복 경계에 별이 붙어 보이는 곳이 있음
- 러그 원본이 비스듬한 그림이라 바닥에서 살짝 납작해 보임
- 봄툰 표지 이미지가 작아(315×415) 가까이 보면 흐림
- 유튜브는 광고·자동재생 정책 영향을 받음
