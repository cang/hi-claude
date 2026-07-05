# Hướng dẫn Claude Code (VS Code) — Từ cơ bản đến automation

> Lưu ý: Claude Code cập nhật liên tục. Tài liệu chuẩn: https://docs.claude.com/en/docs/claude-code/overview — hãy đối chiếu khi có khác biệt.

## 0. Thiết lập nhanh

Claude Code chạy trong terminal, và có extension "Claude Code for VS Code" để tích hợp vào IDE (thấy diff inline, chia sẻ selection, dùng panel bên cạnh editor).

```bash
npm install -g @anthropic-ai/claude-code
cd du-an-cua-ban
claude          # đăng nhập lần đầu bằng tài khoản Claude hoặc API key
```

Trong VS Code: cài extension Claude Code từ Marketplace, hoặc mở terminal tích hợp và gõ `claude` — extension thường tự kích hoạt khi phát hiện Claude Code chạy trong terminal của VS Code. Phím tắt hữu ích: `Shift+Tab` để chuyển giữa chế độ thường / auto-accept / **Plan mode** (Claude lập kế hoạch trước, không sửa file cho đến khi bạn duyệt).

Chạy `/init` ở lần đầu vào một repo để Claude tự sinh file `CLAUDE.md` — bộ nhớ dự án của nó.

---

## 1. Slash commands, Hooks, Plugins

### 1.1 Slash commands có sẵn

Một số lệnh bạn sẽ dùng hàng ngày: `/clear` (xóa sạch context, bắt đầu phiên mới), `/compact` (nén lịch sử hội thoại để tiết kiệm token), `/context` (xem context đang chiếm bao nhiêu), `/model` (đổi model, ví dụ Opus ↔ Sonnet ↔ Haiku), `/agents` (quản lý sub-agents), `/mcp` (quản lý MCP servers), `/rewind` (quay lại checkpoint trước đó), `/init`, `/help`.

### 1.2 Custom slash commands

Tự tạo lệnh riêng bằng cách đặt file Markdown vào `.claude/commands/` (theo dự án) hoặc `~/.claude/commands/` (toàn cục). Tên file = tên lệnh.

`.claude/commands/fix-issue.md`:

```markdown
---
description: Phân tích và sửa một GitHub issue
allowed-tools: Bash(gh issue view:*), Bash(git:*)
---
Hãy phân tích và sửa issue số $ARGUMENTS:
1. Chạy `gh issue view $ARGUMENTS` để đọc issue
2. Tìm các file liên quan trong codebase
3. Viết fix kèm test
4. Chạy test và lint trước khi kết luận
```

Dùng: `/fix-issue 123`. Biến `$ARGUMENTS` nhận toàn bộ phần sau lệnh (hoặc `$1`, `$2` cho từng tham số). Bạn cũng có thể nhúng output lệnh shell bằng cú pháp `!`command`` và tham chiếu file bằng `@path/to/file` ngay trong command.

Đây là cách rẻ nhất để "đóng gói quy trình": mọi việc bạn lặp lại quá 2 lần (review PR, viết changelog, tạo migration...) nên trở thành một command.

### 1.3 Hooks

Hooks là script shell chạy **tự động và có tính quyết định** (deterministic) tại các sự kiện vòng đời — khác với việc "nhờ" Claude nhớ làm gì đó (nó có thể quên), hook luôn chạy. Cấu hình trong `.claude/settings.json` hoặc qua lệnh `/hooks`.

Các event chính: `PreToolUse` (trước khi chạy tool — có thể **chặn** tool), `PostToolUse` (sau khi tool chạy xong), `UserPromptSubmit` (khi bạn gửi prompt), `Stop` (khi Claude kết thúc lượt), `SessionStart`, `Notification`.

