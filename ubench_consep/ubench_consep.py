"""
U-Bench × CoNSeP 实例分割完整实现
==================================
方案：使用 segmentation-models-pytorch (SMP) 中的 U-Net 变体
     进行语义分割 + 距离变换/Watershed 后处理得到实例分割

包含 U-Bench 基准中的经典模型：
  - UNet (baseline)
  - UNet++ (Nested UNet)
  - DeepLabV3+
  - FPN (Feature Pyramid Network)
  - PSPNet
  - MANet (Multi-scale Attention Net)

引用：
  U-Bench: arXiv 2510.07041
  CoNSeP:  HoVer-Net, Medical Image Analysis 2019
"""

import os
import sys
import math
import glob
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import cv2
from scipy import ndimage as ndi
from skimage import morphology as morph
from skimage.segmentation import watershed
from skimage.measure import label as connected_label
from skimage.color import label2rgb
import matplotlib.pyplot as plt
from tqdm import tqdm
import albumentations as A
from albumentations.pytorch import ToTensorV2

# ============================================================
# 配置参数
# ============================================================
class Config:
    # 数据路径
    data_root = "./CoNSeP"                # 下载后解压到这里

    # 模型设置
    model_name = "unetplusplus"            # 可选: unet, unetplusplus, deeplabv3+, fpn, pspnet, manet
    encoder_name = "resnet34"              # backbone: resnet34, efficientnet-b0, etc.
    encoder_weights = "imagenet"           # 预训练权重

    # 训练设置
    image_size = 256                       # 训练patch大小
    batch_size = 8
    num_epochs = 100
    learning_rate = 3e-4
    device = "cuda" if torch.cuda.is_available() else "cpu"
    num_classes = 1                        # 二分类: 核/背景
    save_dir = "./checkpoints"

    # 后处理
    min_nucleus_size = 20                  # 最小细胞核像素数
    watershed_threshold = 0.4              # 距离变换阈值


config = Config()
os.makedirs(config.save_dir, exist_ok=True)
os.makedirs("./results", exist_ok=True)


# ============================================================
# CoNSeP 数据加载器
# ============================================================
def load_mat_label(mat_path: str) -> np.ndarray:
    """
    从 .mat 文件加载实例分割标签。
    CoNSeP 的 .mat 包含 'inst_map' (实例ID) 和 'type_map' (类型ID)。
    """
    import scipy.io as sio
    data = sio.loadmat(mat_path)
    inst_map = data['inst_map'].astype(np.int32)
    return inst_map  # shape (H, W), 每个像素值 = 实例ID (0=背景)


class CoNSePDataset(Dataset):
    """
    CoNSeP 数据集加载器。
    返回: 图像patch, 二进制掩码 (语义), 实例掩码 (实例)
    """
    def __init__(self, image_dir: str, label_dir: str,
                 split: str = "train",
                 image_size: int = 256,
                 augment: bool = True):
        self.image_size = image_size
        self.augment = augment

        # 获取所有图像文件
        self.image_paths = sorted(glob.glob(os.path.join(image_dir, "*.png")))

        # 对应的标签文件
        self.label_dir = label_dir

        # 数据增强
        if augment:
            self.transform = A.Compose([
                A.RandomRotate90(p=0.5),
                A.Flip(p=0.5),
                A.RandomBrightnessContrast(p=0.2),
                A.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
                ToTensorV2(),
            ])
        else:
            self.transform = A.Compose([
                A.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
                ToTensorV2(),
            ])

        # 预加载所有patch坐标
        self.patches = []
        for img_path in self.image_paths:
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = img.shape[:2]

            # 滑窗裁patch (stride = image_size/2 有重叠)
            stride = image_size // 2
            for y in range(0, h - image_size + 1, stride):
                for x in range(0, w - image_size + 1, stride):
                    self.patches.append((img_path, y, x))

            # 确保覆盖右下角
            if (h - image_size) % stride != 0:
                for x in range(0, w - image_size + 1, stride):
                    self.patches.append((img_path, h - image_size, x))
            if (w - image_size) % stride != 0:
                for y in range(0, h - image_size + 1, stride):
                    self.patches.append((img_path, y, w - image_size))
            if (h - image_size) % stride != 0 and (w - image_size) % stride != 0:
                self.patches.append((img_path, h - image_size, w - image_size))

        print(f"[{split}] 共计 {len(self.image_paths)} 张图像, "
              f"{len(self.patches)} 个patches")

    def _get_label_path(self, img_path: str) -> str:
        """从图像路径推导对应的mat标签路径"""
        basename = os.path.splitext(os.path.basename(img_path))[0]
        return os.path.join(self.label_dir, f"{basename}.mat")

    def __len__(self):
        return len(self.patches)

    def __getitem__(self, idx):
        img_path, y, x = self.patches[idx]

        # 读图像
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        patch_img = img[y:y+self.image_size, x:x+self.image_size]

        # 读实例标签
        mat_path = self._get_label_path(img_path)
        if os.path.exists(mat_path):
            inst_map = load_mat_label(mat_path)
            patch_inst = inst_map[y:y+self.image_size, x:x+self.image_size]
        else:
            patch_inst = np.zeros((self.image_size, self.image_size), dtype=np.int32)

        # 生成二进制掩码: 核区域=1, 背景=0
        binary_mask = (patch_inst > 0).astype(np.float32)

        # 生成距离图: 用于watershed后处理训练（可选）
        if binary_mask.sum() > 0:
            dist = ndi.distance_transform_edt(binary_mask)
            # 归一化
            dist = dist / (dist.max() + 1e-8)
        else:
            dist = np.zeros_like(binary_mask)

        # 增强
        augmented = self.transform(
            image=patch_img,
            mask=binary_mask,
        )
        return {
            'image': augmented['image'],           # (3, H, W)
            'mask': augmented['mask'].unsqueeze(0), # (1, H, W)
            'inst_map': patch_inst,                  # (H, W) 实例ID
            'path': img_path,
            'y': y,
            'x': x,
        }


