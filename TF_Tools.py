import tensorflow as tf
import matplotlib.pyplot as plt

# Global variables (simple approach)
train_ds = None
val_ds = None
model = None
history = None
num_classes = 6  # <-- set this to your actual number of classes


def Training_Module():
    global train_ds, val_ds

    data_path = r"C:\Users\hep\Desktop\Wirebond_Inspector\YOLO_Datasets\Dataset 2\TF_Converted"
    #NEED TO CHANGE FOR EACH NEW DATASET AND MODEL

    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_path,
        validation_split=0.2,
        subset="training",
        seed=42,
        image_size=(224, 224),
        batch_size=32
    )

    val_ds = tf.keras.preprocessing.image_dataset_from_directory(
        data_path,
        validation_split=0.2,
        subset="validation",
        seed=42,
        image_size=(224, 224),
        batch_size=32
    )

    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)



def Build_Model():
    data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.05),
    tf.keras.layers.RandomContrast(0.1),
    ])

    global model, num_classes

    base = tf.keras.applications.EfficientNetB0(
        include_top=False,
        input_shape=(224, 224, 3),
        weights="imagenet"
    )
    base.trainable = True

    # Optional: freeze first 200 layers to avoid catastrophic forgetting
    for layer in base.layers[:200]:
        layer.trainable = False


    model = tf.keras.Sequential([
        data_augmentation,
        base,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(num_classes, activation="softmax")
    ])
    


def Model_Compiler():
    global model
    lr_schedule = tf.keras.optimizers.schedules.CosineDecay(
    initial_learning_rate=1e-3,
    decay_steps=1000
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=lr_schedule)

    model.compile(
        optimizer=optimizer,
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )


def train_model():
    global history, model, train_ds, val_ds

    class_weights = {
        0: 1.0,   # no_defect
        1: 1.5,   # debris (slightly boosted)
        2: 1.0,
        3: 1.0,
        4: 1.0,
        5: 1.0
    }

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=20,
        class_weight=class_weights
    )



def Model_Eval_and_Plot():
    global history
    plt.plot(history.history["accuracy"])
    plt.plot(history.history["val_accuracy"])
    plt.legend(["train", "val"])
    plt.show()


def Test_Predictions():
    global model
    img = tf.keras.preprocessing.image.load_img("test.jpg", target_size=(224, 224))
    img = tf.keras.preprocessing.image.img_to_array(img)
    img = tf.expand_dims(img, 0)

    pred = model.predict(img)
    print(pred)


# Example of running the pipeline:
# Training_Module()
# Build_Model()
# Model_Compiler()
# train_model()
# Model_Eval_and_Plot()


def Save_Model(savename):
    global model
    model.save(f"models/{savename}.keras")


def Load_Model(savename):
    global model
    model = tf.keras.models.load_model(f"models/{savename}.keras")
    return model



def Test_Loaded_Model(savename, img_path):
    global model

    loaded = tf.keras.models.load_model(f"models/{savename}")

    img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224, 224))
    img = tf.keras.preprocessing.image.img_to_array(img)
    img = tf.expand_dims(img, 0)

    pred = loaded.predict(img)
    print(pred)



# Example of running the pipeline:
# Training_Module()
# Build_Model()
# Model_Compiler()
# train_model()
# Model_Eval_and_Plot()

import os
import numpy as np
import tensorflow as tf

EXAMPLE_PHOTOS = r"C:\Users\hep\Desktop\Wirebond_Inspector\Example Photos"

def Test_Example_Photos(savename):
    global model

    # Load model
    model = tf.keras.models.load_model(f"models/{savename}.keras")

    # Load class names from classes.txt
    class_names = load_class_names()

    # Loop through images
    for filename in os.listdir(EXAMPLE_PHOTOS):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(EXAMPLE_PHOTOS, filename)

            img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224, 224))
            img = tf.keras.preprocessing.image.img_to_array(img)
            img = tf.expand_dims(img, 0)

            pred = model.predict(img)[0]
            class_id = np.argmax(pred)
            confidence = pred[class_id]

            readable_name = class_names[class_id]

            print(f"{filename} → {readable_name} ({confidence*100:.1f}%)")



import yaml


def load_class_names():
    classes_path = r"C:\Users\hep\Desktop\Wirebond_Inspector\YOLO_Datasets\Dataset 2\project-12-at-2026-04-27-14-36-55ad018e\classes.txt"
    with open(classes_path, "r") as f:
        names = [line.strip() for line in f.readlines() if line.strip()]
    return names

from sklearn.metrics import confusion_matrix
import numpy as np

def Confusion_Matrix():
    global model, val_ds

    y_true = []
    y_pred = []

    for images, labels in val_ds:
        preds = model.predict(images)
        preds = np.argmax(preds, axis=1)

        y_true.extend(labels.numpy())
        y_pred.extend(preds)

    print(confusion_matrix(y_true, y_pred))