Ví dụ kinh điển — tự format code sau mỗi lần Claude sửa file:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "npx prettier --write \"$CLAUDE_FILE_PATHS\" 2>/dev/null || true" }
        ]
      }
    ]
  }
}
```

Ví dụ chặn hành vi nguy hiểm — `PreToolUse` với matcher `Bash`, script đọc JSON từ stdin, nếu thấy lệnh chứa `rm -rf` thì exit code 2 (chặn và báo lý do cho Claude). Đây là lớp bảo vệ cứng mà prompt không thay được.

Các use case đáng làm: chạy test/lint sau mỗi edit, gửi thông báo desktop khi Claude cần bạn duyệt, ghi log mọi lệnh bash để audit, chặn edit vào file `.env` hay thư mục `migrations/`.

### 1.4 Plugins

Plugin là gói đóng hộp gồm slash commands + agents + hooks + MCP servers, cài một phát dùng ngay và chia sẻ được cho team. Quản lý qua lệnh `/plugin` — bạn có thể thêm marketplace (một repo Git chứa danh sách plugin) rồi cài từ đó:

```
/plugin marketplace add ten-org/ten-repo
/plugin install ten-plugin@ten-marketplace
```

Tự viết plugin: tạo repo với file `.claude-plugin/plugin.json` (metadata) và các thư mục `commands/`, `agents/`, `hooks/`. Với team, đây là cách chuẩn hóa workflow: mọi người cài cùng một plugin là có cùng bộ lệnh, cùng quy tắc hook.

---

## 2. Sub-agents & Agent teams

### 2.1 Sub-agents là gì và vì sao quan trọng

Sub-agent là một "Claude con" có **context window riêng**, system prompt riêng, và bộ tool giới hạn riêng. Claude chính (orchestrator) giao việc cho nó qua tool `Task`, nó làm xong trả về **bản tóm tắt kết quả** — toàn bộ quá trình đọc file, mò mẫm, thử sai của nó KHÔNG chiếm context của phiên chính.

Hai lợi ích: (1) tiết kiệm context khủng khiếp cho project lớn, (2) chuyên môn hóa — agent review code có prompt khác agent viết test.

### 2.2 Tạo sub-agent

Chạy `/agents` để tạo bằng giao diện, hoặc tự viết file vào `.claude/agents/` (project) / `~/.claude/agents/` (user):

`.claude/agents/code-reviewer.md`:

```markdown
---
name: code-reviewer
description: Chuyên review code. Dùng CHỦ ĐỘNG sau khi có thay đổi code đáng kể.
tools: Read, Grep, Glob, Bash
model: sonnet
---
Bạn là senior code reviewer. Quy trình:
1. Chạy `git diff` xem thay đổi gần nhất
2. Kiểm tra: bảo mật (secret lộ, injection), lỗi logic, error handling, tên biến
3. Trả về danh sách vấn đề phân theo mức Critical / Warning / Suggestion, kèm cách sửa cụ thể
Chỉ báo cáo, không tự sửa code.
```

Trường `description` rất quan trọng: Claude chính dựa vào nó để quyết định **khi nào tự động** gọi agent này. Viết kiểu "Use proactively when..." nếu muốn nó được gọi không cần bạn nhắc. Trường `model` cho phép agent rẻ tiền (haiku) làm việc đơn giản, agent đắt (opus) làm việc khó.

### 2.3 Agent teams — mô hình orchestrator

Pattern phổ biến: Claude chính đóng vai trò điều phối, chia task lớn thành các mảnh độc lập rồi phái nhiều sub-agent chạy **song song**. Ví dụ prompt:

> "Hãy dùng 3 agent song song: một agent tìm hiểu cách module auth hoạt động, một agent liệt kê mọi chỗ gọi API thanh toán, một agent đọc schema database. Sau đó tổng hợp và đề xuất kế hoạch refactor."

Bộ agent hay dùng trong thực tế: `explorer` (chỉ đọc, chuyên khảo sát codebase), `test-writer`, `code-reviewer`, `debugger`, `docs-writer`. Nguyên tắc: sub-agent nhận nhiệm vụ **cụ thể, tự chứa** (self-contained) vì nó không thấy hội thoại của bạn — mọi ngữ cảnh cần thiết phải nằm trong đề bài giao cho nó.

---

## 3. Parallel work với Git worktrees

Vấn đề: một phiên Claude chỉ nên làm một việc trong một working directory. Muốn 3 việc chạy song song trên cùng repo mà không giẫm chân nhau? Git worktree cho phép checkout nhiều branch ra nhiều thư mục vật lý khác nhau, **dùng chung một `.git`** (không tốn dung lượng clone lại, không phải stash).

```bash
# Từ repo chính
git worktree add ../myapp-feature-auth  -b feature/auth
git worktree add ../myapp-fix-payment   -b fix/payment
git worktree add ../myapp-refactor-db   -b refactor/db