# ============================================================
# 模型构建 (通过 SMP 调用 U-Bench 系列模型)
# ============================================================
def create_model(model_name: str, encoder_name: str,
                 encoder_weights: str = "imagenet",
                 num_classes: int = 1) -> nn.Module:
    """
    创建U-Net变体模型。
    这些模型都包含在U-Bench基准测试的100个变体中。
    """
    import segmentation_models_pytorch as smp

    # 模型名称映射
    model_map = {
        "unet": smp.Unet,
        "unetplusplus": smp.UnetPlusPlus,
        "deeplabv3+": smp.DeepLabV3Plus,
        "deeplabv3p": smp.DeepLabV3Plus,
        "fpn": smp.FPN,
        "pspnet": smp.PSPNet,
        "manet": smp.MAnet,
        "linknet": smp.Linknet,
        "pan": smp.PAN,
    }

    if model_name.lower() not in model_map:
        raise ValueError(f"未知模型: {model_name}。可选: {list(model_map.keys())}")

    model_class = model_map[model_name.lower()]
    model = model_class(
        encoder_name=encoder_name,
        encoder_weights=encoder_weights,
        in_channels=3,
        classes=num_classes,
        activation=None,  # 输出logits，推理时加sigmoid
    )
    return model


# ============================================================
# 训练函数
# ============================================================
def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    pbar = tqdm(dataloader, desc="训练")

    for batch in pbar:
        images = batch['image'].to(device)          # (B, 3, H, W)
        masks = batch['mask'].to(device)            # (B, 1, H, W)

        optimizer.zero_grad()
        logits = model(images)                      # (B, 1, H, W)

        # 处理输出尺寸不一致（某些模型下采样后上采样有问题）
        if logits.shape[-2:] != masks.shape[-2:]:
            logits = F.interpolate(
                logits, size=masks.shape[-2:],
                mode='bilinear', align_corners=False
            )

        loss = criterion(logits, masks)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        pbar.set_postfix({"loss": f"{loss.item():.4f}"})

    return total_loss / len(dataloader)


def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    total_dice = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="验证"):
            images = batch['image'].to(device)
            masks = batch['mask'].to(device)

            logits = model(images)
            if logits.shape[-2:] != masks.shape[-2:]:
                logits = F.interpolate(
                    logits, size=masks.shape[-2:],
                    mode='bilinear', align_corners=False
                )

            loss = criterion(logits, masks)
            total_loss += loss.item()

            # Dice 系数
            probs = torch.sigmoid(logits)
            preds = (probs > 0.5).float()
            intersection = (preds * masks).sum()
            dice = (2. * intersection) / (preds.sum() + masks.sum() + 1e-8)
            total_dice += dice.item()

    return total_loss / len(dataloader), total_dice / len(dataloader)


