import random

# triangular() draws test and training indices from a triangular
# distribution.  The test samples are biased toward samples occuring
# later in the dataset (more recent if the data is a time series).
# The training is bootstrapped (samples may occur more than once).
# The test set consists of all samples not used in the training
# sample.  Since the training data is biased toward later samples, the
# "test" set will be biased in the other direction.  If the intent of
# the training data is to introduce bias toward more recent activity,
# the test set probably isn't very useful.  Nonetheless, it's returned
# for compatibility with sklearn's cross_validation samplers.

def triangular(n, iterations, train_size=1.0):
    train_points = int(n * train_size)
    for i in range(iterations):
        train_index = train_points * [0]
        used = n * [False]
        for s in range(train_points):
            next_sample = max(random.randrange(0,n),random.randrange(0,n))
            train_index[s] = next_sample
            used[next_sample] = True

        test_index=[]
        for t in range(n):
            if not used[t]:
                test_index.append(t)
        yield train_index,test_index