# Mở 3 cửa sổ VS Code / 3 tab terminal, mỗi cái một thư mục
cd ../myapp-feature-auth && claude   # instance 1
cd ../myapp-fix-payment  && claude   # instance 2
cd ../myapp-refactor-db  && claude   # instance 3
```

Mỗi instance Claude làm việc độc lập trên branch riêng; xong việc thì tạo PR như bình thường. Dọn dẹp:

```bash
git worktree remove ../myapp-feature-auth
git worktree prune
```

Mẹo thực tế: nhớ chạy `npm install` (hoặc tương đương) trong từng worktree vì `node_modules` không được chia sẻ; viết một script `new-worktree.sh` tự động hóa tạo worktree + cài dependency + mở VS Code; đặt tên thư mục theo branch để khỏi lẫn. Bạn cũng nên biến chính script này thành một slash command.

---

## 4. Context & token management

Context window là tài nguyên quý nhất. Khi nó đầy, Claude auto-compact (tự nén) và chất lượng suy giảm — mục tiêu là **chủ động** quản lý trước khi chuyện đó xảy ra.

**Theo dõi:** `/context` cho biết phần trăm context đã dùng và cái gì đang chiếm chỗ (system prompt, MCP tools, file đã đọc, hội thoại).

**`/clear` thường xuyên hơn bạn nghĩ.** Mỗi khi chuyển sang task không liên quan, hãy `/clear`. Lịch sử task cũ chỉ làm nhiễu và đốt token ở mọi lượt sau.

**`/compact` có chủ đích.** Thay vì chờ auto-compact, chạy `/compact tập trung vào quyết định thiết kế và các file đã sửa` tại điểm dừng tự nhiên (vừa xong một milestone) — bạn kiểm soát cái gì được giữ lại.

**CLAUDE.md gọn và đắt.** File này được nạp vào MỌI lượt hội thoại, nên mỗi dòng thừa là token trả tiền mãi mãi. Nên chứa: lệnh build/test/lint, quy ước code, cấu trúc thư mục cấp cao, những "bẫy" đặc thù của repo. Không nên chứa: tài liệu dài, lịch sử, những thứ Claude tự tìm được. Dùng phím `#` trong phiên để thêm ghi nhớ nhanh vào CLAUDE.md.

**Đừng dán cả file to vào chat.** Chỉ trỏ đường dẫn (`@src/services/payment.ts`) và để Claude đọc phần nó cần, hoặc tốt hơn — giao cho sub-agent đọc và tóm tắt.

**Dùng sub-agent làm "bộ lọc context":** việc khảo sát ("tìm mọi chỗ dùng hàm X", "hiểu module Y hoạt động thế nào") nên đi qua sub-agent để phiên chính chỉ nhận bản tóm tắt vài trăm token thay vì hàng chục nghìn token file thô.

---

## 5. Deploy API lên cloud với Modal

Modal (modal.com) là nền tảng serverless cho Python — rất hợp với workflow "nhờ Claude viết API rồi deploy trong 2 phút". Không cần Dockerfile, không cần quản lý server, scale về 0 khi không dùng.

```bash
pip install modal
modal setup        # mở trình duyệt xác thực
```

Ví dụ FastAPI hoàn chỉnh — `api.py`:

```python
import modal

app = modal.App("my-api")
image = modal.Image.debian_slim().pip_install("fastapi[standard]")

@app.function(image=image, secrets=[modal.Secret.from_name("my-secrets")])
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    web_app = FastAPI()

    @web_app.get("/health")
    def health():
        return {"status": "ok"}

    @web_app.post("/predict")
    def predict(data: dict):
        # logic của bạn ở đây
        return {"result": data}

    return web_app
```

