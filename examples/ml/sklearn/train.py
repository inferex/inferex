import joblib
from sklearn import datasets, svm
from sklearn.model_selection import train_test_split

def train():
    digits = datasets.load_digits()

    # flatten the images
    n_samples = len(digits.images)
    data = digits.images.reshape((n_samples, -1))

    # Create a classifier: a support vector classifier
    clf = svm.SVC(gamma=0.001)

    # Split data into 50% train and 50% test subsets
    X_train, X_test, y_train, y_test = train_test_split(
        data, digits.target, test_size=0.5, shuffle=False
    )

    # Learn the digits on the train subset
    clf.fit(X_train, y_train)

    joblib.dump(clf, 'clf.joblib')


if __name__ == '__main__':
    train()
