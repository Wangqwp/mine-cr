# U-Bench × CoNSeP 病理细胞核实例分割

使用 U-Bench (U-Net变体基准) 中的模型在 CoNSeP 病理图像数据集上完成实例分割任务。

## 背景

- **[U-Bench](https://arxiv.org/abs/2510.07041)** — 100个 U-Net 变体在28个医学图像数据集上的全面基准 (Fenghe Tang et al., USTC)
- **[CoNSeP](https://warwick.ac.uk/fac/sci/dcs/research/tia/data/hovernet/)** — Colorectal Nuclear Segmentation and Phenotypes 数据集，41张 H&E 结直肠病理图，24,319个细胞核标注

## 方法

1. 使用 `segmentation-models-pytorch` (SMP) 加载 U-Net 变体（U-Net++、DeepLabV3+、FPN等）
2. 在 CoNSeP 上训练**语义分割**（核/背景二分类）
3. 后处理：**距离变换 + Watershed 分水岭算法** 将语义图转化为实例分割
4. 评估指标：**AJI (Aggregated Jaccard Index)**

## 文件

| 文件 | 说明 |
|------|------|
| `ubench_consep.py` | 完整 pipeline：训练、推理、评估、可视化 |

## 快速开始

```bash
# 1. 安装依赖
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install segmentation-models-pytorch opencv-python scikit-image scikit-learn
pip install tqdm albumentations matplotlib scipy

# 2. 下载 CoNSeP 数据
# 从 https://warwick.ac.uk/fac/sci/dcs/research/tia/data/hovernet/ 下载
# 解压到 ./CoNSeP/ (Train/, Test/ 子目录)

# 3. 训练
python ubench_consep/ubench_consep.py --mode train --model unetplusplus

# 4. 训练+评估
python ubench_consep/ubench_consep.py --mode full
```

## 支持的模型

| 模型 | 参数 | 特点 |
|------|------|------|
| U-Net | `--model unet` | 经典基线 |
| U-Net++ | `--model unetplusplus` | 密集跳跃连接 |
| DeepLabV3+ | `--model deeplabv3p` | ASPP多尺度 |
| FPN | `--model fpn` | 轻量高效 |
| PSPNet | `--model pspnet` | 全局上下文 |
| MAnet | `--model manet` | 多头注意力 |
