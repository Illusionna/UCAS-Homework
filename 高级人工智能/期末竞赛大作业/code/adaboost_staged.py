import sys
sys.path.extend(['.'])

import torch
import sklearn
import transformers
import pandas as pd
from tqdm import tqdm

from typing import Optional
from datetime import datetime

from bert import train, DEVICE, BATCH_SIZE, LEARNING_RATE, MAX_LEN, progress_bar, DisasterTweetsDataset

RUN_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
EPOCHS = 10
# DEVICE = 'cuda'

BP_INNER_TRAINING_LOOP = False
BP_INNER_TRAIN_ADABOOST = False


class DisasterTweetsDatasetWithWeights(DisasterTweetsDataset):
    def __init__(self, texts, labels=None, tokenizer=None, max_len=MAX_LEN, weights=None, **kwargs):
        super().__init__(texts, labels, tokenizer, max_len)

        self.init_w = 1 / len(texts)
        self.weights = torch.full((len(texts), ), self.init_w, dtype=torch.float) if weights is None else weights
        # self.weights = torch.softmax(torch.randn((len(texts), ), dtype=torch.float), dim=-1)
        # self.weights = torch.load("./weights.pth")
    
    def set_weights(self, weights):
        self.weights = weights

    def __getitem__(self, idx):
        item = super().__getitem__(idx)
        item['weights'] = self.weights[idx]
        item['idx'] = torch.tensor(idx, dtype=torch.long)
        return item


def inner_train_adaboost(
        model: transformers.BertForSequenceClassification,
        valid_loader: torch.utils.data.DataLoader,
        train_dataset: DisasterTweetsDatasetWithWeights,
        stage: int,
        **kwargs
):
    if stage == 0:
        data_weights = torch.full((len(train_dataset), ), 1 / len(train_dataset), dtype=torch.float)
    else:
        data_weights = torch.load("./weights_tmp.pth")
    
    print( "##########################")
    print(f"#### Training model {stage} ####")
    print( "##########################")
    # import pdb; pdb.set_trace()

    train_dataset.set_weights(data_weights)
    print(f"Data weights statistics: sum = {train_dataset.weights.sum().item():.4f}, max = {train_dataset.weights.max().item():.4f}, min = {train_dataset.weights.min().item():.4f}")
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size = BATCH_SIZE, shuffle = True)

    optimizer = torch.optim.AdamW(model.parameters(), lr = LEARNING_RATE)

    model = _inner_training_loop(
        model=model,
        optimizer=optimizer,
        train_loader=train_loader,
        valid_loader=valid_loader,
        model_id=stage,
    )

    model.eval()
    train_error = 0
    train_predictions = []
    train_labels = []
    train_sample_indices = []
    with torch.no_grad():
        for batch in tqdm(train_loader, total=len(train_loader), desc="Re-evaluating on training set"):
            input_ids       = batch['input_ids'].to(DEVICE)
            attention_mask  = batch['attention_mask'].to(DEVICE)
            labels          = batch['labels'].to(DEVICE)
            weights         = batch['weights'].to(DEVICE)
            sample_indices  = batch['idx'].to(DEVICE)
            
            outputs = model.forward(input_ids, attention_mask = attention_mask)
            _, predictions = torch.max(outputs.logits, dim = 1)

            train_predictions.append(predictions)
            train_labels.append(labels)
            train_sample_indices.append(sample_indices)

            train_error += weights[predictions.flatten() != labels.flatten()].sum()

    y_preds = torch.cat(train_predictions, dim=0)
    y_gts = torch.cat(train_labels, dim=0)
    indices = torch.cat(train_sample_indices, dim=0)

    alpha = 0.5 * torch.log((1 - train_error) / train_error)
    alpha = alpha.detach().clone()
    print(f"Train error for model {stage}: {train_error.item():.4f}")
    print(f"Alpha for model {stage}: {alpha:.4f}")

    weight_factors = torch.full_like(y_preds, alpha, dtype=torch.float, device=y_preds.device)
    weight_factors = torch.masked_fill(weight_factors, y_preds == y_gts, -alpha)
    weight_factors = torch.exp(weight_factors)

    for i in tqdm(range(len(train_loader.dataset)), total=len(train_loader.dataset), desc="Updating training sample weights"):
        sample_idx = indices[i]
        weight_factor = weight_factors[i]
        data_weights[sample_idx] *= weight_factor.detach().clone().to(data_weights.device)
    data_weights /= sum(data_weights)
    # data_weights = torch.full((len(train_dataset), ), 1 / len(train_dataset), dtype=torch.float)
    data_weights = torch.tensor(data_weights, dtype=torch.float)

    torch.save(data_weights, "./weights_tmp.pth")
    torch.save({"model": model, "alpha": alpha}, f"best_model_adastage{stage}.pth")


