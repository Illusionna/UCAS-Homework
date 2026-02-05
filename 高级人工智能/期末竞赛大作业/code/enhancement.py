import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

from datetime import datetime
from typing import Literal


RUN_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
METHOD_TYPE = None


def train(model_val, model_full, dense_model = False, use_scaler = False, val_only = False):
    train_data = pd.read_csv('./datasets/good-train.csv')
    eval_data = pd.read_csv('./datasets/good-test.csv')

    vectorizer = TfidfVectorizer(max_features=5000, min_df=5, max_df=0.7, ngram_range=(1, 1), stop_words='english')

    X_train = vectorizer.fit_transform(train_data['input'])
    if dense_model:
        X_train = np.array(X_train.todense())
    if use_scaler:
        try:
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
        except ValueError:
            scaler = StandardScaler(with_mean=False)
            X_train = scaler.fit_transform(X_train)
    y_train = train_data['target']
    print(f"X vectorized train shape: {X_train.shape}")


    print("### Train validation model ###")
    X_train_split, X_val, y_train_split, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42
    )

    model_val.fit(X_train_split, y_train_split)

    y_val_pred = model_val.predict(X_val)
    val_f1 = f1_score(y_val, y_val_pred)
    print(f"Validation F1 for model: {val_f1:.4f}")

    if not val_only:
        print("### Full-data training ###")
        X_train = vectorizer.fit_transform(train_data['input'])
        if dense_model:
            X_train = np.array(X_train.todense())
        if use_scaler:
            try:
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
            except ValueError:
                scaler = StandardScaler(with_mean=False)
                X_train = scaler.fit_transform(X_train)
        y_train = train_data['target']
        model_full.fit(X_train, y_train)

        X_eval = vectorizer.transform(eval_data['input'])
        if dense_model:
            X_eval = np.array(X_eval.todense())
        predictions = model_full.predict(X_eval)

        results = pd.DataFrame({'id': eval_data['id'], 'target': predictions})
        results.to_csv(f'submission_{METHOD_TYPE}_{RUN_TIME}.csv', index=False)
        print(f"结果已保存到 submission_{METHOD_TYPE}_{RUN_TIME}.csv")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--method", type=str, default='svm', help="Select from ['svm', 'rbfsvm', 'dectree', 'nb']")
    parser.add_argument("--use-scaler", action="store_true")
    parser.add_argument("--val-only", action="store_true")
    args = parser.parse_args()

    METHOD_TYPE = args.method

    if METHOD_TYPE == "svm":
        train(
            model_val=LinearSVC(max_iter=1000, random_state=42),
            model_full=LinearSVC(max_iter=1000, random_state=42),
            use_scaler=args.use_scaler,
            val_only=args.val_only
        )
    elif METHOD_TYPE == "rbfsvm":
        train(
            model_val=SVC(kernel='rbf', random_state=42, verbose=True),
            model_full=SVC(kernel='rbf', random_state=42, verbose=True),
            use_scaler=args.use_scaler,
            val_only=args.val_only
        )
    elif METHOD_TYPE == "dectree":
        train(
            model_val=DecisionTreeClassifier(max_depth=None, min_samples_split=2, min_samples_leaf=1, random_state=42),
            model_full=DecisionTreeClassifier(max_depth=None, min_samples_split=2, min_samples_leaf=1, random_state=42),
            use_scaler=args.use_scaler,
            val_only=args.val_only,
        )
    elif METHOD_TYPE == "nb":
        train(
            model_val=GaussianNB(),
            model_full=GaussianNB(),
            dense_model=True,
            # use_scaler=args.use_scaler,
            use_scaler=False,
            val_only=args.val_only,
        )
    else:
        raise ValueError(f"Unknown method {METHOD_TYPE}.")