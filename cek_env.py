import torch
import torchvision
import cv2
import numpy as np
import matplotlib
from torchvision import models

print("Python OK")
print("torch        :", torch.__version__)
print("torchvision  :", torchvision.__version__)
print("opencv       :", cv2.__version__)
print("numpy        :", np.__version__)
print("matplotlib   :", matplotlib.__version__)
print("GPU CUDA     :", torch.cuda.is_available())

# uji unduh bobot pretrained (butuh internet, sekitar 45 MB)
m = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
print("ResNet-18 pretrained berhasil dimuat")