def _inner_training_loop(
        model: transformers.BertForSequenceClassification,
        optimizer: torch.optim.AdamW,
        train_loader: torch.utils.data.DataLoader,
        valid_loader: torch.utils.data.DataLoader,
        *,
        model_id: Optional[int] = None,
        **kwargs
) -> transformers.BertForSequenceClassification:
    best_f1 = 0.0
    for epoch in range(EPOCHS):
        model.train()

        total_loss = 0
        for idx, batch in enumerate(train_loader):
            input_ids       = batch['input_ids'].to(DEVICE)
            attention_mask  = batch['attention_mask'].to(DEVICE)
            labels          = batch['labels'].to(DEVICE)
            weights         = batch['weights'].to(DEVICE)

            optimizer.zero_grad()
            outputs = model.forward(input_ids, attention_mask = attention_mask, labels = labels)
            
            # loss = outputs.loss
            logits  = outputs.logits
            lls     = torch.log_softmax(logits, dim=-1)
            try:
                weights = weights / weights.sum()
            except:
                weights = torch.full_like(labels.flatten(), fill_value=1/len(labels), dtype=lls.dtype)
            w_lls   = torch.stack([weights, weights], dim=0).T * lls
            loss    = torch.nn.functional.nll_loss(w_lls, labels.flatten(), reduction='sum')

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
            save_path = f'best_model_boost_{model_id}.pth' if model_id is not None else 'best_model.pth'
            torch.save(model, save_path)
            print(f'  -> F1 分数提升至 {best_f1:.4f}，模型已保存')
    
    save_path = f'best_model_boost_{model_id}.pth' if model_id is not None else 'best_model.pth'
    best_model = torch.load(save_path, weights_only=False)
    return best_model


def predict(
        df_good_test: pd.DataFrame,
        test_loader: torch.utils.data.DataLoader,
        model_paths: Optional[list[str]] = None,
        models: Optional[list[transformers.BertForSequenceClassification]] = None,
        alphas: Optional[list[float]] = None,
):
    if models is None or alphas is None:
        model_dicts = [torch.load(path, weights_only=False) for path in model_paths]
        models = [m['model'] for m in model_dicts]
        alphas = [m['alpha'] for m in model_dicts]
    
    predictions = []
    with torch.no_grad():
        for idx, batch in tqdm(enumerate(test_loader), total=len(test_loader), desc="Evaluating on test set"):
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)

            model_preds = 0
            for model, alpha in zip(models, alphas):
                outputs = model.forward(input_ids, attention_mask = attention_mask)
                _, preds = torch.max(outputs.logits, dim = 1)
                preds = torch.masked_fill(preds, preds == 0, -1) * alpha
                model_preds += preds
            
            preds = torch.sign(model_preds).to(dtype=torch.long)
            preds = preds.masked_fill(preds == -1, 0)
            predictions.extend(preds.cpu().tolist())

    submission = pd.DataFrame({'id': df_good_test['id'], 'target': predictions})
    submission.to_csv(f'submission_adaboost_{RUN_TIME}.csv', index = False)
    print('  -> BERT 预测文件已生成.')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", type=str, default='bert-large-uncased')
    parser.add_argument("-e", "--epochs", type=int, default=10)
    parser.add_argument("-s", "--stage", type=int, default=0)
    parser.add_argument("--predict", nargs='*', type=str, default=None)
    args = parser.parse_args()

    PRETRAINED_MODEL = args.model
    EPOCHS = int(args.epochs)

    tokenizer = transformers.BertTokenizer.from_pretrained(PRETRAINED_MODEL, cache_dir = 'bert_cache')

    if args.predict:
        df_good_test=pd.read_csv('./datasets/good-test.csv').fillna('')
        test_dataset = DisasterTweetsDataset(df_good_test['input'].to_numpy(), None, tokenizer)
        test_loader = torch.utils.data.DataLoader(test_dataset, batch_size = BATCH_SIZE)

        predict(
            df_good_test=df_good_test,
            test_loader=test_loader,
            model_paths=args.predict,
        )

    else:
        train(
            inner_train_call=inner_train_adaboost,
            dataset_wrapper=DisasterTweetsDatasetWithWeights,
            model=transformers.BertForSequenceClassification.from_pretrained(PRETRAINED_MODEL, num_labels = 2, cache_dir = 'bert_cache').to(DEVICE),
            tokenizer=tokenizer,
            stage=args.stage,
        )