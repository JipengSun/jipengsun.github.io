## BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
Jacob Devlin Ming-Wei Chang Kenton Lee Kristina Toutanova
2019 NAACL
### Summary:
The BERT pre-training model is a language model that designed to use bi-directional Transformer architecture to get a contextual semantics embedding for the word sequence. The goal of BERT is to build a pre-training language model that could handle all other specific language tasks by directly using its output representation and adding up simple task-related layers after BERT layers to avoid training large corpus from scratch. This idea is called fine-tuning. 

Fine-tunning demands the BERT to model the context information (both left-to-right and right-to-left) of each word to better capture the semantics. By that time, only bi-LSTM could satisfy this requirement even though Transformer is proofed to overperform it. BERT thus proposed a bi-directional revision on Transformer: First it only keeps the encoder part of the Transformer since the language model task here also requires the length match between the input and output sequence; Then to avoid the leak of the target word information in the later Transformer layers in bi-directional design, it introduces the traditional mask idea to mask out the target word to make the model predict the probability distribution of the candidate words without knowing the target word information in later layers. Therefore, the BERT model is trained to predict the correct full sentence of the input masked sentence. 

There are three important things to notice here. First, the input token is not the pure word embedding tokens, it is the sum of the token embeddings, the segment embeddings, and the position embeddings. However, the output of the BERT is the pure word embedding. Second, to model the sequence level information, the input word sequence is separated by [Seg] token and the beginning of every  input sequence is always the [CLS] token. For the output of that [CLS] token position, it is going to predict whether the input sentences is the related next sentence.(To force the model understand the sentence-level semantics information, the input sequence might contain two unrelated sentences.) Third, since there is no [Mask] token for later task specific fine-tunning, the BERT has to mitigate the mismatch by only mask target words in 80% of the time, and 10% for random token and another 10% for providing the original tokens. By this way, it could force the model not to purely rely on the specific input token making the predication but the whole sentence context semantics. 

Later to use the BERT model, one only needs to do several steps:
1.	Tokenize the input sequence in the BERT way
2.	Get the output of the BERT.
3.	If it is a sentence level classification task, only use the first dimension ([CLS]), if it other task, use the whole output.
4.	Build your own simple task specific model and use the Step 3 well-represented output as input.

### Strength:
The BERT is usually compared with the uni-directional Transformer based language model OpenAI GPT and bi-directional LSTM language model ELMo. The strength of BERT lies in two aspects:
Compared with OpenAI GPT, the BERT firstly achieves bi-directional Transformer. The ablation environment shows bi-directional Transformer encodes better context information than uni-direction.
Compared with ELMo, the Transformer structure is faster and handle better on long sequences.

### Critique:
From my point of view, the NSP prediction in training seems to be un-relevant to the whole sentence semantics. It only tells the model whether it is relevant to later sentence, rather than encode more global semantics. The problem here is that NSP is for a binary task while infinite sentences have infinite potential meanings. The solution space here is not match. You can tell one sentence is not following another sentence without the need to know the exact semantics of the sentence.
