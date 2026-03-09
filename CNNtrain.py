import diffusers
from torchvision.models import resnet50, ResNet50_Weights
import torch
import torchvision
from torchvision import models, datasets
import torchvision.transforms.v2 as transforms_v2

#Data Augmentation for training, validation and test proccess

image_transforms = {
    "train": transforms_v2.Compose([
        transforms_v2.RandomResizedCrop(size=256, scale=(0.8,1)),
        transforms_v2.RandomRotation(degrees=15),
        transforms_v2.RandomHorizontalFlip(),
        transforms_v2.CenterCrop(size=224),
        transforms_v2.ToDtype(torch.float32, scale=True),
        transforms_v2.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ]),
        
    "valid": transforms_v2.Compose([
        transforms_v2.Resize(size=256),
        transforms_v2.CenterCrop(size=224),
        transforms_v2.ToDtype(torch.float32, scale=True),
        transforms_v2.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ]),
    
    "test": transforms_v2.Compose([
        transforms_v2.Resize(size=256),
        transforms_v2.CenterCrop(size=224),
        transforms_v2.ToDtype(torch.float32, scale=True),
        transforms_v2.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ])
}   
# Loading up the data and start augmenting it

image_datasets = {
    "train": datasets.ImageFolder('')
}

#Setting up the model

device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
weights = models.ResNet50_Weights.IMAGENET1K_V1
model = models.resnet50(weights=weights).to(device)
