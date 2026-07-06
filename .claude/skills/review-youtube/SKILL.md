---
name: review-youtube
description: Tự động kích hoạt khi người dùng dán một link YouTube (youtube.com hoặc youtu.be) vào chat, hoặc khi họ yêu cầu "xem/tóm tắt/review video này giúp tôi". Lấy tiêu đề, mô tả và transcript/phụ đề của video rồi tóm tắt nội dung bằng tiếng Việt mà không cần hỏi lại.
---

Skill này lấy transcript của một video YouTube (không tải video) bằng
driver `driver.py`, rồi Claude đọc transcript đó và viết tóm tắt trực
tiếp cho người dùng. Đường dẫn dưới đây tính từ gốc repo (`<unit>/`).

## Kích hoạt tự động

Khi tin nhắn người dùng chứa một URL `youtube.com/watch?v=...`,
`youtu.be/...` hoặc `youtube.com/shorts/...` — **tự chạy driver ngay,
không hỏi xác nhận trước**, rồi trả về bản tóm tắt. Đây là hành vi
người dùng đã yêu cầu rõ ràng cho skill này.

## Chuẩn bị (đã cài, chỉ cần làm lại nếu máy khác)

```bash
python -m pip install --user yt-dlp curl_cffi
```

`curl_cffi` là tuỳ chọn nhưng nên có — yt-dlp dùng nó để giả lập
TLS/browser fingerprint, tăng tỉ lệ vượt qua chặn bot của YouTube.

## Chạy (agent path)

```bash
python .claude/skills/review-youtube/driver.py "<youtube-url>"
```

In ra một dòng JSON:

```json
{
  "video_id": "aircAruvnKk",
  "title": "But what is a neural network? | Deep learning chapter 1",
  "uploader": "3Blue1Brown",
  "duration_sec": 1058,
  "upload_date": "20171005",
  "description": "...",
  "transcript_lang": "en",
  "transcript_is_auto": false,
  "transcript": "This is a 3. It's sloppily written..."
}
```

Đọc JSON này, rồi viết tóm tắt tiếng Việt cho người dùng: ý chính,
các luận điểm/mốc thời gian đáng chú ý, kết luận. Không cần gọi thêm
bước "summarize" riêng — Claude đọc `transcript` trực tiếp trong
context và tóm tắt.

- `transcript_is_auto: true` = phụ đề tự động (ASR), có thể sai chính
  tả/dấu câu — báo cho người dùng biết mức độ tin cậy thấp hơn.
- `transcript_lang` **không nhất thiết là tiếng Việt hay tiếng Anh**
  (có thể là ngôn ngữ gốc của video, vd. `ko`, `ar`...). Không sao —
  Claude tự đọc hiểu và tóm tắt sang tiếng Việt, không cần dịch qua
  YouTube.
- Nếu script thoát mã 2 (`"transcript": null`, có `"note"`): video
  không có phụ đề nào. Tóm tắt tạm dựa trên `title` + `description`,
  và nói rõ với người dùng là không có transcript nên tóm tắt bị hạn
  chế.
- Nếu script thoát mã 1 (raise `RuntimeError` in ra stderr): URL sai,
  video bị xoá/riêng tư/region-block — báo lỗi rõ ràng cho người dùng,
  đừng đoán mò nội dung.

## Test nhanh (đã chạy thật, dùng để kiểm tra driver còn hoạt động)

```bash
python .claude/skills/review-youtube/driver.py "https://youtu.be/aircAruvnKk"
```

Kỳ vọng: JSON có `"transcript_lang": "en"`, `"transcript_is_auto": false`,
`transcript` dài ~18000 ký tự nói về neural network.

## Gotchas

- **Đừng để yt-dlp/YouTube dịch phụ đề (`tlang=`).** Yêu cầu bản dịch
  tự động (vd. phụ đề gốc tiếng Hàn dịch sang `en`) gần như luôn bị
  YouTube trả `HTTP 429 Too Many Requests` — đã tái hiện nhiều lần khi
  build skill này. Vì vậy `driver.py` luôn chọn track **gốc** (URL
  không có `tlang=`) bất kể ngôn ngữ, không bao giờ yêu cầu dịch.
  Việc "dịch" giao lại hoàn toàn cho Claude ở bước tóm tắt.
- **Không cần ffmpeg.** Driver không tải video hay dùng
  `yt-dlp --write-sub` (bước đó cần ffmpeg để convert định dạng) — nó
  chỉ gọi `yt-dlp -j` lấy metadata rồi tự tải track phụ đề JSON3 qua
  `urllib` và parse tay. Cảnh báo "ffmpeg not found" nếu thấy ở nơi
  khác (vd. khi tự chạy `yt-dlp --write-auto-sub` để debug) có thể bỏ
  qua, không ảnh hưởng driver này.
- **Console Windows là cp1252, không phải UTF-8.** In trực tiếp
  transcript tiếng Hàn/Ả Rập/Việt ra `python -c "print(...)"` trong
  PowerShell/Git Bash sẽ bay `UnicodeEncodeError`. `driver.py` đã tự
  `sys.stdout.reconfigure(encoding="utf-8")` nên bản thân nó an toàn;
  nếu viết script phụ để đọc lại JSON, nhớ làm tương tự hoặc ghi ra
  file thay vì in thẳng ra console.
- **Phụ đề thủ công (`subtitles`) có thể có nhiều ngôn ngữ cộng đồng**
  (vd. video 3Blue1Brown có cả `ar`, `en`...). `driver.py` ưu tiên
  `vi`, `en` trong số các track hiện có trước khi lấy đại track đầu
  tiên trong dict — nếu không ưu tiên, thứ tự dict trả về ngẫu nhiên
  theo YouTube, dễ tóm tắt nhầm ngôn ngữ không mong muốn.
- **Video auto-caption gắn tag "-orig"** (vd. `ko-orig`) khi có cả bản
  dịch song song dưới key ngôn ngữ trần — đây cũng là track gốc hợp lệ,
  không cần xử lý gì thêm.

## Troubleshooting

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `HTTP Error 429: Too Many Requests` khi tải phụ đề | Đang yêu cầu track dịch (`tlang=`) hoặc gọi quá nhiều lần liên tiếp trong thời gian ngắn | Đảm bảo dùng đúng `driver.py` (không tự thêm `--sub-lang` ép ngôn ngữ khác ngôn ngữ gốc); nếu vẫn 429, đợi ~1-2 phút rồi thử lại |
| `yt-dlp failed: ERROR: [youtube] ...: Video unavailable` | Sai video ID, video bị xoá/riêng tư/tuổi hạn chế | Báo người dùng kiểm tra lại link |
| `No supported JavaScript runtime` (warning) | yt-dlp cảnh báo thiếu deno cho việc giải mã signature khi tải file video | Không ảnh hưởng vì driver không tải video, chỉ lấy JSON metadata + phụ đề — bỏ qua |
| `"transcript": null` với `note` | Video không có phụ đề nào (thủ công lẫn tự động) | Tóm tắt dựa trên title/description, nói rõ giới hạn |
