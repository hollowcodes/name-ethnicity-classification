""" file for small helper functions """

import string
from functools import partial
import numpy as np
import torch
import torch.utils.data
import torch.nn as nn
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence

import pickle
from termcolor import colored

from nameEthnicityDataset import NameEthnicityDataset

torch.manual_seed(0)

def custom_collate(batch):
    batch_size = len(batch)

    sample_batch, target_batch, sequence_lengths, non_padded_batch = [], [], [], []
    for sample, target, non_padded_sample in batch:
        sequence_lengths.append(sample.size(1))

        sample_batch.append(sample)
        target_batch.append(target)
        # non_padded_batch is the original batch, which is not getting padded so it can be converted back to string
        non_padded_batch.append(non_padded_sample)
        
    padded_batch = pad_sequence(sample_batch, batch_first=True)
    padded_to = list(padded_batch.size())[1]

    padded_batch = padded_batch.reshape(batch_size, padded_to, 28)        
    # packed_batch = pack_padded_sequence(padded_batch, sequence_lengths, batch_first=True, enforce_sorted=False)

    return padded_batch, torch.cat(target_batch, dim=0).reshape(batch_size, 1), non_padded_batch

def create_dataloader(dataset_path: str="", test_size: float=0.01, val_size: float=0.01, batch_size: int=32):
    """ create three dataloader (train, test, validation)

    :param str dataset_path: path to dataset
    :param float test_size/val_size: test-/validation-percentage of dataset
    :param int batch_size: batch-size
    :return torch.Dataloader: train-, test- and val-dataloader
    """

    dataset = NameEthnicityDataset(root_dir=dataset_path, class_amount=42)

    test_amount, val_amount = int(dataset.__len__() * test_size), int(dataset.__len__() * val_size)

    train_set, val_set, test_set = torch.utils.data.random_split(dataset, [
        (dataset.__len__() - (test_amount + val_amount)), 
        test_amount, 
        val_amount
    ])

    train_dataloader = torch.utils.data.DataLoader(
        train_set,
        batch_size=batch_size,
        num_workers=2,
        shuffle=True,
        collate_fn=custom_collate
    )
    val_dataloader = torch.utils.data.DataLoader(
        val_set,
        batch_size=int(batch_size),
        num_workers=1,
        shuffle=True,
        collate_fn=custom_collate

    )
    test_dataloader = torch.utils.data.DataLoader(
        test_set,
        batch_size=int(batch_size),
        num_workers=1,
        shuffle=True,
        collate_fn=custom_collate
    )

    return train_dataloader, val_dataloader, test_dataloader


def validate_accuracy(y_true, y_pred, threshold: float) -> float:
    """ calculate the accuracy of predictions
    
    :param torch.tensor y_true: targets
    :param torch.tensor y_pred: predictions
    :param float threshold: treshold for logit-rounding
    :return float: accuracy
    """

    correct_in_batch = 0
    for i in range(len(y_true)):
        output, target = y_pred[i], y_true[i]

        amount_classes = output.shape[0]

        target_empty = np.zeros((amount_classes))
        target_empty[target] = 1
        target = target_empty

        output = list(output).index(max(output))
        output_empty = np.zeros((amount_classes))
        output_empty[output] = 1
        output = output_empty

        # output = [1 if e >= threshold else 0 for e in output]

        if list(target) == list(output):
            correct_in_batch += 1
    
    return round((100 * correct_in_batch / len(y_true)), 5)


def show_progress(epochs: int, epoch: int, train_loss: float, train_accuracy: float, val_loss: float, val_accuracy: float):
    """ print training stats
    
    :param int epochs: amount of total epochs
    :param int epoch: current epoch
    :param float loss: train-loss
    :param float val_accuracy/val_loss: validation accuracy/loss
    :return None
    """

    epochs = colored(epoch, "cyan", attrs=["bold"]) + colored("/", "cyan", attrs=["bold"]) + colored(epochs, "cyan", attrs=["bold"])
    train_accuracy = colored(round(train_accuracy, 4), "cyan", attrs=["bold"]) + colored("%", "cyan", attrs=["bold"])
    train_loss = colored(round(train_loss, 6), "cyan", attrs=["bold"])
    val_accuracy = colored(round(val_accuracy, 4), "cyan", attrs=["bold"]) + colored("%", "cyan", attrs=["bold"])
    val_loss = colored(round(val_loss, 6), "cyan", attrs=["bold"])
    
    print("epoch {} train_loss: {} - train_acc: {} - val_loss: {} - val_acc: {}".format(epochs, train_loss, train_accuracy, val_loss, val_accuracy), "\n")


def onehot_to_char(one_hot_name: list=[]) -> str:
    """ convert one-hot encoded name back to string

    :param list one_hot_name: one-hot enc. name
    :return str: original string-type name
    """

    alphabet = string.ascii_lowercase.strip()

    name = ""
    for one_hot_char in one_hot_name:
        idx = list(one_hot_char).index(1) # [i for i, x in enumerate(one_hot_char) if x == 1][0]

        if idx == 26:
            name += " "
        elif idx == 27:
            name += "-"
        else:
            name += alphabet[idx]

    return name



"""with open("datasets/matrix_name_list.pickle",'rb') as o:
    data = pickle.load(o)

print(len(data))
print(len(data[0]))
print(len(data[0][1][0]))

print(onehot_to_char(data[2][1]))
"""