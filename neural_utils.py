import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
from functools import lru_cache
from spaces import ActionSpaces
import pickle
from controls.Events import *
from image_to_ascii import UnionASCIIConverter

class GameRecordTransformer:

    def __init__(self, action_space:ActionSpaces):
        self.action_space = action_space
        self.ascii_converter = UnionASCIIConverter(12)
        # fixed for now
        self.W = 212
        self.H = 60

    def transform_img(self, imgs:np.ndarray): # img batched
        result = self.ascii_converter.convertAllBatched(imgs)
        self.N, self.H, self.W, self.C = imgs.shape
        # result has shape (N,H,W,8) # 8 is  [ascii, ascii big, rgb (3) , rgb (3) ]
        return result

    def flat_xy(self, xy):
        x,y = xy
        x /= self.action_space.ww
        y /= self.action_space.hh
        return self.W * y + x

    def convert_event(self, event):
        """

        :param event:
        :return: two value, ( event, mouse_position x,y )
        """

        if type(event) is MoveEvent:
            xy = event.xy()
            return self.action_space.abstract_move_idx, self.flat_xy(xy)
        else :
            if type(event) is ButtonEvent and event.event_type == 'double':
                event.event_type = 'down'
            event_idx = self.action_space.action2idx[str(event)]
            return event_idx, -1 # use -1 to indicate no mouse coordinate

    def transform_event(self, event:list): # event a list
        temp = np.array([self.convert_event(i) for i in event])
        return temp[:, 0], temp[:, 1]

class GameRecordDataset(Dataset):
    """Face Landmarks dataset."""

    def __init__(self, file_name:str, log_partial_length:int, time_seq_length:int, transformer:GameRecordTransformer=None):
        """

        :param file_name: file name start like "{capture}_events_0.npz"
        :param log_partial_length: the length of each log files, except the last one
        :param time_seq_length: each sample is consisted with several consecutive frames,
        :param transform:
        """
        self.file_name = file_name
        self.log_partial_length = log_partial_length
        self.time_seq_length = time_seq_length
        self.files = [] # (image npz file, action pickle file )
        for i in os.listdir("."):
            if i.endswith(".pickle") and i.startswith(self.file_name):
                name1 = i
                i2 = i[len(self.file_name + "_events" ):- len(".pickle")]
                i2 = f"{self.file_name}_imgs{i2}.npz"
                fs = (i2, i)
                print(fs)
                self.files += [fs]

        assert len(self.files) > 0

        self.n = len(self.files)
        self.n = log_partial_length * (self.n - 1)
        with open(name1, "rb") as f:
            events = pickle.load(f)
            self.n += len(events)

        self.transformer = transformer

        # need to minus sequence,
        self.n = self.n - time_seq_length + 1

    @lru_cache(maxsize=5)
    def get_file(self, i):
        path_capture = f"{self.file_name}_XXX_{i}"
        temp_path_capture = path_capture.replace("XXX", "imgs")

        if os.path.exists(f"{temp_path_capture}.ascii.npz") \
            and self.transformer is not None:
            with open(f"{temp_path_capture}.ascii.npz", "rb") as f:
                f2 = np.load(f)
                imgs = f2["arr_0"]
        else:
            with open(f"{temp_path_capture}.npz", "rb") as f:
                f2 = np.load(f)
                imgs = f2["arr_0"]
                if self.transformer is not None:
                    i = 0
                    temp = []
                    while i*50 < imgs.shape[0]:
                        partial = self.transformer.transform_img(imgs[i * 50: (i+1) * 50 ])
                        print( partial.shape )
                        temp += [partial]
                        i += 1
                    temp = np.concatenate(temp)
                    imgs = temp
                    # cache images
                    print(f"ascii save shape {imgs.shape} to file {temp_path_capture}.ascii.npz")
                    np.savez_compressed(f"{temp_path_capture}.ascii.npz", temp)



        temp_path_capture = path_capture.replace("XXX", "events")
        with open(f"{temp_path_capture}.pickle", "rb") as f:
            events = pickle.load(f)
            if self.transformer is not None:
                events = self.transformer.transform_event(events)
        return imgs, events

    def get_ith_seq(self, i):
        # not correct work around
        file_ith = i // self.log_partial_length
        infile_ith = i % self.log_partial_length

        if infile_ith + self.time_seq_length >= self.log_partial_length:
            print("change ith ",i ,i - self.time_seq_length)
            infile_ith -= self.time_seq_length

        imgs, events = self.get_file(file_ith)
        gather_imgs = imgs[ infile_ith: infile_ith + self.time_seq_length ]
        gather_events = events[0][infile_ith: infile_ith + self.time_seq_length]
        gather_events_pos = events[1][infile_ith: infile_ith + self.time_seq_length]
        return gather_imgs, (gather_events, gather_events_pos)

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        sample = self.get_ith_seq(idx)
        return sample


def work():
    action_space = ActionSpaces(font_size = 12)
    transforms = GameRecordTransformer(action_space)
    ds = GameRecordDataset("capture", log_partial_length=500, time_seq_length=5, transformer=transforms)
    #imgs,(e,e_pos) = ds[497]
    imgs, (e, e_pos) = ds[520]
    print(imgs.shape)
    print(e.shape, e_pos.shape)
    print(e)
    print(e_pos)
    loader = DataLoader(ds, batch_size=3, shuffle=False)
    for batch_ndx, sample in enumerate(loader):
        imgs, (e, e_pos) = sample
        print(batch_ndx*3, imgs.shape, e.shape, e_pos.shape)

#work()
