# VAIC Chatbot

Hệ thống chatbot + API cho ngân hàng ABC Bank, gồm 4 endpoint phục vụ: chấm điểm khách hàng, sinh email marketing, sắp xếp công việc, gợi ý hành động sau cuộc gọi.

---

## Cài đặt

```bash
pip install -r requirements.txt

# Nếu dùng DeepSeek hoặc Gemini, tạo file .env:
echo 'DEEPSEEK_API_KEY=sk-xxx' >> .env
echo 'GEMINI_API_KEY=xxx'     >> .env

# Ollama — không cần API key, chỉ cần pull model và chạy server:
ollama pull qwen3.5:9b
ollama pull gemma4:12b
```

---

## Chạy server

```bash
uvicorn server:app --reload --port 8000
```

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

---

## API Reference

### 1. `POST /score` — Chấm điểm khách hàng

**Mục đích:** Dùng mô hình XGBoost (đã train trên `bank.csv`) để dự đoán xác suất
khách hàng sẽ mở sổ tiết kiệm (`y=yes`).


**Output (200):**
```json
{"score": 0.228}
```
`score` ∈ [0, 1], càng cao → khách hàng càng tiềm năng.

**Output (400):**
```json
{"error": "Missing required columns", "missing": ["job", "balance", ...], "required": [...]}
```

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "info": {
      "age": 58, "job": "management", "marital": "married",
      "education": "tertiary", "balance": 2143,
      "housing": "yes", "loan": "no", "contact": "unknown",
      "day": 5, "month": "may", "campaign": 1,
      "pdays": -1, "previous": 0, "poutcome": "unknown"
    }
  }'
```

---

### 2. `POST /create_mail` — Sinh email marketing

**Mục đích:** Nhận thông tin khách hàng + phân hạng tier (1-5, càng nhỏ càng tiềm năng),
gọi LLM để viết email marketing cá nhân hóa. Chiến lược theo tier:

**Output (200):**
```json
{"email": "Tiêu đề: Đặc quyền lãi suất dành riêng cho bạn\n\nKính gửi..."}
```

**Output (400):**
```json
{"error": "Tier must be between 1 and 5"}
```

```bash
curl -X POST http://localhost:8000/create_mail \
  -H "Content-Type: application/json" \
  -d '{
    "info": {"age":58,"job":"management","marital":"married","education":"tertiary","balance":2143,"housing":"yes","loan":"no","contact":"unknown","day":5,"month":"may","campaign":1,"pdays":-1,"previous":0,"poutcome":"unknown"},
    "tier": 1,
    "provider": "qwen"
  }'
```

---

### 3. `POST /remind` — Sắp xếp công việc theo ưu tiên

**Mục đích:** Nhận danh sách công việc của nhân viên (dạng dict hoặc string),
gọi LLM sắp xếp theo tiêu chí: mức độ khẩn cấp, tầm quan trọng, deadline,
ảnh hưởng đến công việc khác. Trả về JSON đã sắp xếp.

**Output (200) — model không trả JSON:**
```json
{"_raw": "...nội dung thô...", "_error": "Model did not return valid JSON"}
```

```bash
# Dạng dict
curl -X POST http://localhost:8000/remind \
  -H "Content-Type: application/json" \
  -d '{
    "info": {"a":"Gửi báo cáo tháng (deadline hôm nay)","b":"Họp team 14h","c":"Check email"},
    "provider": "qwen"
  }'

# Dạng string
curl -X POST http://localhost:8000/remind \
  -H "Content-Type: application/json" \
  -d '{
    "info": "1. Chuẩn bị slide ngày mai\n2. Đặt vé máy bay\n3. Điền timesheet",
    "provider": "qwen"
  }'
```

---

### 4. `POST /suggest_next_action` — Gợi ý hành động tiếp theo

**Mục đích:** Nhận tóm tắt cuộc gọi của nhân viên với khách hàng, kết hợp hồ sơ
khách hàng và tier, gọi LLM đưa ra lời khuyên về bước tiếp theo để giữ chân
và chuyển đổi khách hàng. Output có 4 phần: Đánh giá → Hành động → Ưu tiên → Gợi ý kịch bản.

**Output (200):**
```json
{"advice": "1. [Đánh giá] Khách đang so sánh lãi suất...\n2. [Hành động] Gửi bảng so sánh...\n3. [Ưu tiên] Cao\n4. [Gợi ý kịch bản] Chào anh/chị...\""}
```

**Output (400):**
```json
{"error": "Tier must be between 1 and 5"}
```

```bash
curl -X POST http://localhost:8000/suggest_next_action \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Khách hỏi lãi suất gửi 6 tháng, đang so sánh với ngân hàng khác. Còn lưỡng lự.",
    "info": {"age":44,"job":"technician","marital":"single","education":"secondary","balance":29000,"housing":"yes","loan":"no","contact":"unknown","day":5,"month":"may","campaign":1,"pdays":-1,"previous":0,"poutcome":"unknown"},
    "tier": 2,
    "provider": "qwen"
  }'
```


### Dấu hiệu thành công / thất bại

| Endpoint | ✓ Thành công | ✗ Thất bại |
|----------|-------------|-----------|
| `/score` | `{"score": 0.XX}`, status 200 | `{"error": "...", "missing": [...]}`, status 400 |
| `/create_mail` | `{"email": "Tiêu đề: ...\n..."}`, status 200 | `{"error": "..."}`, status 400 hoặc rỗng |
| `/remind` | `{"1": "...", "2": "..."}`, key là số | `{"_raw": "...", "_error": "Model did not return valid JSON"}` |
| `/suggest_next_action` | `{"advice": "1. [Đánh giá]..."}`, đủ 4 mục | `{"error": "..."}`, status 400 |


## Provider & API key

| Provider | Biến môi trường | Ghi chú |
|----------|----------------|---------|
| `ollama` | không cần | `ollama pull <model>` |
| `deepseek` | `DEEPSEEK_API_KEY` | `sk-...` từ [platform.deepseek.com](https://platform.deepseek.com) |
| `gemini` | `GEMINI_API_KEY` | Từ [Google AI Studio](https://aistudio.google.com) |

---

## Cấu trúc

```
VAIC/
├── server.py          # FastAPI — 6 endpoint
├── chatbot.py         # LangGraph — graph + chat()
├── models.py          # get_model() — qwen / gemma / deepseek / gemini
├── prompts.py         # 7 system prompt
├── train_xgboost.py   # Train XGBoost trên bank.csv
├── xgboost.json       # Checkpoint mô hình
├── bank.csv           # Dữ liệu 45K khách hàng
├── requirements.txt
└── .env               # API key (không commit)
```