def train():
    print(f"设备: {config.device}")
    print(f"模型: {config.model_name} + {config.encoder_name}")

    # 数据路径
    train_img_dir = os.path.join(config.data_root, "Train", "Images")
    train_lbl_dir = os.path.join(config.data_root, "Train", "Labels")
    test_img_dir = os.path.join(config.data_root, "Test", "Images")
    test_lbl_dir = os.path.join(config.data_root, "Test", "Labels")

    # 数据集
    train_dataset = CoNSePDataset(
        train_img_dir, train_lbl_dir,
        split="train", image_size=config.image_size,
        augment=True,
    )
    val_dataset = CoNSePDataset(
        test_img_dir, test_lbl_dir,
        split="test", image_size=config.image_size,
        augment=False,
    )

    train_loader = DataLoader(
        train_dataset, batch_size=config.batch_size,
        shuffle=True, num_workers=0, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=config.batch_size,
        shuffle=False, num_workers=0, pin_memory=True,
    )

    # 模型
    model = create_model(
        config.model_name, config.encoder_name,
        config.encoder_weights, config.num_classes,
    )
    model = model.to(config.device)

    # 损失函数 & 优化器
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config.num_epochs
    )

    # 训练循环
    best_dice = 0.0
    for epoch in range(1, config.num_epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, config.device)
        val_loss, val_dice = validate(model, val_loader, criterion, config.device)
        scheduler.step()

        print(f"Epoch {epoch:3d}/{config.num_epochs} | "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | Val Dice: {val_dice:.4f}")

        # 保存最佳模型
        if val_dice > best_dice:
            best_dice = val_dice
            torch.save(model.state_dict(),
                       os.path.join(config.save_dir, "best_model.pth"))
            print(f"  → 保存最佳模型, Dice={best_dice:.4f}")

    print(f"训练完成！最佳验证 Dice = {best_dice:.4f}")
    return model


# ============================================================
# 后处理: 语义掩码 → 实例分割
# ============================================================
def mask_to_instances(prob_map: np.ndarray,
                      threshold: float = 0.5,
                      min_size: int = 20) -> np.ndarray:
    """
    将语义概率图通过 Watershed 转换成实例分割掩码。

    步骤:
    1. 阈值化得到二进制掩码
    2. 距离变换 (核中心值高，边缘值低)
    3. 寻找局部极大值作为种子点
    4. Watershed 分水岭算法分离实例
    """
    # 1. 二进制掩码
    binary = (prob_map > threshold).astype(np.uint8)

    if binary.sum() == 0:
        return np.zeros_like(prob_map, dtype=np.int32)

    # 2. 距离变换
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

    # 3. 寻找种子点 (局部极大值)
    # 平滑后找峰值
    smooth_dist = cv2.GaussianBlur(dist, (5, 5), 0)

    # 用 h-maxima 变换抑制噪声峰值
    h_maxima = morph.h_maxima(smooth_dist, 0.3 * smooth_dist.max())
    seeds = connected_label(h_maxima)

    # 如果没找到种子，试试更低的阈值
    if seeds.max() == 0:
        h_maxima = morph.h_maxima(smooth_dist, 0.1 * smooth_dist.max())
        seeds = connected_label(h_maxima)

    # 如果还是没找到，整个前景作为单个实例
    if seeds.max() == 0:
        seeds = binary.astype(np.int32)

    # 4. Watershed
    # 用距离图的负值作为地形，种子点作为标记
    markers = seeds.astype(np.int32)
    markers[binary == 0] = 0  # 背景标记为0
    labels = watershed(-dist, markers, mask=binary, watershed_line=True)

    # 5. 过滤过小实例
    result = np.zeros_like(labels)
    for inst_id in range(1, labels.max() + 1):
        mask = (labels == inst_id)
        if mask.sum() >= min_size:
            result[mask] = inst_id

    return result


# ============================================================
# 推理 + 评估
# ============================================================
def compute_aji(pred_inst: np.ndarray, gt_inst: np.ndarray) -> float:
    """
    Aggregated Jaccard Index (AJI) — CoNSeP 的主要评估指标。

    对每个 GT 实例找到匹配的预测实例，计算 IoU 并聚合。
    """
    pred_ids = np.unique(pred_inst)
    pred_ids = pred_ids[pred_ids > 0]    # 去掉背景
    gt_ids = np.unique(gt_inst)
    gt_ids = gt_ids[gt_ids > 0]

    if len(gt_ids) == 0 and len(pred_ids) == 0:
        return 1.0
    if len(gt_ids) == 0:
        return 0.0

    # 为每个 GT 实例找最佳匹配的预测实例
    matched_pred = set()
    total_i = 0
    total_u = 0

    for gt_id in gt_ids:
        gt_mask = (gt_inst == gt_id)
        best_iou = 0
        best_pred_id = 0

        for pred_id in pred_ids:
            pred_mask = (pred_inst == pred_id)
            inter = (gt_mask & pred_mask).sum()
            union = (gt_mask | pred_mask).sum()
            iou = inter / max(union, 1)

            if iou > best_iou:
                best_iou = iou
                best_pred_id = pred_id

        if best_pred_id > 0:
            matched_pred.add(best_pred_id)
            total_i += (gt_mask & (pred_inst == best_pred_id)).sum()
            total_u += (gt_mask | (pred_inst == best_pred_id)).sum()

    # 未匹配的预测实例（FP）加入分母
    unmatched_pred = set(pred_ids) - matched_pred
    for pred_id in unmatched_pred:
        total_u += (pred_inst == pred_id).sum()

    return total_i / max(total_u, 1)


def infer_and_evaluate(model, dataloader, device,
                       save_vis: bool = True) -> Dict:
    """
    在测试集上进行推理并评估实例分割效果。
    """
    model.eval()

    all_aji = []
    all_dice = []

    # 用于全图重建
    predictions = {}  # path -> (H, W) 预测实例图

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="推理"):
            images = batch['image'].to(device)
            gt_inst = batch['inst_map']  # numpy, (B, H, W)
            paths = batch['path']
            ys = batch['y'].numpy()
            xs = batch['x'].numpy()

            # 模型推理
            logits = model(images)
            if logits.shape[-2] != config.image_size:
                logits = F.interpolate(
                    logits, size=(config.image_size, config.image_size),
                    mode='bilinear', align_corners=False
                )
            probs = torch.sigmoid(logits).cpu().numpy()  # (B, 1, H, W)

            for i in range(len(images)):
                path = paths[i]

                # 语义 → 实例
                prob_map = probs[i, 0]
                pred_inst = mask_to_instances(
                    prob_map,
                    threshold=config.watershed_threshold,
                    min_size=config.min_nucleus_size,
                )

                # 重建全图预测
                if path not in predictions:
                    # 读取原图尺寸
                    img = cv2.imread(path)
                    h, w = img.shape[:2]
                    predictions[path] = {
                        'pred': np.zeros((h, w), dtype=np.int32),
                        'counts': np.zeros((h, w), dtype=np.int32),
                    }

                y, x = ys[i], xs[i]
                pred = predictions[path]

                # 重叠区域的简单处理: 取平均 (这里只做增量标注)
                # 实际可以用更复杂的融合策略
                H_pred, W_pred = pred_inst.shape

                # 将patch结果加上偏移ID避免冲突
                patch_offset = pred['pred'].max() + 1
                patch_inst_offset = pred_inst.copy()
                patch_inst_offset[patch_inst_offset > 0] += patch_offset

                # 叠加到全图 (简单覆盖，patch重叠区以最后为准)
                pred['pred'][y:y+H_pred, x:x+W_pred] = patch_inst_offset

            # 如需要可视化样例
            if save_vis and len(all_aji) < 4:
                fig, axes = plt.subplots(1, 4, figsize=(16, 4))
                idx = 0

                img = (batch['image'][idx].cpu().permute(1,2,0).numpy() * 0.5 + 0.5)
                img = np.clip(img, 0, 1)
                axes[0].imshow(img)
                axes[0].set_title("输入图像")
                axes[0].axis('off')

                axes[1].imshow(probs[idx, 0], cmap='hot', vmin=0, vmax=1)
                axes[1].set_title("语义概率图")
                axes[1].axis('off')

                gt_show = gt_inst[idx].numpy()
                axes[2].imshow(label2rgb(gt_show, bg_label=0))
                axes[2].set_title(f"GT 实例 ({gt_show.max()}个)")
                axes[2].axis('off')

                pred_show = pred_inst
                axes[3].imshow(label2rgb(pred_show, bg_label=0))
                axes[3].set_title(f"预测实例 ({pred_show.max()}个)")
                axes[3].axis('off')

                plt.tight_layout()
                plt.savefig(f"./results/sample_{len(all_aji)}.png", dpi=150)
                plt.close()

    print("\n===== 实例分割评估结果 =====")
    aji_list = []
    dice_list = []

    for path, data in predictions.items():
        pred_full = data['pred']

        # 读取GT实例掩码
        mat_path = os.path.join(
            os.path.dirname(path).replace("Images", "Labels"),
            os.path.splitext(os.path.basename(path))[0] + ".mat"
        )
        if os.path.exists(mat_path):
            gt_full = load_mat_label(mat_path)

            # 只评估有标注的区域
            aji = compute_aji(pred_full, gt_full)
            aji_list.append(aji)
            print(f"  {os.path.basename(path)}: AJI = {aji:.4f}")

    if aji_list:
        print(f"\n平均 AJI: {np.mean(aji_list):.4f} ± {np.std(aji_list):.4f}")

    return {
        'aji': np.mean(aji_list) if aji_list else 0,
        'aji_list': aji_list,
        'predictions': predictions,
    }


