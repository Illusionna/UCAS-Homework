import os
import re
import csv
import torch
import shutil
import platform
import itertools


def cls() -> None:
    os.system('')
    for root, dirs, files in os.walk(os.getcwd()):
        for dir in dirs:
            if dir == '__pycache__':
                shutil.rmtree(os.path.join(root, dir))
    try:
        os.system(
            {'Windows': 'cls', 'Linux': 'clear', 'Darwin': 'clear'}[platform.system()]
        )
    except:
        print('\033[H\033[J', end = '')
cls()


def progress_bar(current: int, total: int, description: str = None) -> None:
    """显示进度条.

    Args:
        current (int): 当前循环次数.
        total (int): 一共需要循环次数.
        description (str): 描述文本.

    Returns:
        None: 无.
    """
    width = 50
    print('\x1b[?25l', end = '')
    percentage = (current + 1) / total
    filled = int(percentage * width)
    if description:
        print(f'\r{description}  [', end = '')
    else:
        print(f'\r[', end = '')
    for i in range(0, width, 1):
        if i < filled:
            print('\x1b[32m=\x1b[0m', end = '')
        elif i == filled:
            print('>', end = '')
        else:
            print(' ', end = '')
    print('] %7.2f%%  (%d/%d)' % (percentage * 100, current + 1, total), end = '')
    if current + 1 == total:
        print('\x1b[?25h')


class NNLM(torch.nn.Module):
    """
    `NNLM` 类根据论文 "`A Neural Probabilistic Language Model (2003)`" 公式编写.
    """

    def __init__(self, V: int, m: int, h: int, n: int, *args, **kwargs) -> None:
        """初始化构造函数.

        Args:
            V (int): 词汇字典所含元素个数.
            m (int): 词向量维度.
            h (int): 隐藏层神经元个数.
            n (int): 已知前 `n-1` 个单词, 推理接下来第 `n` 个单词, 论文中 `n` 的最小索引从 `1` 开始.

        Returns:
            None: 无.
        """
        super().__init__(*args, **kwargs)
        # θ = (b, d, W, U, H, C)
        self.b = torch.nn.Parameter(torch.randn(V))
        self.d = torch.nn.Parameter(torch.randn(h))
        self.W = torch.nn.Parameter(torch.rand((n - 1) * m, V))
        self.U = torch.nn.Parameter(torch.rand(h, V))
        self.H = torch.nn.Parameter(torch.rand((n - 1) * m, h))
        self.C = torch.nn.Embedding(num_embeddings = V, embedding_dim = m)
        self._m = m
        self._n = n

    def forward(self, x: torch.LongTensor) -> torch.Tensor:
        x = self.C(x)
        x = x.view(-1, (self._n - 1) * self._m)
        y = self.b + x @ self.W + torch.tanh(self.d + x @ self.H) @ self.U
        return y


class Tokenizer:
    """
    中英文分词器.
    """

    @staticmethod
    def en(sentence: str) -> list[str]:
        """英文句子分词器.

        Args:
            sentence (str): 英文句子.
        
        Returns:
            list[str]: 分词结果.
        
        Example::
            >>> Tokenizer.en('In the beginning God created the heavens and the earth. The earth was formless and void, and darkness was over the surface of the deep, and the Spirit of God was moving over the surface of the waters.')
            >>> ['in', 'the', 'beginning', 'god', 'created', 'the', 'heavens', 'and', 'the', 'earth', 'the', 'earth', 'was', 'formless', 'and', 'void', 'and', 'darkness', 'was', 'over', 'the', 'surface', 'of', 'the', 'deep', 'and', 'the', 'spirit', 'of', 'god', 'was', 'moving', 'over', 'the', 'surface', 'of', 'the', 'waters']
        """
        return re.sub(r'[^\w\s]', '', sentence).lower().split()

    @staticmethod
    def zh(sentence: str) -> list[str]:
        """中文句子分词器.

        Args:
            sentence (str): 中文句子.
        
        Returns:
            list[str]: 分词结果.
        """
        return re.split(r'\s+', re.sub(r'[，。,、“”‘’：:；;？?！!（）()]', '', sentence).strip())