```bash
modal serve api.py    # dev: hot-reload, URL tạm
modal deploy api.py   # production: URL cố định dạng https://<user>--my-api-fastapi-app.modal.run
```

Những mảnh ghép hay dùng: `modal.Secret.from_name(...)` cho API key (tạo secret trên dashboard Modal, không bao giờ hardcode); `gpu="A10G"` trong `@app.function` nếu cần GPU cho model ML; `modal.Volume` để lưu trữ bền vững; `@modal.fastapi_endpoint()` nếu chỉ cần một endpoint đơn lẻ thay vì cả app.

Kết hợp với Claude Code: bảo Claude "viết endpoint X, deploy bằng modal deploy, rồi curl thử endpoint và sửa nếu lỗi" — nó có thể tự chạy trọn vòng lặp viết → deploy → test vì mọi thứ đều là lệnh terminal. Lưu ý: hãy tự quản lý việc `modal setup`/xác thực và secrets của bạn, đừng dán token vào hội thoại.

---

## 6. Các tính năng nâng cao đáng chú ý

**Plan mode (`Shift+Tab` hai lần).** Claude chỉ đọc và lập kế hoạch, không sửa gì cho đến khi bạn duyệt kế hoạch. Bắt buộc dùng cho task lớn — chi phí sửa một kế hoạch sai rẻ hơn nhiều so với sửa 20 file bị đổi sai hướng.

**Extended thinking.** Thêm từ khóa "think", "think hard", "ultrathink" vào prompt cho bài toán khó (thiết kế kiến trúc, debug hắc búa) — Claude được cấp thêm ngân sách suy nghĩ trước khi hành động.

**Checkpoints & `/rewind`.** Claude Code tự lưu trạng thái code trước mỗi thay đổi; `/rewind` (hoặc Esc hai lần) cho phép quay về điểm trước đó — cả code lẫn hội thoại. Đây là lưới an toàn để bạn dám cho Claude thử nghiệm mạnh tay.

**Headless mode (`claude -p`).** Chạy Claude không tương tác, dùng trong script/CI:

```bash
claude -p "chạy toàn bộ test, nếu fail thì sửa cho pass, xuất tóm tắt" --output-format json
```

Kèm `--allowedTools "Bash(npm test:*),Edit"` để giới hạn quyền. Đây là nền tảng của mọi automation (phần 10).

**Permissions & sandbox.** `/permissions` để cho phép trước các tool an toàn (đỡ phải bấm duyệt liên tục). Cờ `--dangerously-skip-permissions` bỏ mọi hỏi đáp — chỉ dùng trong container/sandbox không có gì để mất, đừng dùng trên máy chính.

**Đổi model theo việc.** `/model` — dùng Opus/model cao nhất cho thiết kế và bài khó, Sonnet cho code thường ngày, Haiku cho việc cơ học. Riêng cách này đã giảm chi phí đáng kể.

**Resume phiên.** `claude --continue` tiếp tục phiên gần nhất, `claude --resume` chọn phiên cũ từ danh sách.

**Output styles & CLAUDE.md phân tầng.** CLAUDE.md có thể đặt ở `~/.claude/CLAUDE.md` (mọi dự án), gốc repo (cả team, commit vào Git), và trong thư mục con (chỉ nạp khi làm việc ở đó) — tầng sau ghi đè/bổ sung tầng trước.

---

## 7. Multi Claude instances làm việc song song

Ba mô hình thực dụng:

**Mô hình 1 — Worktrees (đã nói ở phần 3):** mỗi instance một branch, một thư mục. Phù hợp khi các task độc lập nhau. 2–4 instance là điểm ngọt; nhiều hơn thì chi phí chuyển ngữ cảnh của chính bạn thành nút cổ chai.

