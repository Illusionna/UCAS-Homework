import utils.crf
import torch


class BiLSTM_CRF(torch.nn.Module):
    def __init__(
        self, *args,
        vocabulary_size: int,
        tag2index: dict[str, int],
        embedding_dimension: int,
        hidden_dimension: int,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.embedding = torch.nn.Embedding(vocabulary_size, embedding_dimension)
        self.lstm = torch.nn.LSTM(
            input_size = embedding_dimension,
            hidden_size = hidden_dimension // 2,
            num_layers = 1,
            batch_first = True,
            bidirectional = True
        )
        self.map = torch.nn.Linear(hidden_dimension, len(tag2index))
        self.crf = utils.crf.CRF(len(tag2index), batch_first = True)
    
    def forward(self, x: torch.Tensor, tags: torch.Tensor = None, mask: torch.Tensor = None) -> torch.Tensor | list[list[int]]:
        lstm, _ = self.lstm.forward((self.embedding.forward(x)))
        emissions = self.map.forward(lstm)
        if tags is not None:
            return -self.crf.forward(emissions = emissions, tags = tags, mask = mask, reduction = 'mean')
        else:
            return self.crf.decode(emissions = emissions, mask = mask)