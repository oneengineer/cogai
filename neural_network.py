import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from functools import lru_cache
from spaces import ActionSpaces
import pickle
from controls.Events import *
from image_to_ascii import UnionASCIIConverter
from torch import nn
from neural_utils import *

def conv3x3(inc:int,outc:int, stride:int = 1, padding = 1):
    return nn.Conv2d(inc, outc, (3,3), stride, padding)

def conv3x3T(inc:int,outc:int, stride:int = 1, padding = 1):
    return nn.ConvTranspose2d(inc, outc, (3,3), stride, padding)

class ResBlock(nn.Module):

    def __init__(self, channel):
        super().__init__()
        self.conv1 = conv3x3(channel, channel, padding=1)
        self.conv2 = conv3x3(channel, channel, padding=1)
        self.batchNorm1 = nn.BatchNorm2d(channel)
        self.batchNorm2 = nn.BatchNorm2d(channel)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        temp = self.conv1(x)
        temp = self.batchNorm1(temp)
        temp = self.relu(temp)
        temp = self.conv2(temp)
        temp = self.batchNorm2(temp)
        temp = temp + x
        temp = self.relu(temp)
        return temp

class UpsampleConvLayer(torch.nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size):
        super(UpsampleConvLayer, self).__init__()
        self.upsample = nn.Upsample(scale_factor=2, mode='nearest')
        self.conv2d = torch.nn.ConvTranspose2d(in_channels, out_channels, kernel_size, stride=2)

    def forward(self, x):
        x_in = x
        x_in = self.upsample(x_in)
        out = self.conv2d(x_in)
        # print("up.in", x.shape, "up.out",out.shape) # debug
        return out

class Upsampling(nn.Module):
    def __init__(self, H, W, h,w,c):
        super().__init__()
        self.H = H
        self.W = W

        self.h = h
        self.w = w
        self.c = c

        self.deconv1 = UpsampleConvLayer(c, 64, kernel_size=3, stride=1, upsample=2)
        self.in4 = torch.nn.InstanceNorm2d(64, affine=True)
        self.deconv2 = UpsampleConvLayer(64, 32, kernel_size=3, stride=1, upsample=2)
        self.in5 = torch.nn.InstanceNorm2d(32, affine=True)

    def forward(self, x):
        x = self.deconv1(x)
        x = self.in4(x)
        x = self.deconv2(x)
        x = self.in5(x)
        return x



class CellNet(nn.Module):

    def __init__(self, H, W, C, action_num):
        super().__init__()
        self.H = H
        self.W = W
        self.C = C
        self.action_num = action_num

        # 60 x 212
        # 30 x 106
        # 15 x 53 =

        self.W1 = self.H * self.W / 4 / 4


        self.relu = nn.LeakyReLU()
        self.conv1 = conv3x3(self.C, 8) # use 8 channel
        self.conv2 = conv3x3(self.C, 32) # use 8 channel
        self.pool = nn.MaxPool2d(2, stride=2)
        self.res1 = ResBlock(32)
        self.res2 = ResBlock(64)
        self.fully = nn.Linear(self.W1, self.action_num)

        self.upsample = Upsampling(H,W)

    def forward(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x)
        # TODO need to check x.shape

        x2 = self.res1(x)
        x2 = self.pool(x2)

        # TODO need to check x2.shape
        x3 = self.res2(x2)

        x3 = x3.reshape( x3.shape[0] ,-1) # flat other dimension, only preserve batch
        x4 = self.fully(x3)


        return x4,


class MyNet(nn.Module):
    """
    Cell block:
    first image has shape X0
    several conv layer first,

    shrink shape un change to layer X
    X0 --> X --- fully connect --> Y
    X --- up sampling --> X0

    Y ---> shrink to action space size  A

    predict A and X0
    train X0 if it is a move, else no back prop


    LSTM part:
    A and X0
    |           |
    + ----------+
    |           |
    + ----------+

    """

    def __init__(self, H, W, C, action_num):
        super().__init__()
        self.net = CellNet(H, W, C, action_num)
        # TODO LSTM

    def forward(self,x):
        return self.net(x)


def one_hot_encode_img(imgs:np.ndarray):
    """
    one hot encoding ascii
    :param imgs: of shape (Batch, Seq_time, H, W, 8)
    :return:    shape (Batch, Seq_time, H, W, embedding_size * 2 + 6)
    """
    N,T,H,W,_ = imgs.shape
    idx1 = imgs[:, :, :, :, 0]
    idx2 = imgs[:, :, :, :, 1]
    # TODO make sure idx1 is uint type
    zeros1 = np.zeros( (N,T,H,W, 256) )
    zeros2 = np.zeros((N, T, H, W, 256))
    # for n in range(N):
    #     for t in range(T):
    #         for h in range(H):
    #             for w in range(W):
    #                 x = idx1[ n,t,h,w ]
    #                 zeros1[n,t,h,w,x] = 1
    #                 x = idx2[ n,t,h,w ]
    #                 zeros2[n,t,h,w,x] = 1

    n,t,h,w = np.ogrid[:N, :T, :H, :W]
    zeros1[n,t,h,w,idx1] = 1
    zeros2[n, t, h, w, idx2] = 1

    #zeros1[ tuple(idx1) ] = 1
    #zeros1[ np.arange(N), np.arange(T), np.arange(H), np.arange(W), idx1] = 1
    #zeros2[ np.arange(N), np.arange(T), np.arange(H), np.arange(W), idx2] = 1
    result = np.concatenate([ zeros1, zeros2, imgs[:, :, :, :, 2:] ], axis=-1) # concat last dimension
    return result


def work():

    action_space = ActionSpaces(font_size = 12)
    transforms = GameRecordTransformer(action_space)
    ds = GameRecordDataset("capture", log_partial_length=500, time_seq_length=5, transformer=transforms)
    loader = DataLoader(ds, batch_size=3, shuffle=False)
    for batch_ndx, sample in enumerate(loader):
        imgs, (e, e_pos) = sample
        imgs = one_hot_encode_img(imgs)

        # make N,T,H,W C ---> NCHW
        imgs = imgs[:,0]
        imgs = imgs.transpose( [0,3,1,2] )
        print(imgs.shape)
        break


    #mynet = MyNet()
    #mynet()

work()
