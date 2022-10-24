# Pixel Recurrent Neural Network
Aäron van den Oord, Nal Kalchbrenner, Koray Kavukcuoglu 
PMLR 2016

## Summary:
The paper tries to model the distribution of natural images in an unsupervised way. The challenges lie in the high dimensional and structured nature of the image data and the tractability and scalability of the generative model. The paper innovates the NN architecture by implementing 2D recurrent layer with residual connection and the PixelCNN which leverage CNN to sequence processing. 

The LSTM contains two components: state-to-state and input-to-state. For input-to-state component, the Row LSTM will take the whole input map and apply k*1 masked convolution to include only valid context. For RowLSTM, only input from left and above pixels will be used. The state-to-state component takes the previous hidden state and cell state. So overall, the RowLSTM process the image row by row with convolution and use the convolution result to guide the next pixel generation.

The diagonal bi-LSTM first skew the input map to make it easier to apply diagonal convolution. The input-to-state component applies 1*1 convolution for the four gates. The state-to-state is computed with a column-wise convolution kernel size 2*1. As the RowLSTM, the step take the previous hidden and output state and generate the current output state. To prevent the content from right is released, the right LSTM will shift one row down and added to the left output map.

PixelCNN is to reduce the time brought by the sequential computation process of RNN. The PixelCNN applies multiple convolution kernels and use mask to prevent future context as before. The PixelCNN also processes information sequentially in the generation phase but since the parallelization potential, it could save time during training phase.

Multi-Scale PixelRNN sample the context with period. So that the context information could cover more scope of the input information.

## Strength:
The PixelRNN provides a framework how to use RNN+CNN structure to do image generation. Even though the LSTM model here is relatively computational heavy compared with simpler model (GLU), it could leverage better the longer sequence context information and change the traditional dot product gate operations into the convolution to fit for the image domain applications.

## Critique:
The image task usually has long sequence data. However, the RNN/LSTM suffers from the long term memory loss. In the image generation case, the previous context pixel might be forgotten during autoregression. Even though Transformer appears after a year of this work, the idea of using Transformer structure to overcome this shortage but combing this paper’s methods is really worthy to try.

Also the organization of the paper is confusing and the theme is not clear enough. Authors have done so much exploration and wanted to include everything together without good refinement. Even though the title of the paper is Pixel RNN, it actually proposed many CNN based structures. The figures in the paper are also not coherent enough with the writing.
