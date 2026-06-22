import pandas as pd
import numpy as np
import re
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Conv1D, GlobalMaxPooling1D, Dense, Dropout

# =======================
# 1️⃣ Load Dataset
# =======================
# CSV format: sender_email,label
# label: 0 = safe, 1 = phishing
data = pd.read_csv("dataset.csv")

# =======================
# 2️⃣ Clean Emails
# =======================
def clean_email(email):
    email = email.lower()  # Convert to lowercase
    # Keep only letters, digits, and meaningful email symbols: @ . _ -
    return re.sub(r'[^a-z0-9@._-]', '', email)

emails = data['sender_email'].astype(str).apply(clean_email)
labels = data['label'].values

# =======================
# 3️⃣ Tokenize Emails
# =======================
MAX_WORDS = 5000           # Top 5000 tokens
MAX_SEQUENCE_LENGTH = 50   # Emails are short

tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
tokenizer.fit_on_texts(emails)
sequences = tokenizer.texts_to_sequences(emails)
X = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH, padding='post')

y = np.array(labels)

# Save tokenizer for future use
with open("tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)

# =======================
# 4️⃣ Train/Test Split
# =======================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =======================
# 5️⃣ Build CNN Model
# =======================
model = Sequential([
    Embedding(input_dim=MAX_WORDS, output_dim=64, input_length=MAX_SEQUENCE_LENGTH),
    Conv1D(filters=64, kernel_size=3, activation='relu'),
    GlobalMaxPooling1D(),
    Dense(64, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# =======================
# 6️⃣ Train Model
# =======================
history = model.fit(
    X_train, y_train,
    epochs=5,
    batch_size=32,
    validation_data=(X_test, y_test),
    verbose=1
)

# =======================
# 7️⃣ Save Model
# =======================
model.save("model.h5")
print("✅ Model trained and saved as model.h5")
print("✅ Tokenizer saved as tokenizer.pkl")

# =======================
# 8️⃣ Evaluate Model
# =======================
# Evaluate loss and accuracy
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\n📊 Test Accuracy: {acc*100:.2f}%")

# Predict classes (0 or 1)
y_pred = (model.predict(X_test) > 0.5).astype("int32")

# Calculate Precision, Recall, F1-score
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"📌 Precision: {precision:.4f}")
print(f"📌 Recall:    {recall:.4f}")
print(f"📌 F1 Score:  {f1:.4f}")
