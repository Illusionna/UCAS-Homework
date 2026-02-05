import os
import re
import torch
import shutil
import platform
import numpy as np
import pandas as pd
import transformers
import sklearn.metrics
import sklearn.model_selection

from datetime import datetime
from typing import Callable, Optional


EPOCHS = 32
MAX_LEN = 128
# BATCH_SIZE = 128 + 64
BATCH_SIZE = 64
LEARNING_RATE = 2e-5

RIBBON = ''.join(f'\x1b[38;5;{idx}m-\x1b[0m' for idx in range(0, 64, 1))
DEVICE = torch.device('mps' if platform.system() == 'Darwin' else 'cuda' if torch.cuda.is_available() else 'cpu')

RUN_TIME = None


def cls() -> None:
    transformers.logging.set_verbosity_error()
    os.system('')
    for root, dirs, files in os.walk(os.getcwd()):
        for dir in dirs:
            if dir == '__pycache__':
                shutil.rmtree(os.path.join(root, dir))
        for file in files:
            if file == '.DS_Store':
                os.remove(os.path.join(root, file))
    try:
        os.system(
            {'Windows': 'cls', 'Linux': 'clear', 'Darwin': 'clear'}[platform.system()]
        )
    except:
        print('\x1b[H\x1b[J', end = '')
# cls()


def progress_bar(current: int, epochs: int, step: int, description: str) -> None:
    if current != 0 and current % step != 0 and current != epochs: return
    width = 50
    if epochs > 0: percentage = current / epochs
    else: percentage = 0
    filled = int(percentage * width)
    print('\r[', end = '')
    for j in range(0, width, 1):
        if j < filled: print('\x1b[32m=\x1b[0m', end = '')
        elif j == filled: print('>', end = '')
        else: print(' ', end = '')
    print('] %7.2f%% (%d/%d)' % (percentage * 100, current, epochs), end = '')
    if description != None: print(' \x1b[33m%s\x1b[0m\x1b[K' % description, end = '')
    else: print('\x1b[K', end = '')
    print(end = '', flush = True)
    if current >= epochs: print('')


def statistics(df: pd.DataFrame, label: str) -> None:
    missing_columns = ['keyword', 'location']
    missing_distribution = df[missing_columns].isnull().sum()
    print(f'{label}规模: {df.shape} | {label}大小: {(df.memory_usage().sum() / 1024):.3f} KB')
    print(f"{label}缺失值: keyword = {missing_distribution['keyword']} ({(100 * missing_distribution['keyword'] / df.shape[0]):.3f}%) | location = {missing_distribution['location']} ({(100 * missing_distribution['location'] / df.shape[0]):.3f}%)")
    print(f"{label}类型数: keyword = {df['keyword'].nunique()} | location = {df['location'].nunique()}")


def regex(text: str) -> str:
    text = re.sub(r'https?:\/\/t.co\/[A-Za-z0-9]+', '<URL>', text)
    text = re.sub(r'@\w+', '<USER>', text)
    text = re.sub(r'#(\w+)', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def generate(df_train: pd.DataFrame, df_test: pd.DataFrame) -> None:
    df_train['input'] = df_train.fillna('').apply(
        func = lambda row: f"[keyword: {row['keyword']}] [location: {row['location']}] {regex(row['text'])}",
        axis = 1
    )
    df_train[['id', 'input', 'target']].to_csv(os.path.join('datasets', 'good-train.csv'), index = None)
    df_test['input'] = df_test.fillna('').apply(
        func = lambda row: f"[keyword: {row['keyword']}] [location: {row['location']}] {regex(row['text'])}",
        axis = 1
    )
    df_test[['id', 'input']].to_csv(os.path.join('datasets', 'good-test.csv'), index = None)


class DisasterTweetsDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels = None, tokenizer = None, max_len = MAX_LEN, **kwargs) -> None:
        super().__init__()
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        text = str(self.texts[idx])
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens = True,
            max_length = self.max_len,
            padding = 'max_length',
            truncation = True,
            return_token_type_ids = False,
            return_attention_mask = True,
            return_tensors = 'pt',
        )
        item = {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten()
        }
        if self.labels is not None: item['labels'] = torch.tensor(self.labels[idx], dtype = torch.long)
        return item


