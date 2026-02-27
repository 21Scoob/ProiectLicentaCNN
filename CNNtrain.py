import diffusers
from torchvision.models import resnet50, ResNet50_Weights
import torch
import torchvision
from torchvision import transforms, models

#Data Augmentation for training, validation and test proccess

image_transforms = {
    "train": transforms.Compose([
        transforms.RandomResizedCrop(size=256, scale=(0.8,1)),
        transforms.RandomRotation(degrees=15),
        transforms.RandomHorizontalFlip(),
        transforms.CenterCrop(size=224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ]),
        
    "valid": transforms.Compose([
        transforms.Resize(size=256),
        transforms.CenterCrop(size=224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ]),
    
    "test": transforms.Compose([
        transforms.Resize(size=256),
        transforms.CenterCrop(size=224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ])
}   

#Setting up the model

device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
weights = models.ResNet50_Weights
model = models.resnet50(weights=weights).to(device)

