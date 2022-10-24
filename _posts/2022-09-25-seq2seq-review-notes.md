---
layout: post
title: "Seq2Seq Paper Review Notes"
date: 2022-09-25
---

## Sequence to Sequence Learning with Neural Networks
Ilya Sutskever, Oriol Vinyals, Quoc V. Le
Neural Information Processing Systems (NIPS 2014)

### Summary:
By the time when the paper was published, the DNN limits its application with fixed-length encoding vectors tasks, however, this work proposed an approach to handle sequence to sequence tasks whose lengths are not known a-priori. The method achieves such result by using two different multi-layer LSTMs as encoder and decoder. The encoder LSTM part will take the source language sentence as input and tries to learn a single hidden state to semantically best represent the meaning of the input sentence. The decoder network will take the last hidden state of the encoder and the previous timestep output as the input to predict the translation sentence in the target language. Notice that, the paper also firstly reported an important performance improvement trick as reverse the input words of the input sentence. This is reasonable since it could help the LSTM easier predict the first several words correctly which is crucial for beam search algorithm.

### Strength:
The paper claims three important improvements for overperforming the previous methods. 
First is using separated LSTMs for encoder and decoder rather than a straight end to end design. This indirect idea makes it possible to train multiple language pairs simultaneously since the tasks for encoder is decoupling from the decoder part. 

Second it stacks multiple LSTM layers rather than one by having multiple hidden states for a single timestep. The increase of the parameter numbers help the NN to have better fitting power. 

Third, it found out reversing of the input word sequence but keep the output sentence words order could lessen the LSTM burden to hold the long term meaning by minimizing the timestep between the front words of the source sentence and the front words of the target sentence. In the beam search setting, the correctness of the first several words is more important. This also becomes a good support for predicting the long sentences since LSTM usually suffers from limited memory issue.

### Critiques:
1.	The reverse of the source sentence does help the LSTM to predict correct the first several words but also put more difficulty for the model to predict the latter words correctly since the ‘time leg’ becomes longer than the normal-order approach. Even though this is good for beam search algorithm but this might not always hold for more advanced sequence generation algorithms and it is counterintuitive to our human learning paradigm, which is supposed to be relatively optimal.
2.	The usage of the last hidden state is not optimal since the intermediate hidden states do contain more word-related information than the last one which is useful for predicting the corresponding translation words in target language later. This actually fosters the later development of attention mechanism.
3.	The paper doesn’t touch much on the hyperparameter selection even though it has good scalability for adding more LSTM layers by adding more GPUs for parallelization. There is no guarantee the number 4 is the optimal selection for the LSTM layer number. In some ways, the model could figure itself how many layers is appropriate for a specific task by adding residual connection.