def inner_train(
    df_good_test: pd.DataFrame,
    model: transformers.BertForSequenceClassification,
    train_loader: torch.utils.data.DataLoader,
    valid_loader: torch.utils.data.DataLoader,
    test_loader: torch.utils.data.DataLoader,
    **kwargs
) -> None:
    optimizer = torch.optim.AdamW(model.parameters(), lr = LEARNING_RATE)
    best_f1 = 0.0
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for idx, batch in enumerate(train_loader):
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            labels = batch['labels'].to(DEVICE)
            optimizer.zero_grad()
            outputs = model.forward(input_ids, attention_mask = attention_mask, labels = labels)
            
            # loss = outputs.loss
            try:
                logits  = outputs.logits
                lls     = torch.log_softmax(logits, dim=-1)
                weights = torch.full_like(labels.flatten(), fill_value=1/len(labels), dtype=lls.dtype)
                w_lls   = torch.stack([weights, weights], dim=0).T * lls
                loss    = torch.nn.functional.nll_loss(w_lls, labels.flatten(), reduction='sum')
            except Exception:
                import pdb; pdb.set_trace()

            loss.backward()
            optimizer.step()
            total_loss = total_loss + loss.item()
            progress_bar(idx + 1, len(train_loader), 1, f'[epoch {epoch + 1}/{EPOCHS}] loss = {total_loss:.3f}')
        avg_train_loss = total_loss / len(train_loader)

        model.eval()
        valid_predictions = []
        valid_labels = []
        with torch.no_grad():
            for batch in valid_loader:
                input_ids = batch['input_ids'].to(DEVICE)
                attention_mask = batch['attention_mask'].to(DEVICE)
                labels = batch['labels'].to(DEVICE)
                outputs = model.forward(input_ids, attention_mask = attention_mask)
                _, predictions = torch.max(outputs.logits, dim = 1)
                valid_predictions.extend(predictions.cpu().numpy())
                valid_labels.extend(labels.cpu().numpy())
        current_f1 = sklearn.metrics.f1_score(valid_labels, valid_predictions, average = 'macro')
        print(f'  -> train loss: {avg_train_loss:.4f} | valid f1: {current_f1:.4f}')
        if current_f1 > best_f1:
            best_f1 = current_f1
            torch.save(model.state_dict(), f'best_model_{RUN_TIME}.pth')
            print(f'  -> F1 分数提升至 {best_f1:.4f}，模型已保存')

    predictions = []
    with torch.no_grad():
        for idx, batch in enumerate(test_loader):
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            outputs = model.forward(input_ids, attention_mask = attention_mask)
            _, preds = torch.max(outputs.logits, dim = 1)
            predictions.extend(preds.cpu().tolist())
            progress_bar(idx + 1, len(test_loader), 1, None)
    submission = pd.DataFrame({'id': df_good_test['id'], 'target': predictions})
    submission.to_csv(f'submission_bert_{RUN_TIME}.csv', index = False)
    print('  -> BERT 预测文件已生成.')


def train(
        inner_train_call: Optional[Callable] = None,
        dataset_wrapper: Optional[torch.utils.data.Dataset] = None,
        model = None,
        tokenizer = None,
        **train_kwargs
):
    if inner_train_call is None:
        inner_train_call = inner_train
    if dataset_wrapper is None:
        dataset_wrapper = DisasterTweetsDataset

    df_train = pd.read_csv(filepath_or_buffer = './datasets/train.csv', dtype = {'id': np.int16, 'target': np.int8})
    df_test = pd.read_csv(filepath_or_buffer = './datasets/test.csv', dtype = {'id': np.int16})

    statistics(df_train, '训练集')
    print(RIBBON)
    statistics(df_test, '测试集')

    generate(df_train, df_test)

    df_good_train = pd.read_csv('./datasets/good-train.csv').fillna('')
    df_good_test = pd.read_csv('./datasets/good-test.csv').fillna('')

    train_input, valid_input, train_target, valid_target = sklearn.model_selection.train_test_split(
        df_good_train['input'],
        df_good_train['target'],
        test_size = 0.1,
        shuffle=False,
    )

    train_dataset = dataset_wrapper(train_input.to_numpy(), train_target.to_numpy(), tokenizer)
    valid_dataset = dataset_wrapper(valid_input.to_numpy(), valid_target.to_numpy(), tokenizer)
    test_dataset = dataset_wrapper(df_good_test['input'].to_numpy(), None, tokenizer)

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size = BATCH_SIZE, shuffle = True)
    valid_loader = torch.utils.data.DataLoader(valid_dataset, batch_size = BATCH_SIZE)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size = BATCH_SIZE)

    # model = transformers.BertForSequenceClassification.from_pretrained(PRETRAINED_MODEL, num_labels = 2, cache_dir = 'bert_cache')
    # model = model.to(DEVICE)
    # optimizer = torch.optim.AdamW(model.parameters(), lr = LEARNING_RATE)

    inner_train_call(
        df_good_test=df_good_test,
        model=model,
        train_loader=train_loader,
        valid_loader=valid_loader,
        test_loader=test_loader,
        train_dataset=train_dataset,
        valid_dataset=valid_dataset,
        test_dataset=test_dataset,
        **train_kwargs,
    )


if __name__ == "__main__":
    RUN_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", type=str, default='bert-large-uncased')
    args = parser.parse_args()
    
    PRETRAINED_MODEL = args.model

    model = transformers.BertForSequenceClassification.from_pretrained(PRETRAINED_MODEL, num_labels = 2, cache_dir = 'bert_cache')
    model = model.to(DEVICE)
    tokenizer = transformers.BertTokenizer.from_pretrained(PRETRAINED_MODEL, cache_dir = 'bert_cache')
    train(model=model, tokenizer=tokenizer)