from code.base_class.method import method
from code.stage_2_code.Evaluate_Accuracy import Evaluate_Accuracy
import torch
from torch import nn
import numpy as np
import os
import matplotlib.pyplot as plt


class Method_MLP(method, nn.Module):
    data = None
    # it defines the max rounds to train the model
    max_epoch = 1400
    # it defines the learning rate for gradient descent based optimizer for model learning
    learning_rate = 1e-3

    # it defines the the MLP model architecture, e.g.,
    # how many layers, size of variables in each layer, activation function, etc.
    # the size of the input/output portal of the model architecture should be consistent with our data input and desired output
    def __init__(self, mName, mDescription):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        method.__init__(self, mName, mDescription)
        nn.Module.__init__(self)
        # check here for nn.Linear doc: https://pytorch.org/docs/stable/generated/torch.nn.Linear.html
        self.fc1 = nn.Linear(784, 512)
        # check here for nn.ReLU doc: https://pytorch.org/docs/stable/generated/torch.nn.ReLU.html
        self.activation_func_1 = nn.ReLU()
        self.fc2 = nn.Linear(512, 64)
        self.activation_func_2 = nn.ReLU()
        self.fc3 = nn.Linear(64, 32)
        self.activation_func_3 = nn.ReLU()
        self.fc4 = nn.Linear(32, 10)
        # check here for nn.Softmax doc: https://pytorch.org/docs/stable/generated/torch.nn.Softmax.html
        self.activation_func_4 = nn.Softmax(dim=1)

    # it defines the forward propagation function for input x
    # this function will calculate the output layer by layer

    def forward(self, x):
        '''Forward propagation'''
        # hidden layer embeddings
        h1 = self.activation_func_1(self.fc1(x))
        h2 = self.activation_func_2(self.fc2(h1))
        h3 = self.activation_func_3(self.fc3(h2))
        # output layer result
        # self.fc_layer_2(h) will be a nx2 tensor
        # n (denotes the input instance number): 0th dimension; 2 (denotes the class number): 1st dimension
        # we do softmax along dim=1 to get the normalized classification probability distributions for each instance
        y_pred = self.activation_func_4(self.fc4(h3))
        return y_pred

    # backward error propagation will be implemented by pytorch automatically
    # so we don't need to define the error backpropagation function here

    def train(self, X, y):
        self.to(self.device)
        # check here for the torch.optim doc: https://pytorch.org/docs/stable/optim.html
        optimizer = torch.optim.AdamW(self.parameters(), lr=self.learning_rate)
        # check here for the nn.CrossEntropyLoss doc: https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html
        loss_function = nn.CrossEntropyLoss()
        # for training accuracy investigation purpose
        accuracy_evaluator = Evaluate_Accuracy('training accuracy evaluator', 'Evaluate accuracy for model on training data')

        epochs = []
        accuracies = []
        losses = []

        # it will be an iterative gradient updating process
        # we don't do mini-batch, we use the whole input as one batch
        # you can try to split X and y into smaller-sized batches by yourself
        # get the output, we need to covert X into torch.tensor so pytorch algorithm can operate on it
        X_tensor = torch.FloatTensor(np.array(X)).to(self.device)
        # convert y to torch.tensor as well
        y_tensor = torch.LongTensor(np.array(y)).to(self.device)
        # y_one_hot = torch.nn.functional.one_hot(y_tensor, num_classes=10).float()
        for epoch in range(self.max_epoch): # you can do an early stop if self.max_epoch is too much...
            y_pred = self.forward(X_tensor)
            # calculate the training loss
            train_loss = loss_function(y_pred, y_tensor)
            # train_loss = loss_function(y_pred, y_one_hot)
            # check here for the gradient init doc: https://pytorch.org/docs/stable/generated/torch.optim.Optimizer.zero_grad.html
            optimizer.zero_grad()
            # check here for the loss.backward doc: https://pytorch.org/docs/stable/generated/torch.Tensor.backward.html
            # do the error backpropagation to calculate the gradients
            train_loss.backward()
            # check here for the opti.step doc: https://pytorch.org/docs/stable/optim.html
            # update the variables according to the optimizer and the gradients calculated by the above loss.backward function
            optimizer.step()

            accuracy_evaluator.data = {'true_y': y_tensor.detach().cpu().numpy(), 'pred_y': y_pred.max(1)[1].detach().cpu().numpy()}
            accuracy = accuracy_evaluator.evaluate()
            epochs.append(epoch)
            accuracies.append(accuracy)
            losses.append(train_loss.item())
            if epoch % 50 == 0:
                print('Epoch:', epoch, 'Accuracy:', accuracy, 'Loss:', train_loss.item())

        # training accuracy plot
        plt.figure()
        plt.plot(epochs, accuracies)
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.title('Training Accuracy')
        plt.grid(True)

        save_dir = '../../result/stage_2_result'
        os.makedirs(save_dir, exist_ok=True)

        plot_path = os.path.join(save_dir, 'training_accuracy_plot.png')
        plt.savefig(plot_path)

        plt.close()

        # training loss plot
        plt.figure()
        plt.plot(epochs, losses)
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training Loss')
        plt.grid(True)

        plot_path = os.path.join(save_dir, 'training_loss_plot.png')
        plt.savefig(plot_path)

        plt.close()

    
    def test(self, X):
        # do the testing, and result the result
        y_pred = self.forward(torch.FloatTensor(np.array(X)).to(self.device))
        # convert the probability distributions to the corresponding labels
        # instances will get the labels corresponding to the largest probability
        return y_pred.max(1)[1]

    
    def run(self):
        print('method running...')
        print('--start training...')
        self.train(self.data['train']['X'], self.data['train']['y'])
        print('--start testing...')
        pred_y = self.test(self.data['test']['X'])
        return {'pred_y': pred_y.detach().cpu().numpy(), 'true_y': self.data['test']['y']}
            