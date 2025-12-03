import os
import torch
import platform


hyperparameter_configuration = {
    'proportion_trainset': 0.8,
    'embedding_dim': 2048,
    'hidden_dim': 4096,
    'batch_size': 1024,
    'epochs': 100,
    'learning_rate': 0.001,
    'max_len': 256,
    'train_corpus': os.path.join('data', 'train_corpus.txt'),
    'train_label': os.path.join('data', 'train_label.txt'),
    'test_corpus': os.path.join('data', 'test_corpus.txt'),
    'test_label': os.path.join('data', 'test_label.txt'),
    'device': torch.device('mps' if platform.system() == 'Darwin' else 'cuda:7' if torch.cuda.is_available() else 'cpu')
}