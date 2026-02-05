import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

from datetime import datetime

RUN_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")

train_data = pd.read_csv('./datasets/good-train.csv')
eval_data = pd.read_csv('./datasets/good-test.csv')

def train_model_series(vectorizers, models):
    best_vectorizer = None
    best_model = None
    best_f1 = 0
    for i, (vectorizer, model) in enumerate(zip(vectorizers, models)):
        print(f"### Training model {i+1} ###")

        X_train = vectorizer.fit_transform(train_data['input'])
        y_train = train_data['target']
        print(f"X vectorized train shape: {X_train.shape}")

        X_train_split, X_val, y_train_split, y_val = train_test_split(
            X_train, y_train, test_size=0.1, random_state=42
        )

        model.fit(X_train_split, y_train_split)

        y_val_pred = model.predict(X_val)
        val_f1 = f1_score(y_val, y_val_pred)
        print(f"Validation F1 for model {i+1}: {val_f1:.4f}")
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_model = model
            best_vectorizer = vectorizer
            print("Best model updated.")
    
    return best_vectorizer, best_model


vectorizers = [
    # TfidfVectorizer(max_features=None, min_df=5, max_df=0.7, ngram_range=(1, 2), stop_words='english'),
    # TfidfVectorizer(max_features=5000, min_df=5, max_df=0.7, ngram_range=(1, 2), stop_words='english'),
    # TfidfVectorizer(max_features=2500, min_df=5, max_df=0.7, ngram_range=(1, 2), stop_words='english'),
    # TfidfVectorizer(max_features=1200, min_df=5, max_df=0.7, ngram_range=(1, 2), stop_words='english'),
    # TfidfVectorizer(max_features=600, min_df=5, max_df=0.7, ngram_range=(1, 2), stop_words='english'),
    # TfidfVectorizer(max_features=None, min_df=5, max_df=0.7, ngram_range=(1, 1), stop_words='english'),
    # TfidfVectorizer(max_features=5000, min_df=5, max_df=0.7, ngram_range=(1, 1), stop_words='english'),
    TfidfVectorizer(max_features=2500, min_df=5, max_df=0.7, ngram_range=(1, 1), stop_words='english'),
    # TfidfVectorizer(max_features=1200, min_df=5, max_df=0.7, ngram_range=(1, 1), stop_words='english'),
    # TfidfVectorizer(max_features=600, min_df=5, max_df=0.7, ngram_range=(1, 1), stop_words='english'),
]

models = [
    LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
    # LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True),
]

best_vec, best_model = train_model_series(vectorizers, models)

# import pdb; pdb.set_trace()

print("Full-data training")
X_train = best_vec.fit_transform(train_data['input'])
y_train = train_data['target']
model_full = LogisticRegression(random_state=42, max_iter=1000, C=1.0, verbose=True)
model_full.fit(X_train, y_train)

X_eval = best_vec.transform(eval_data['input'])
predictions = model_full.predict(X_eval)

results = pd.DataFrame({'id': eval_data['id'], 'target': predictions})
results.to_csv(f'submission_lr_{RUN_TIME}.csv', index=False)
print("结果已保存到 submission.csv")