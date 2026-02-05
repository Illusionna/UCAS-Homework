# Kaggle: Natural Language Processing with Disaster Tweets

## 模型运行

### Baseline (TF-IDF + Logistic Regression)

```bash
python baseline.py
```

上述命令自动进行训练和测试流程。最终测试结果保存在当前工作目录下的 `submission_lr_*.csv` 文件中。

### 增强模型 (TF-IDF + SVM/决策树/朴素贝叶斯)

```bash
python enhancement.py -m <svm/rbfsvm/dectree/nb> --use-scaler
```

上述指令的 `-m` 标志用于指定使用哪种方法。四个可选项分别对应 *线性核 SVM/RBF 核 SVM/决策树/朴素贝叶斯*。在运行上述指令之前，需要按照实验报告中的设置修改对应 TF-IDF 的 `max_features` 参数（第 23 行）。上述命令自动进行训练和测试流程，最终测试结果保存在当前工作目录下的 `submission_svm/rbfsvm/dectree/nb_*.csv` 文件中。

### BERT 分类器

```bash
python bert.py -m /path/to/your/bert/ckpt
```

可以在 `bert.py` 文件内第 16～20 行自定义训练轮次、最大序列长度、批次大小以及学习率。上述命令自动进行训练和测试流程，最终测试结果将保存在当前工作目录下的 `submission_bert_*.csv` 文件中。

### AdaBoost + BERT

**训练：**

```bash
python train_adaboost.py
```

可以在 `train_adaboost.py` 文件内前 3 行自定义模型位置、总模型数以及每个模型的训练轮次。其余设置与 `bert.py` 文件中保持一致。上述命令仅进行训练。

**测试：**

运行完 `train_adaboost.py` 后，当前工作目录下会存在几个命名为 `best_model_adastage*.pth` 格式的文件，这几个便是训练好的模型以及对应的集成权重 （$\alpha_t$）。使用下面的命令开始测试：

```bash
python adaboost_staged.py --predict best_model_adastage0.pth best_model_adastage1.pth [...]
```

最终结果保存在当前工作目录下的 `submission_adaboost_*.csv` 文件中。