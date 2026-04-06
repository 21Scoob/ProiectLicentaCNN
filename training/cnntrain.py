import diffusers
from torchvision.models import regnet_y_128gf, RegNet_Y_128GF_Weights
import torch
import torchvision
from torchvision import models, datasets
import torchvision.transforms.v2 as transforms_v2
import torch.nn as nn
import time 
from torch.optim import Adam

# Data Augmentation for training, validation and test proccess

image_transforms = {
    'train': transforms_v2.Compose([
        transforms_v2.RandomResizedCrop(size=256, scale=(0.8,1)),
        transforms_v2.RandomRotation(degrees=15),
        transforms_v2.RandomHorizontalFlip(),
        transforms_v2.CenterCrop(size=224),
        transforms_v2.ToImage(),
        transforms_v2.ToDtype(torch.float32, scale=True),
        transforms_v2.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ]),
        
    'valid': transforms_v2.Compose([
        transforms_v2.Resize(size=256),
        transforms_v2.CenterCrop(size=224),
        transforms_v2.ToImage(),
        transforms_v2.ToDtype(torch.float32, scale=True),
        transforms_v2.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ]),
    
    'test': transforms_v2.Compose([
        transforms_v2.Resize(size=256), 
        transforms_v2.CenterCrop(size=224),
        transforms_v2.ToImage(),
        transforms_v2.ToDtype(torch.float32, scale=True),
        transforms_v2.Normalize(mean=[0.485,0.456,0.406],
                             std=[0.229,0.224,0.225])
    ])
}   

# Loading up the data and start augmenting it

image_datasets = {
    'train': datasets.ImageFolder('/Volumes/SSD1/Dataset_Final/train', image_transforms['train']),
    'valid': datasets.ImageFolder('/Volumes/SSD1/Dataset_Final/valid', image_transforms['valid'])
}

image_loaders = {
    'train': torch.utils.data.DataLoader(image_datasets['train'],
                                         batch_size=32,
                                         num_workers=0),
    
     'valid': torch.utils.data.DataLoader(image_datasets['valid'],
                                         batch_size=32,
                                         num_workers=0)
}
# Setting up the model

device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
weights = models.RegNet_Y_128GF_Weights.IMAGENET1K_SWAG_E2E_V1
model = models.regnet_y_128gf(weights=weights).to(device)

for param in model.parameters():
    
    param.requires_grad = False
    
fc_inputs = model.fc.in_features

model.fc = nn.Sequential(
    nn.Linear(fc_inputs, 256),
    nn.ReLU(),
    nn.Dropout(0.45),
    nn.Linear(256, 2)
)

model.to(device)

loss_func = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.fc.parameters())
epochs=32

def train_model(model, loss_func, optimizer, epochs):
    
    for epoch in range(epochs):
        
        epoch_start = time.time()
        print("Epoch: {}/{}".format(epoch+1, epochs))
        print('-' * 10)
        
        for phase in ['train','valid']:
            
            if phase == 'train':
                model.train()
                
            else:
                model.eval()
                
            running_loss = 0.0
            running_corrects = 0.0
        
            for inputs, labels in image_loaders[phase]:
            
                inputs = inputs.to(device)
                labels = labels.to(device)
            
                outputs = model(inputs)
                loss = loss_func(outputs, labels)
            
                if phase == 'train':
                
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                
                _, preds = torch.max(outputs, 1)
                running_loss += loss.detach() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            
            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = running_corrects / len(image_datasets[phase])
        
            print('{} loss: {:.4f}, acc: {:.4f}'.format(phase,
                                                        epoch_loss.item(),
                                                        epoch_acc.item()))
        
    return model

if __name__ == '__main__':
    
    train_model(model, loss_func, optimizer, epochs)
    
    file_name = 'vitdeepfake.pth'
    
    torch.save(train_model.state_dict(), file_name)