import torch
# 在代码开头添加这个（临时解决方案）
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['CUDA_HOME'] = '/usr/local/cuda-13.0'

if torch.cuda.is_available():
    print("GPU is available")
else:
    print("GPU is not available")

    
print(torch.__version__)  # PyTorch版本
print(torch.version.cuda)  # PyTorch内置的CUDA版本（如果是GPU版本）