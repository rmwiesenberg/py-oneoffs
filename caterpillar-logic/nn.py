import argparse
import json
import logging
import os
import random
import time
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader

from common import DATA_DIR, Caterpillar, Color, TestScreen

EPOCHS = 50
BATCH_SIZE = 16
LEARN_RATE = 0.005


class Dataset(torch.utils.data.Dataset):
    def __init__(self, data: List[Tuple[tuple, bool]]):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index: int):
        row = self.data[index]
        return np.array(row[0]), float(row[1])


class NN(nn.Module):
    def __init__(self):
        super(NN, self).__init__()

        self.layer_1 = nn.Linear(7, 32)
        self.layer_2 = nn.Linear(32, 32)
        self.layer_3 = nn.Linear(32, 64)
        self.layer_4 = nn.Linear(64, 16)
        self.layer_out = nn.Linear(16, 1)

        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(p=0.1)

    def forward(self, inputs):
        x = self.relu(self.layer_1(inputs))
        x = self.relu(self.layer_2(x))
        x = self.dropout(x)
        x = self.relu(self.layer_3(x))
        x = self.relu(self.layer_4(x))
        # x = self.dropout(x)
        x = self.layer_out(x)

        return x


def pred(y):
    return torch.round(torch.sigmoid(y))


def binary_acc(y_pred, y_test):
    y_pred_tag = pred(y_pred)

    correct_results_sum = (y_pred_tag == y_test).sum().float()
    acc = correct_results_sum / y_test.shape[0]
    acc = torch.round(acc * 100)

    return acc


def train(*, name: str, validation: float = 0.1):
    data_file = os.path.join(DATA_DIR, f'{name}.json')
    with open(data_file, 'r') as f:
        data = json.load(f)

    train_data = []
    valid_data = []
    for idx, d in enumerate(data):
        cat_info, value = d
        caterpillar = Caterpillar(tuple([Color(c) for c in cat_info]))
        if random.random() < validation:
            valid_data.append(d)
            if len(caterpillar) <= 2:
                train_data.append(d)
        else:
            train_data.append(d)

    training_data = Dataset(train_data)
    train_loader = DataLoader(dataset=training_data, batch_size=BATCH_SIZE, shuffle=True)
    validation_data = Dataset(valid_data)
    valid_loader = DataLoader(dataset=validation_data, batch_size=BATCH_SIZE, shuffle=True)

    logging.info(f'Using {len(training_data)} sets for training and {len(validation_data)} for validation.')

    net = NN()
    print(net)

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda:0" if use_cuda else "cpu")
    net.to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = Adam(net.parameters(), lr=LEARN_RATE)

    losses = []
    accuracies = []
    for epoch in range(EPOCHS):
        epoch_loss = 0
        epoch_acc = 0
        for x_train, y_train in train_loader:
            x_train, y_train = x_train.to(device), y_train.to(device)
            optimizer.zero_grad()

            y_pred = net(x_train.float())

            loss = criterion(y_pred, y_train.unsqueeze(1))
            acc = binary_acc(y_pred, y_train.unsqueeze(1))

            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            epoch_acc += acc.item()

        losses.append(epoch_loss / len(train_loader))
        accuracies.append(epoch_acc / len(train_loader))

        print(f'Epoch {epoch + 0:03}: '
              f'| Loss: {losses[-1]:.5f} '
              f'| Acc: {accuracies[-1]:.3f}')

    final_acc = 0
    with torch.set_grad_enabled(False):
        for x_valid, y_valid in valid_loader:
            x_valid, y_valid = x_valid.to(device), y_valid.to(device)
            y_pred = net(x_valid.float())
            acc = binary_acc(y_pred, y_valid.unsqueeze(1))
            final_acc += acc.item()
        print(f'Validation Acc: {final_acc / len(valid_loader):.3f}')
    torch.save(net.state_dict(), os.path.join(DATA_DIR, f'{name}.torch'))

    fig, (ax1, ax2) = plt.subplots(2, 1)
    fig.set_size_inches(16, 9)
    ax1.plot(losses)
    ax1.set_title('Losses')
    ax2.plot(accuracies)
    ax2.set_title('Accuracies')
    fig.savefig(os.path.join(DATA_DIR, f'{name}.png'))

    plt.show()


def test(*, name: str):
    net = NN()
    net.load_state_dict(torch.load(os.path.join(DATA_DIR, f'{name}.torch')))

    test_screen = TestScreen()
    test_screen.init()

    with torch.set_grad_enabled(False):
        while 1:
            val = input('Press enter to read the caterpillar. (q to quit)').lower()
            if val == 'q':
                break
            caterpillar = test_screen.test_caterpillar()
            res = net(torch.from_numpy(np.array(caterpillar.json())).float())
            bool_res = bool(pred(res))
            if bool_res:
                print(f'{caterpillar} is Valid')
                # test_screen.valid.click()
            else:
                print(f'{caterpillar} is Invalid')
                # test_screen.invalid.click()
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['train', 'test'])
    parser.add_argument('--name', required=True)
    args = parser.parse_args()

    if args.mode == 'train':
        train(name=args.name)
    else:
        test(name=args.name)


if __name__ == '__main__':
    main()