**Mô hình 2 — Người viết / người kiểm.** Cùng một repo, instance A viết code, instance B (phiên khác, context sạch) review hoặc viết test cho code của A. Vì B không bị "nhiễm" bởi quá trình suy nghĩ của A, nó bắt lỗi khách quan hơn — giống pair programming thật. Cách giao tiếp giữa hai bên: qua file (A ghi `PLAN.md`, B đọc) hoặc qua git commit.

**Mô hình 3 — Fan-out headless.** Một script phái n việc song song:

```bash
for module in auth payment users orders; do
  (cd "worktrees/$module" && claude -p "viết unit test cho module $module, coverage ≥ 80%" \
      --allowedTools "Edit,Write,Bash(npm test:*)" \
      --output-format json > "../logs/$module.json") &
done
wait
```

Kinh nghiệm vận hành: đặt hook `Notification` bắn thông báo desktop để biết instance nào đang chờ bạn duyệt; đừng cho 2 instance sửa cùng file; ghi rõ trong CLAUDE.md quy ước để mọi instance code cùng phong cách; và luôn có bước hợp nhất (một phiên cuối review + merge tất cả).

---

## 8. MCP (Model Context Protocol)

MCP là chuẩn mở để nối Claude với công cụ và dữ liệu bên ngoài: database, GitHub, Slack, trình duyệt, hệ thống nội bộ... Server MCP cung cấp tools/resources; Claude Code là client.

```bash
# Thêm server (ví dụ minh họa)
claude mcp add github -- npx -y @modelcontextprotocol/server-github
claude mcp add --transport http ten-server https://mcp.example.com/mcp
claude mcp list
```

Ba **scope** cấu hình: `local` (mặc định, chỉ mình bạn, chỉ repo này), `project` (ghi vào file `.mcp.json` ở gốc repo, commit được để cả team dùng chung), `user` (`--scope user`, mọi dự án trên máy bạn). File `.mcp.json` trông thế này:

```json
{
  "mcpServers": {
    "postgres-dev": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
    }
  }
}
```

Trong phiên, `/mcp` để xem trạng thái, xác thực OAuth, bật tắt server. Tài nguyên từ MCP tham chiếu được bằng `@server:resource`, và prompt do server cung cấp xuất hiện như slash command `/mcp__server__prompt`.

Hai cảnh báo quan trọng. Thứ nhất, **mỗi MCP server nạp định nghĩa tool vào context** — cắm 5 server "cho vui" có thể ngốn chục nghìn token trước khi bạn gõ chữ nào; chỉ bật cái đang dùng. Thứ hai, **chỉ cài server từ nguồn tin cậy**: nội dung server trả về đi thẳng vào context của Claude, server độc hại có thể tiêm chỉ thị (prompt injection).

Các server đáng thử: GitHub (issue/PR), Postgres/SQLite (query schema thật thay vì đoán), Playwright/Puppeteer (Claude tự mở web app của bạn để test), Sentry (đọc lỗi production), filesystem mở rộng.

---

## 9. Tối ưu token khi làm project lớn

Đây là tổng hợp chiến lược, xếp theo tác động giảm dần:

**1. Kiến trúc phiên: một phiên = một nhiệm vụ.** Nguồn lãng phí lớn nhất là phiên "trường thiên" kéo dài cả ngày — mỗi lượt mới phải cõng toàn bộ lịch sử. `/clear` giữa các task, `/compact` có định hướng giữa các giai đoạn của cùng task.

**2. Đẩy việc khảo sát xuống sub-agent.** Như phần 2 — phiên chính chỉ nhận tóm tắt. Với repo lớn, đây là khác biệt giữa "context đầy sau 10 phút" và "làm việc cả buổi thoải mái".

**3. Plan mode trước khi code.** Kế hoạch được duyệt trước nghĩa là ít vòng lặp "làm sai → giải thích lại → làm lại" — mỗi vòng như vậy đốt token gấp nhiều lần chi phí lập kế hoạch.

**4. CLAUDE.md súc tích + phân tầng.** Nạp mọi lượt, nên tính bằng "token thuê bao trọn đời". CLAUDE.md con trong thư mục module chỉ nạp khi cần.