# ============================================================
# 主入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="U-Bench × CoNSeP 实例分割")
    parser.add_argument("--mode", type=str, default="train",
                        choices=["train", "eval", "full"],
                        help="运行模式")
    parser.add_argument("--model", type=str, default=config.model_name,
                        help=f"模型名称 (默认: {config.model_name})")
    parser.add_argument("--encoder", type=str, default=config.encoder_name,
                        help=f"Encoder backbone (默认: {config.encoder_name})")
    parser.add_argument("--epochs", type=int, default=config.num_epochs,
                        help=f"训练轮数 (默认: {config.num_epochs})")
    parser.add_argument("--batch_size", type=int, default=config.batch_size,
                        help=f"批次大小 (默认: {config.batch_size})")
    parser.add_argument("--image_size", type=int, default=config.image_size,
                        help=f"Patch尺寸 (默认: {config.image_size})")
    parser.add_argument("--data_root", type=str, default=config.data_root,
                        help="CoNSeP 数据根目录")
    args = parser.parse_args()

    # 更新配置
    config.model_name = args.model
    config.encoder_name = args.encoder
    config.num_epochs = args.epochs
    config.batch_size = args.batch_size
    config.image_size = args.image_size
    config.data_root = args.data_root

    print("=" * 60)
    print("  U-Bench × CoNSeP 实例分割")
    print("=" * 60)
    print(f"  模型:       {config.model_name} + {config.encoder_name}")
    print(f"  设备:       {config.device}")
    print(f"  数据根目录: {config.data_root}")
    print(f"  Patch尺寸:  {config.image_size}")
    print(f"  Batch大小:  {config.batch_size}")
    print(f"  训练轮数:   {config.num_epochs}")
    print("=" * 60)

    if args.mode in ("train", "full"):
        # 训练语义分割模型
        model = train()
    else:
        # 直接加载训练好的模型
        model = create_model(
            config.model_name, config.encoder_name,
            encoder_weights=None,
            num_classes=config.num_classes,
        )
        checkpoint_path = os.path.join(config.save_dir, "best_model.pth")
        if os.path.exists(checkpoint_path):
            model.load_state_dict(torch.load(checkpoint_path, map_location=config.device, weights_only=True))
            print(f"已加载模型: {checkpoint_path}")
        else:
            print(f"警告: 未找到checkpoint {checkpoint_path}，使用随机初始化")
        model = model.to(config.device)

    if args.mode in ("eval", "full"):
        # 评估
        test_img_dir = os.path.join(config.data_root, "Test", "Images")
        test_lbl_dir = os.path.join(config.data_root, "Test", "Labels")

        test_dataset = CoNSePDataset(
            test_img_dir, test_lbl_dir,
            split="test", image_size=config.image_size,
            augment=False,
        )
        test_loader = DataLoader(
            test_dataset, batch_size=config.batch_size,
            shuffle=False, num_workers=0,
        )

        results = infer_and_evaluate(model, test_loader, config.device, save_vis=True)

        # 保存结果
        np.save("./results/aji_scores.npy", results['aji_list'])
        print(f"\nAJI 分数已保存到 ./results/")

    print("\n✨ 完成！")


if __name__ == "__main__":
    main()
