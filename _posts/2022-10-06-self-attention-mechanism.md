## Self-attention with Relative Position Representations
Shaw, Peter and Uszkoreit, Jakob and Vaswani, Ashish
NAACL 2018

### Summary:
The relative positional encoding is the to use the relative position offset relationship to encode the position of the token rather than use the absolute position representation. The purpose of the position encoding is to add position information into the input tokens since Transformer use fully connected network so that the model could distinguish what is the difference between the same word in different position and learn the possible relative position semantics relationship of a type of sequence. To fulfill these two goals, absolute position is capable but not perfect:

Absolute position encodes the relative position information based on the fact that for any fixed position offset k, $$sin((pos+k)/c)$$ can be acquired by the linear (rotation) operation on $$sin(pos/c)$$. However, this rotation matrix is implicit and hard for model to fit.

For any long output sequence that is longer than the training sequence, the absolute position is totally new for the model and thus can’t easily reuse the learned positional information.
These two disadvantages (especially the second) make the model difficult to achieve good performance on long sequence generation tasks (music, paragraph, etc). Thus, a way to directly modeling the relative position for each token is emerging.

The Shaw’s solution is to create a N\*N\*D tensor to store the relative position information compared with the N\*D tensor in abs position. (Notice that there is more space) The modeling way is quite straightforward, for every token, a relative position of other N tokens is encoded into a N\*D tensor. The token itself is the center with the position index as k, while the range of the rest of the positions indice are $$[0,2k+1]$$. The k here is the window size. For any tokens that go out of the window size, the position encoding index will be 0 (left) or 2k+1(right). By this setting, every token has a relative position relationship mapping with others and the problem now is to combine this N\*N\*D tensor into the computation flow since the previous N\*D tensor addition operation won’t fit for such size.

To combine the relative position representation into the flow, they modify two operations:

Previously, the final output value is the attention-based weighted sum of different tokens semantics embeddings. Now, it modified to be the weighted sum of different tokens semantics + relative position embeddings.

When calculating the attention energy between token i and token j, previously we get it by dot product the query i and key j vectors, now, we change to add the relative positional encoding ij onto the key vector j first and then multiply with the query i. So that it has one more term for dot product the positional encoding with the query vector. Somehow it is combined, but this term doesn’t make so much sense to me. (Why not add the attention term directly here)

### Strength:
The relative position provides more explicit position encoding information to the model and thus brings better performance. The further modification of the relative position encoding by Huang makes it easier to generalize to longer sequence due to the save of the memory space. In some way, it mitigate the extra memory usage drawback of this approach.
  
### Critique:
In the Music Transformer developed by Huang et al, the space of relative position encoding is further shrunk to N*D by smartly reusing (skewing) the Q*E matrix. This shows a N fold memory saving and thus could add more heads inside. Even though the information flow is unchanged. 
