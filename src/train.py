import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

tfidf = TfidfVectorizer()
# SageMaker passes training data in /opt/ml/input/data/train
train_path = "/opt/ml/input/data/train/train.csv"
print("Loading training data from:", train_path)
df = pd.read_csv(train_path)
df['transformed_text'] = df['transformed_text'].fillna('').astype(str)

X = tfidf.fit_transform(df['transformed_text']).toarray()
y = df['target'].values


print("Training the model...")

model = MultinomialNB()
model.fit(X, y)

# Save the model to /opt/ml/model
model_dir = "/opt/ml/model"
os.makedirs(model_dir, exist_ok=True)
joblib.dump(model, os.path.join(model_dir, "model.joblib"))
joblib.dump(tfidf, os.path.join(model_dir, "vectorizer.pkl"))

import shutil

CODE_DIR = "/opt/ml/model/code"
os.makedirs(CODE_DIR, exist_ok=True)

# Copy inference script into model artifact
shutil.copy(
    os.path.join(os.getcwd(), "inference.py"),
    os.path.join(CODE_DIR, "inference.py")
)

print("Training the model completeed and model saved to:", model_dir)
print("Files in /opt/ml/model:", os.listdir(model_dir))