class Train:
    """
    神经网络训练器.
    """

    @staticmethod
    def en(epoch: int, device: torch.device) -> None:
        """英文训练器.
        
        Args:
            epoch (int): 迭代次数.
            device (torch.device): 计算处理器设备.
        
        Returns:
            None: 无.
        """
        words: list[list[str]] = []
        with open(os.path.join('data', 'en.txt'), mode = 'r', encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                words.append(Tokenizer.en(line))

        n = 8
        sentences_input: list[list[str]] = []
        sentences_target: list[str] = []
        for word in words:
            if len(word) >= n:
                sentences_input.append(word[: (n - 1)])
                sentences_target.append(word[n - 1])

        vocabulary = set(itertools.chain.from_iterable(words))
        word2index = {value: key for key, value in enumerate(vocabulary)}
        # index2word = {key: value for key, value in enumerate(vocabulary)}

        criterion = torch.nn.CrossEntropyLoss()
        model = NNLM(V = len(vocabulary), m = 32, h = 12, n = n).to(device)
        optimizer = torch.optim.Adam(params = model.parameters(), lr = 1e-3)

        x = torch.LongTensor([[word2index.get(j) for j in i] for i in sentences_input]).to(device)
        target = torch.LongTensor([word2index.get(i) for i in sentences_target]).to(device)

        for i in range(0, epoch, 1):
            optimizer.zero_grad()
            y = model.forward(x)
            loss = criterion.forward(y, target)
            loss.backward()
            optimizer.step()
            progress_bar(i, epoch, description = f'loss = {loss:.7f}')

        matrix = model.C.weight.detach().cpu().numpy()

        with open('en_embedding_result.csv', mode = 'w', newline = '') as f:
            writer = csv.writer(f)
            features = list(word2index.keys())
            for name, row in zip(features, matrix):
                writer.writerow([name] + row.tolist())
        print(f'\x1b[32m[OK] "en_embedding_result.csv".\x1b[0m')

    @staticmethod
    def zh(epoch: int, device: torch.device) -> None:
        """中文训练器.

        Args:
            epoch (int): 迭代次数.
            device (torch.device): 计算处理器设备.

        Returns:
            None: 无.
        """
        words: list[list[str]] = []
        with open(os.path.join('data', 'zh.txt'), mode = 'r', encoding = 'utf-8') as f:
            for line in f:
                line = line.strip()
                words.append(Tokenizer.zh(line))

        n = 8
        sentences_input: list[list[str]] = []
        sentences_target: list[str] = []
        for word in words:
            if len(word) >= n:
                sentences_input.append(word[: (n - 1)])
                sentences_target.append(word[n - 1])

        vocabulary = set(itertools.chain.from_iterable(words))
        word2index = {value: key for key, value in enumerate(vocabulary)}

        criterion = torch.nn.CrossEntropyLoss()
        model = NNLM(V = len(vocabulary), m = 32, h = 12, n = n).to(device)
        optimizer = torch.optim.Adam(params = model.parameters(), lr = 1e-3)

        x = torch.LongTensor([[word2index.get(j) for j in i] for i in sentences_input]).to(device)
        target = torch.LongTensor([word2index.get(i) for i in sentences_target]).to(device)

        for i in range(0, epoch, 1):
            optimizer.zero_grad()
            y = model.forward(x)
            loss = criterion.forward(y, target)
            loss.backward()
            optimizer.step()
            progress_bar(i, epoch, description = f'loss = {loss:.7f}')

        matrix = model.C.weight.detach().cpu().numpy()

        with open('zh_embedding_result.csv', mode = 'w', newline = '') as f:
            writer = csv.writer(f)
            features = list(word2index.keys())
            for name, row in zip(features, matrix):
                writer.writerow([name] + row.tolist())
        print(f'\x1b[32m[OK] "zh_embedding_result.csv".\x1b[0m')


if __name__ == '__main__':
    device = torch.device('mps' if platform.system() == 'Darwin' else 'cuda' if torch.cuda.is_available() else 'cpu')

    Train.en(epoch = 50, device = device)
    Train.zh(epoch = 100, device = device)