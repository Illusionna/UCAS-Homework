import os
import torch
import config
import pickle
import shutil
import platform
import utils.net
import utils.tool
import sklearn.metrics


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


def test() -> None:
    with open(os.path.join('log', 'word2index.pkl'), mode = 'rb') as f: word2index: dict[str, int] = pickle.load(f)
    with open(os.path.join('log', 'tag2index.pkl'), mode = 'rb') as f: tag2index: dict[str, int] = pickle.load(f)
    index2tag = {value: key for key, value in tag2index.items()}

    test_corpus, test_label = utils.tool.load_dataset(
        corpus_path = config.hyperparameter_configuration['test_corpus'],
        label_path = config.hyperparameter_configuration['test_label']
    )
    test_dataset = utils.tool.DatasetNER(
        corpus = test_corpus,
        label = test_label,
        word2index = word2index,
        tag2index = tag2index,
        max_len = config.hyperparameter_configuration['max_len']
    )
    test_loader = torch.utils.data.DataLoader(
        dataset = test_dataset,
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
    model.load_state_dict(
        state_dict = torch.load(
            f = os.path.join('log', 'optimal_weight.pt'),
            map_location = config.hyperparameter_configuration['device'],
            weights_only = True
        )
    )
    model.eval()

    all_predictions = []
    all_labels = []

    with torch.no_grad():
        for inputs, targets, mask in test_loader:
            inputs = inputs.to(config.hyperparameter_configuration['device'])
            targets = targets.to(config.hyperparameter_configuration['device'])
            mask = mask.to(config.hyperparameter_configuration['device'])
            batch_predictions = model.forward(inputs, mask = mask)
            for idx, predictions in enumerate(batch_predictions):
                size = len(predictions)
                y = targets[idx][:size].tolist()
                all_predictions.extend([index2tag[i] for i in predictions])
                all_labels.extend([index2tag[i] for i in y])
    label_no_o = sorted(list(set(all_labels) - {'O', '<PAD>'}))

    precision_all = sklearn.metrics.precision_score(
        y_true = all_labels,
        y_pred = all_predictions,
        zero_division = 0,
        average = 'weighted'
    )
    recall_all = sklearn.metrics.recall_score(
        y_true = all_labels,
        y_pred = all_predictions,
        zero_division = 0,
        average = 'weighted'
    )
    f1_all = sklearn.metrics.f1_score(
        y_true = all_labels,
        y_pred = all_predictions,
        zero_division = 0,
        average = 'weighted'
    )
    precision_no_o = sklearn.metrics.precision_score(
        y_true = all_labels,
        y_pred = all_predictions,
        zero_division = 0,
        labels = label_no_o,
        average = 'micro'
    )
    recall_no_o = sklearn.metrics.recall_score(
        y_true = all_labels,
        y_pred = all_predictions,
        zero_division = 0,
        labels = label_no_o,
        average = 'micro'
    )
    f1_no_o = sklearn.metrics.f1_score(
        y_true = all_labels,
        y_pred = all_predictions,
        zero_division = 0,
        labels = label_no_o,
        average = 'micro'
    )

    print('Test Information:')
    print(f'\x1b[34m - precision: {precision_all}\x1b[0m')
    print(f'\x1b[34m - recall: {recall_all}\x1b[0m')
    print(f'\x1b[34m - f1: {f1_all}\x1b[0m')
    print(f'\x1b[32m - precision (without O): {precision_no_o}\x1b[0m')
    print(f'\x1b[32m - recall (without O): {recall_no_o}\x1b[0m')
    print(f'\x1b[32m - f1 (without O): {f1_no_o}\x1b[0m')


def predict(sentence: str) -> None:
    with open(os.path.join('log', 'word2index.pkl'), mode = 'rb') as f: word2index: dict[str, int] = pickle.load(f)
    with open(os.path.join('log', 'tag2index.pkl'), mode = 'rb') as f: tag2index: dict[str, int] = pickle.load(f)
    index2tag = {value: key for key, value in tag2index.items()}

    model = utils.net.BiLSTM_CRF(
        vocabulary_size = len(word2index),
        tag2index = tag2index,
        embedding_dimension = config.hyperparameter_configuration['embedding_dim'],
        hidden_dimension = config.hyperparameter_configuration['hidden_dim']
    ).to(config.hyperparameter_configuration['device'])
    model.load_state_dict(
        state_dict = torch.load(
            f = os.path.join('log', 'optimal_weight.pt'),
            map_location = config.hyperparameter_configuration['device'],
            weights_only = True
        )
    )
    model.eval()

    words = list(sentence.strip())
    word_id = [word2index.get(word, word2index.get('<UNK>', 1)) for word in words]
    tensors = torch.LongTensor([word_id]).to(config.hyperparameter_configuration['device'])
    mask = (tensors != 0).bool().to(config.hyperparameter_configuration['device'])

    with torch.no_grad(): prediction_id = model.forward(tensors, mask = mask)
    prediction_tag = [index2tag.get(i) for i in prediction_id[0]]

    for word, tag in list(zip(words, prediction_tag)): print(f'{tag}', end=' ')


if __name__ == '__main__':
    # test()
    predict('2025年秋季入学的硕士研究生叶炳辉是人工智能学院计算机科学与技术专业.')