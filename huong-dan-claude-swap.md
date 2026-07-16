# Hướng dẫn cài claude-swap trên Windows (chi tiết nhất có thể)

## Bước 1: Cài Python (nếu chưa có)

Truy cập: [python.org/downloads](https://www.python.org/downloads/)

Tải Python 3.12 hoặc mới hơn (khuyến nghị 3.13).

> **Quan trọng:** Khi cài, tick vào ô **"Add python.exe to PATH"**.

## Bước 2: Cài uv (cách khuyến nghị và nhanh nhất)

Mở PowerShell (chạy với quyền bình thường, không cần Admin) và chạy lệnh sau:

```powershell
# Cài uv (tool quản lý Python rất nhanh)
irm https://astral.sh/uv/install.ps1 | iex
```
nếu bị thoát thì chạy
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Sau khi cài xong, đóng PowerShell và mở lại để PATH cập nhật.

## Bước 3: Cài claude-swap

Trong PowerShell mới mở, chạy:

```powershell
uv tool install claude-swap
```

Nếu thành công, bạn sẽ thấy dòng thông báo cài đặt xong. Kiểm tra bằng lệnh:

```powershell
cswap --version
```

## Bước 4: Thiết lập 2 account (Team + Pro)

Chạy lệnh thêm account đầu tiên:

```powershell
cswap --add
```

→ Nó sẽ mở browser để bạn login Team account.

Hoặc add account đang active:

```powershell
cswap --add-account
```

Xem danh sách account:

```powershell
cswap --list
```

## Bước 5: Sử dụng (rất đơn giản)

Chuyển sang Pro:

```powershell
cswap --switch-to <số thứ tự hoặc email>
```

Chuyển sang Team: dùng cùng lệnh trên, thay `<số thứ tự hoặc email>` bằng số thứ tự/email của account Team (lấy từ `cswap --list`):

```powershell
cswap --switch-to <số thứ tự hoặc email của Team>
```

Sau khi switch, đóng và mở lại Claude panel trong VS Code (hoặc restart VS Code) để áp dụng.

### Mẹo dùng trong VS Code

- Bạn có thể tạo 2 Terminal profile trong VS Code để dễ switch.
- Hoặc gõ trực tiếp lệnh `cswap --switch-to <tên/email>` trong terminal của VS Code.