**5. Model rẻ cho việc rẻ.** Haiku/Sonnet cho rename, viết test lặp lại, sửa lint; để dành model đắt cho thiết kế và debug khó.

**6. Tiết chế MCP và tool.** Tắt server không dùng; mỗi tool definition là token cố định mỗi lượt.

**7. Cho tọa độ thay vì bắt tìm.** "Sửa hàm `calculateTax` trong `src/billing/tax.ts`, lỗi ở nhánh xử lý giảm giá" rẻ hơn hẳn "có bug về thuế, tìm và sửa đi" — mỗi bước tìm kiếm là nhiều lần đọc file.

**8. Chốt kiến thức vào file.** Khi Claude vừa hiểu xong một module phức tạp, bảo nó ghi lại vào `docs/notes/ten-module.md`. Phiên sau đọc file 500 token này thay vì khảo sát lại từ đầu — biến chi phí lặp lại thành chi phí một lần.

---

## 10. Xây hệ thống automation thay vì làm thủ công

Tư duy cốt lõi: **mỗi lần bạn tự tay làm một việc lặp lại, hoặc tự tay nhắc Claude cùng một điều, đó là một automation chưa được viết.** Bậc thang tiến hóa:

**Bậc 1 — Slash commands:** quy trình lặp lại → file trong `.claude/commands/`. Ví dụ `/review`, `/changelog`, `/new-endpoint <tên>`.

**Bậc 2 — Hooks:** những thứ PHẢI xảy ra → hook, không phải lời nhắc. Format sau edit, test sau khi xong lượt, chặn sửa file cấm. Prompt có thể bị quên; hook thì không.

**Bậc 3 — Sub-agents chủ động:** agent với description "use proactively..." để Claude tự gọi reviewer sau khi viết code mà bạn không cần ra lệnh.

**Bậc 4 — Headless trong script:** `claude -p` biến Claude thành một lệnh Unix, ghép được vào pipeline:

```bash
# tự phân loại lỗi từ log
cat error.log | claude -p "phân loại các lỗi này theo mức nghiêm trọng, xuất JSON" --output-format json
```

**Bậc 5 — CI/CD:** GitHub Actions chính thức (`anthropics/claude-code-action`) cho phép tag `@claude` trong issue/PR để Claude tự sửa và mở PR, hoặc tự động review mọi PR mới:

```yaml
# .github/workflows/claude.yml (rút gọn)
on:
  issue_comment: { types: [created] }
jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Bậc 6 — Pipeline hoàn chỉnh:** kết hợp tất cả. Ví dụ một hệ thống thực tế: issue được gắn nhãn `auto-fix` → Action phái Claude headless trong container (sandbox, quyền giới hạn) → Claude sửa + viết test → hook chặn nó động vào file nhạy cảm → tạo PR → một instance Claude khác review PR → con người chỉ đọc bản review và bấm merge.

Nguyên tắc an toàn khi automation hóa: luôn giới hạn `--allowedTools`, chạy headless trong container/CI chứ không phải máy cá nhân, mọi thay đổi đi qua PR chứ không push thẳng, và giữ con người ở bước phê duyệt cuối.

---

## Lộ trình gợi ý cho bạn

Tuần 1: dùng thành thạo Plan mode, `/clear`, `/compact`, viết CLAUDE.md tốt. Tuần 2: tạo 3–5 slash commands cho quy trình của riêng bạn + hook auto-format. Tuần 3: tạo bộ sub-agents (explorer, reviewer, test-writer) và thử worktree với 2 instance. Tuần 4: cắm 1–2 MCP server thật sự cần, viết script headless đầu tiên, và thử claude-code-action trên một repo phụ.

Nguồn tham khảo chính thức:
- Tổng quan: https://docs.claude.com/en/docs/claude-code/overview
- Bản đồ tài liệu Claude Code: https://docs.anthropic.com/en/docs/claude-code/claude_code_docs_map.md
- Modal: https://modal.com/docs
- MCP: https://modelcontextprotocol.io
