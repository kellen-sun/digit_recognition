import numpy as np
from nn import MLP
from engine import Value
import pickle

# Load the .npz file
mnist_data = np.load('mnist.npz')
# 60,000 training data points
# 10,000 testing data
# each [x] is a 28x28 array in grayscale
# each [y] is the corresponding number
print("Data loaded...")
def vis(data):
    # given the matrix format data of a mnist image print it out
    for i in data:
        for j in i:
            if j>0:
                print("% ", end="")
            else:
                print("  ", end="")
        print("")

# setup training and testing data
train_img = mnist_data["x_train"]
train_lab = mnist_data["y_train"]
test_img = mnist_data["x_test"]
test_lab = mnist_data["y_test"]
train_x = []
train_y = []
for i in range(len(train_img)):
    train_x.append([item for sublist in train_img[i] for item in sublist])
    train_y.append([Value(1) if j==train_lab[i] else Value(-1) for j in range(10)])
test_x = []
test_y = []
for i in range(len(test_img)):
    test_x.append([item for sublist in test_img[i] for item in sublist])
    test_y.append([Value(1) if j==test_lab[i] else Value(-1) for j in range(10)])
print("Data setup...")

n = MLP(784, [10, 10])
print("MLP created...")
# print("number of parameters", len(n.parameters()))

# calculating loss
def findloss(predvals, train_y):
    err = 0
    s = len(predvals)
    for i, j in zip(predvals, train_y):
        #sm = sum([scorei.exp() for scorei in i])
        #err += sum([(yi - scorei.exp()/sm)**2 for yi, scorei in zip(j, i)])
        err += sum([(yi - scorei)**2
                     for yi, scorei in zip(j, i)])
        # still a value type
    acc = [max(range(10), key=lambda k: i[k].data) == max(range(10), key=lambda k: j[k].data) for i,j in zip(predvals, train_y)]
    return err * (1.0 / s), sum(acc)/s

#training process:
def train():
    learningrate = 0.5
    numofpasses = 5
    batchsize = 8
    counter = 0
    for batch in range(100):
        print("Training batch", batch+1, "of 100...")
        for i in range(numofpasses):
            # forward pass
            predvals = list(map(n, train_x[counter:counter+batchsize]))
            loss, acc = findloss(predvals, train_y[counter:counter+batchsize])
            # backwards pass
            for p in n.parameters():
                p.grad = 0.0
            loss.backwards()
            print("    Loss:", loss.data, "Acc:", acc)
            print("    Training", i+1, "of", numofpasses, "...")
            # update
            learningrate = 0.5 - 0.45 * (batch+i)/(100+numofpasses)
            for p in n.parameters():
                p.data -= learningrate * p.grad
            
        counter+=batchsize
        if batch%5 == 0:
            # checks accuracy
            test_pred = [max(range(len(i)), key=lambda j: i[j].data) for i in
                        map(n, test_x[:100])]
            # returns highest activated neuron in output layer ie: which digit
            # test predictions, of first 30

            # check accuracy on test data
            suc = 0
            for i in range(100):
                if test_pred[i] == test_lab[i]:
                    suc+=1
            print("Accuracy on test data:", suc/100.0)

    # write weights to a file
    with open('weights.pkl', 'wb') as file:
        pickle.dump([i.data for i in n.parameters()], file)

train()
# print("Label:", [i.data for i in train_y[12]])
# pred = n(train_x[12])
# print("Prediction:     ", [round(i.data,4) for i in pred])
# loss, acc = findloss([pred], [train_y[12]])
# print(loss.data, acc)
# for p in n.parameters():
#     p.grad = 0.0
# loss.backwards()
# learningrate = 1
# for p in n.parameters():
#     p.data -= learningrate * p.grad
# newpred = n(train_x[12])
# print("New Prediction1:", [round(i.data, 4) for i in newpred])
# loss, acc = findloss([newpred], [train_y[12]])
# print(loss.data, acc)
# for p in n.parameters():
#     p.grad = 0.0
# loss.backwards()
# for p in n.parameters():
#     p.data -= learningrate * p.grad
# newpred = n(train_x[12])
# print("New Prediction2:", [round(i.data, 4) for i in newpred])
# loss, acc = findloss([newpred], [train_y[12]])
# print(loss.data, acc)
# for p in n.parameters():
#     p.grad = 0.0
# loss.backwards()
# for p in n.parameters():
#     p.data -= learningrate * p.grad
# newpred = n(train_x[12])
# print("New Prediction3:", [round(i.data, 4) for i in newpred])
