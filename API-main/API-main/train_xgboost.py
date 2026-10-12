import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss

# B1: CHUẨN BỊ DATA
data = pd.read_csv("bank.csv", sep=";")
data = data.drop(columns=["duration", "default"])  # Bỏ data leakage

# Mã hóa nhãn nhanh gọn bằng dictionary mapping
data["y"] = data["y"].map({"no": 0, "yes": 1})

# Ép kiểu các cột chuỗi sang 'category' để XGBoost tự xử lý
cat_cols = data.select_dtypes(include="object").columns
data[cat_cols] = data[cat_cols].astype("category")

X = data.drop(columns=["y"])
y = data["y"]


X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, random_state=42)

# B2: KHỞI TẠO VÀ HUẤN LUYỆN MODEL
# Tính tỷ lệ class 0 / class 1 gọn gàng hơn
ratio = (y_train == 0).sum() / (y_train == 1).sum()

model = XGBClassifier(
    objective='binary:logistic',
    scale_pos_weight=ratio,
    max_depth=5,
    learning_rate=0.08,
    n_estimators=250,
    enable_categorical=True,  # Bật tính năng tự xử lý category
    random_state=42
)

model.fit(X_train, y_train)

# B3: LƯU CHECKPOINT
model.save_model("xgboost.json")
print("Đã lưu checkpoint mô hình tại 'xgboost.json'")

# B4: ĐÁNH GIÁ (EVALUATION)
y_pred_proba = model.predict_proba(X_test)[:, 1]

print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
print(f"Log Loss:      {log_loss(y_test, y_pred_proba):.4f}")