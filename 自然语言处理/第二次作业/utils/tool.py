import utils.net
import torch
import sklearn.metrics


def progress_bar(current: int, total: int, step: int = 1, description: str = None) -> None:
    """
    显示进度条.

    Args:
        current (int): 当前进度.
        total (int): 一共进度.
        step (int): 每若干步打印一次.
        description (str): 前置描述文本.

    Returns:
        None
    """
    if (current + 1) != 0 and (current + 1) % step != 0 and (current + 1) != total: return
    width = 50
    print('\x1b[?25l', end = '')
    percentage = (current + 1) / total
    filled = int(percentage * width)
    if description: print(f'\r{description}  [', end = '') 
    else: print(f'\r[', end = '')
    for i in range(0, width, 1):
        if i < filled: print('\x1b[32m=\x1b[0m', end = '')
        elif i == filled: print('>', end = '')
        else: print(' ', end = '')
    print('] %7.2f%%  (%d/%d)' % (percentage * 100, current + 1, total), end = '')
    if current + 1 >= total:
        print('\x1b[?25h')


def load_dataset(corpus_path: str, label_path: str) -> tuple[list[list[str]], list[list[str]]]:
    """
    加载数据集.
    
    Args:
        corpus_path (str): 输入数据路径.
        label_path (str): 输入标签路径.
    
    Returns:
        tuple: 数据和标签.
    """
    ...
    sentences = []
    labels = []
    with open(corpus_path, mode = 'r', encoding = 'utf-8') as fc, open(label_path, mode = 'r', encoding = 'utf-8') as fl:
        for c, l in zip(fc, fl):
            words = c.strip().split()
            tags = l.strip().split()
            if len(words) > 0 and len(words) == len(tags):
                sentences.append(words)
                labels.append(tags)
    return sentences, labels


def build_vocabulary(corpus: list[list[str]], label: list[list[str]]) -> tuple[dict[str, int], dict[str, int]]:
    """
    构建字符串映射整型的键值对字典.

    Args:
        corpus (list[list[str]]): 文本.
        label (list[list[str]]): 标签.

    Returns:
        tuple: 文本数据字典和标签字典.
    """
    word2index = {'<PAD>': 0, '<UNK>': 1}
    tag2index = {'<PAD>': 0}
    for sentence in corpus:
        for word in sentence:
            if word not in word2index.keys():
                word2index[word] = len(word2index)
    for tags in label:
        for tag in tags:
            if tag not in tag2index.keys():
                tag2index[tag] = len(tag2index)
    return word2index, tag2index


def collate_function(batch: list[tuple[torch.Tensor, torch.Tensor]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Padding 核对处理.
    
    Args:
        batch (list[tuple[torch.Tensor, torch.Tensor]]): 数据与标签构成的元组对列表.

    Returns:
        tuple: 填充好的数据、填充好的标签、填充的 bool 型掩码.
    """
    inputs, targets = zip(*batch)
    inputs_padding = torch.nn.utils.rnn.pad_sequence(inputs, batch_first = True, padding_value = 0)
    targets_padding = torch.nn.utils.rnn.pad_sequence(targets, batch_first = True, padding_value = 0)
    mask = (inputs_padding != 0).bool()
    return inputs_padding, targets_padding, mask


class DatasetNER(torch.utils.data.Dataset):
    def __init__(
        self, *args,
        corpus: list[list[str]],
        label: list[list[str]],
        word2index: dict[str, int],
        tag2index: dict[str, int],
        max_len: int,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.corpus = corpus
        self.label = label
        self.word2index = word2index
        self.tag2index = tag2index
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.corpus)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        words = self.corpus[index]
        tags = self.label[index]
        word_id = [self.word2index.get(word, self.word2index['<UNK>']) for word in words]
        tag_id = [self.tag2index.get(tag, self.tag2index['<PAD>']) for tag in tags]
        if len(word_id) > self.max_len:
            word_id = word_id[:self.max_len]
            tag_id = tag_id[:self.max_len]
        return torch.LongTensor(word_id), torch.LongTensor(tag_id)


def evaluate(
    device: str,
    model: utils.net.BiLSTM_CRF,
    dataloader: torch.utils.data.DataLoader,
    index2tag: dict[int, str]
) -> tuple[float, float, float, float, float, float, dict, dict]:
    all_predictions = []
    all_labels = []
    model.eval()
    with torch.no_grad():
        for inputs, targets, mask in dataloader:
            inputs = inputs.to(device)
            mask = mask.to(device)
            batch_predictions = model.forward(inputs, mask = mask)
            for idx, predictions in enumerate(batch_predictions):
                size = len(predictions)
                y = targets[idx][:size].tolist()
                all_predictions.extend([index2tag[i] for i in predictions])
                all_labels.extend([index2tag[i] for i in y])
    label_no_o = sorted(list(set(all_labels) - {'O', '<PAD>'}))
    # report_all = sklearn.metrics.classification_report(
    #     y_true = all_labels,
    #     y_pred = all_predictions,
    #     digits = 5,
    #     zero_division = 0,
    #     output_dict = True
    # )
    # report_no_o = sklearn.metrics.classification_report(
    #     y_true = all_labels,
    #     y_pred = all_predictions,
    #     labels = label_no_o,
    #     digits = 5,
    #     zero_division = 0,
    #     output_dict = True
    # )
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
    if precision_no_o + recall_no_o == 0: f1_no_o = 0.0
    else: f1_no_o = 2 * precision_no_o * recall_no_o / (precision_no_o + recall_no_o)
    report_all = dict()
    report_no_o = dict()
    return precision_all, recall_all, f1_all, precision_no_o, recall_no_o, precision_no_o, f1_no_o, report_all, report_no_o