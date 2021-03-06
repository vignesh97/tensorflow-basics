import tensorflow as tf
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Load training data set from CSV file
training_data_df = pd.read_csv("sales_data_training.csv", dtype=float)

# Pull out columns for X (data to train with) and Y (value to predict)
X_training = training_data_df.drop('total_earnings', axis=1).values
Y_training = training_data_df[['total_earnings']].values

# Load testing data set from CSV file
test_data_df = pd.read_csv("sales_data_test.csv", dtype=float)

# Pull out columns for X (data to train with) and Y (value to predict)
X_testing = test_data_df.drop('total_earnings', axis=1).values
Y_testing = test_data_df[['total_earnings']].values

# All data needs to be scaled to a small range like 0 to 1 for the neural
# network to work well. Create scalers for the inputs and outputs.
X_scaler = MinMaxScaler(feature_range=(0, 1))
Y_scaler = MinMaxScaler(feature_range=(0, 1))

# Scale both the training inputs and outputs
X_scaled_training = X_scaler.fit_transform(X_training)
Y_scaled_training = Y_scaler.fit_transform(Y_training)

# It's very important that the training and test data are scaled with the same scaler.
X_scaled_testing = X_scaler.transform(X_testing)
Y_scaled_testing = Y_scaler.transform(Y_testing)

# Define model parameters
learning_rate = 0.001
training_epochs = 100
display_step = 5

RUN_NAME = "run 1 with 20 nodes"

# Define how many inputs and outputs are in our neural network
number_of_inputs = 9
number_of_outputs = 1

# Define how many neurons we want in each layer of our neural network
layer_1_nodes = 20
layer_2_nodes = 100
layer_3_nodes = 50

# Section One: Define the layers of the neural network itself

# Input Layer
with tf.variable_scope('input'):
    X = tf.placeholder(tf.float32,shape=(None, number_of_inputs))

# Layer 1
with tf.variable_scope('layer_1'):
    weights = tf.get_variable(name="weights1", shape=[number_of_inputs, layer_1_nodes],
                              initializer=tf.contrib.layers.xavier_initializer())
    biases = tf.get_variable(name="biases1", shape=[layer_1_nodes], initializer=tf.zeros_initializer)
    layer_1_output = tf.nn.relu(tf.matmul(X, weights)+ biases)

# Layer 2
with tf.variable_scope('layer_2'):
    weights = tf.get_variable(name="weights2", shape=[layer_1_nodes, layer_2_nodes],
                              initializer=tf.contrib.layers.xavier_initializer())
    biases = tf.get_variable(name="biases2", shape=[layer_2_nodes], initializer=tf.zeros_initializer)
    layer_2_output = tf.nn.relu(tf.matmul(layer_1_output, weights) + biases)

# Layer 3
with tf.variable_scope('layer_3'):
    weights = tf.get_variable(name="weights3", shape=[layer_2_nodes, layer_3_nodes],
                              initializer=tf.contrib.layers.xavier_initializer())
    biases = tf.get_variable(name="biases3", shape=[layer_3_nodes], initializer=tf.zeros_initializer)
    layer_3_output = tf.nn.relu(tf.matmul(layer_2_output, weights) + biases)

# Output Layer
with tf.variable_scope('output'):
    weights = tf.get_variable(name="weights4", shape=[layer_3_nodes, number_of_outputs],
                              initializer=tf.contrib.layers.xavier_initializer())
    biases = tf.get_variable(name="biases4", shape=[number_of_outputs], initializer=tf.zeros_initializer)
    prediction = tf.nn.relu(tf.matmul(layer_3_output, weights) + biases)



# Section Two: Define the cost function of the neural network that will measure prediction accuracy during training

with tf.variable_scope('cost'):
    Y = tf.placeholder(tf.float32, shape=(None , 1))
    cost = tf.reduce_mean(tf.squared_difference(prediction , Y))


