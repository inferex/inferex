import tensorflow as tf
import os


WEIGHTS_PATH = "./tf_weights/weights"


def create_model():

    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(10)
    ])

    return model


def load_model():
    model = create_model()
    if os.path.exists(WEIGHTS_PATH):
        model.load_weights(WEIGHTS_PATH)
    return model


def train():
    mnist = tf.keras.datasets.mnist

    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0

    model = load_model()

    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    model.compile(optimizer='adam',
                  loss=loss_fn,
                  metrics=['accuracy'])

    model.fit(x_train, y_train, epochs=3)

    model.save_weights(WEIGHTS_PATH)

    model.evaluate(x_test,  y_test, verbose=2)


if __name__ == '__main__':
    train()
