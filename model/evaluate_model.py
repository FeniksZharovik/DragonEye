import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Load model
model = tf.keras.models.load_model("model.h5")

# Dataset test
datagen = ImageDataGenerator(rescale=1./255)
test_data = datagen.flow_from_directory(
    "../dataset/",
    target_size=(128, 128),
    batch_size=32,
    class_mode='categorical',
    shuffle=False
)

# Prediksi
y_pred = model.predict(test_data)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = test_data.classes

print(classification_report(y_true, y_pred_classes))
print(confusion_matrix(y_true, y_pred_classes))