# Section Three: Define the optimizer function that will be run to optimize the neural network

with tf.variable_scope('train'):
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)

with tf.variable_scope('logging'):
    tf.summary.scalar('current_cost', cost)
    tf.summary.histogram('prediction', prediction)
    summary = tf.summary.merge_all()

saver = tf.train.Saver()

with tf.Session() as session:
    session.run(tf.global_variables_initializer())

    training_writer = tf.summary.FileWriter("C:/Projects/tensorboard/{}/training".format(RUN_NAME), session.graph)
    testing_writer = tf.summary.FileWriter("C:/Projects/tensorboard/{}/testing".format(RUN_NAME), session.graph)

    #saver.restore(session, "C:/Projects/tensorboard/models/trained_models.ckpt")


    for epoch in range(training_epochs):
        session.run(optimizer, feed_dict={X: X_scaled_training, Y: Y_scaled_training})
        if epoch % 5 == 0:
            training_cost, training_summary = session.run([cost, summary], feed_dict={X: X_scaled_training,
                                                                                      Y: Y_scaled_training})
            testing_cost, testing_summary = session.run([cost, summary], feed_dict={X: X_scaled_testing,
                                                                                    Y: Y_scaled_testing})

            training_writer.add_summary(training_summary, epoch)
            testing_writer.add_summary(testing_summary, epoch)

            print(epoch, training_cost, testing_cost)
        #print("Training pass: {}".format(epoch))
    print("Training is complete")
    training_cost, training_summary = session.run([cost, summary], feed_dict={X: X_scaled_training, Y: Y_scaled_training})
    testing_cost, testing_summary = session.run([cost, summary], feed_dict={X: X_scaled_testing, Y: Y_scaled_testing})

    final_training_cost = session.run(cost, feed_dict={X: X_scaled_training, Y: Y_scaled_training})
    final_testing_cost = session.run(cost, feed_dict={X: X_scaled_testing, Y: Y_scaled_testing})
    print("Final Training cost: {}".format(final_training_cost))
    print("Final Testing cost: {}".format(final_testing_cost))

    Y_predicted_scaled = session.run(prediction, feed_dict={X: X_scaled_testing})

    Y_predicted = Y_scaler.inverse_transform(Y_predicted_scaled)

    real_earnings = test_data_df['total_earnings'].values[0]
    predicted_earnings = Y_predicted[0][0]

    print("The actual earnings of Game #1 were ${}".format(real_earnings))
    print("Our neural network predicted earnings of ${}".format(predicted_earnings))

    #save_path = saver.save(session, "C:/Projects/tensorboard/models/trained_models.ckpt")
    #print("Model saved : {}".format(final_testing_cost))

    # tensorboard --logdir="C:\tensorboard\"

    model_builder = tf.saved_model.builder.SavedModelBuilder("exported_model")

    inputs = {
        'input': tf.saved_model.utils.build_tensor_info(X)
    }

    outputs = {
        'earnings': tf.saved_model.utils.build_tensor_info(prediction)
    }

    signature_def = tf.saved_model.signature_def_utils.build_signature_def(
        inputs=inputs,
        outputs=outputs,
        method_name=tf.saved_model.signature_constants.PREDICT_METHOD_NAME
    )

    model_builder.add_meta_graph_and_variables(
        session,
        tags=[tf.saved_model.tag_constants.SERVING],
        signature_def_map={
            tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY:signature_def
        }
    )

    model_builder.save()

    #Google cloud commands
    #gsutil mb -l us-central1 gs://tensorflow-class-1000
    #gsutil cp -R exported_model/* gs://tensorflow-class-1000/earnings_v1/
    #gcloud ml-engine models create earnings --regions us-central1
    #gcloud ml-engine versions create v1 --model=earnings --origin=gs://tensorflow-class-1000/earnings_v1/
    #gcloud ml-engine predict --model=earnings --json-instances=sample_input_prescaled.json










