import os
import json
import torch
import config
import pickle
import shutil
import datetime
import platform
import utils.net
import utils.tool
import collections
import sklearn.model_selection


def cls() -> None:
    os.system('')
    os.makedirs('log', exist_ok = True)
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
cls()


def train() -> None:
    INPUT, LABEL = utils.tool.load_dataset(
        corpus_path = config.hyperparameter_configuration['train_corpus'],
        label_path = config.hyperparameter_configuration['train_label']
    )
    train_corpus, valid_corpus, train_label, valid_label = sklearn.model_selection.train_test_split(
        INPUT, LABEL,
        train_size = config.hyperparameter_configuration['proportion_trainset'],
        random_state = 42,
        shuffle = True
    )

    word2index, tag2index = utils.tool.build_vocabulary(train_corpus + valid_corpus, train_label + valid_label)
    index2tag = {value: key for key, value in tag2index.items()}

    with open(os.path.join('log', 'word2index.pkl'), mode = 'wb') as f: pickle.dump(word2index, f)
    with open(os.path.join('log', 'tag2index.pkl'), mode = 'wb') as f: pickle.dump(tag2index, f)
    print(f'Vocabulary Size: {len(word2index)} | Tag Size: {len(index2tag)}\n')

    train_dataset = utils.tool.DatasetNER(
        corpus = train_corpus,
        label = train_label,
        word2index = word2index,
        tag2index = tag2index,
        max_len = config.hyperparameter_configuration['max_len']
    )
    valid_dataset = utils.tool.DatasetNER(
        corpus = valid_corpus,
        label = valid_label,
        word2index = word2index,
        tag2index = tag2index,
        max_len = config.hyperparameter_configuration['max_len']
    )
    train_loader = torch.utils.data.DataLoader(
        dataset = train_dataset,
        batch_size = config.hyperparameter_configuration['batch_size'],
        shuffle = True,
        collate_fn = utils.tool.collate_function
    )
    valid_loader = torch.utils.data.DataLoader(
        dataset = valid_dataset,
        batch_size = config.hyperparameter_configuration['batch_size'],
        shuffle = True,
        collate_fn = utils.tool.collate_function
    )

    model = utils.net.BiLSTM_CRF(
        vocabulary_size = len(word2index),
        tag2index = tag2index,
        embedding_dimension = config.hyperparameter_configuration['embedding_dim'],
        hidden_dimension = config.hyperparameter_configuration['hidden_dim']
    ).to(config.hyperparameter_configuration['device'])

    optimal_f1 = 0
    info = collections.defaultdict(dict)
    optimizer = torch.optim.Adam(model.parameters(), lr = config.hyperparameter_configuration['learning_rate'])
    epochs = config.hyperparameter_configuration['epochs']

    for epoch in range(0, epochs, 1):
        model.train()
        total_loss = 0
        hashmap = dict()
        for idx, (inputs, targets, mask) in enumerate(train_loader):
            inputs = inputs.to(config.hyperparameter_configuration['device'])
            targets = targets.to(config.hyperparameter_configuration['device'])
            mask = mask.to(config.hyperparameter_configuration['device'])
            optimizer.zero_grad()
            loss = model.forward(inputs, targets, mask)
            loss.backward()
            optimizer.step()
            total_loss = total_loss + loss.detach().item()
            utils.tool.progress_bar(
                current = idx,
                total = len(train_loader),
                step = 1,
                description = f'epoch {epoch + 1} / {epochs} | loss = {(total_loss / len(train_loader)):.5f}\t'
            )
        precision_all, recall_all, f1_all, precision_no_o, recall_no_o, precision_no_o, f1_no_o, report_all, report_no_o = utils.tool.evaluate(
            device = config.hyperparameter_configuration['device'],
            model = model,
            dataloader = train_loader,
            index2tag = index2tag
        )
        hashmap['train'] = {
            'precision_all': precision_all,
            'recall_all': recall_all,
            'f1_all': f1_all,
            'precision_no_o': precision_no_o,
            'recall_no_o': recall_no_o,
            'f1_no_o': f1_no_o
        }
        precision_all, recall_all, f1_all, precision_no_o, recall_no_o, precision_no_o, f1_no_o_valid, report_all, report_no_o = utils.tool.evaluate(
            device = config.hyperparameter_configuration['device'],
            model = model,
            dataloader = valid_loader,
            index2tag = index2tag
        )
        hashmap['valid'] = {
            'precision_all': precision_all,
            'recall_all': recall_all,
            'f1_all': f1_all,
            'precision_no_o': precision_no_o,
            'recall_no_o': recall_no_o,
            'f1_no_o': f1_no_o_valid
        }
        info[epoch + 1]['loss'] = total_loss / len(train_loader)
        info[epoch + 1]['train'] = hashmap['train']
        info[epoch + 1]['valid'] = hashmap['valid']
        if f1_no_o_valid > optimal_f1:
            optimal_f1 = f1_no_o_valid
            torch.save(model.state_dict(), os.path.join('log', 'optimal_weight.pt'))
            print(f"({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) >>> Optimal Model Saved!\n")
    with open(os.path.join('log', 'info.json'), mode = 'w', encoding = 'utf-8') as f:
        json.dump(info, f, indent = 4, ensure_ascii = False)



if __name__ == '__main__':
    train()