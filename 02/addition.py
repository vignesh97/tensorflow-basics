import os
import tensorflow as tf

# Turn off TensorFlow warning messages in program output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Define computational graph
X = tf.placeholder(tf.float32, name="X")
Y = tf.placeholder(tf.float32, name= "Y")

addition = tf.add(x)


# Create the session
with tf.Session() as session:

    result =

    print(result)
