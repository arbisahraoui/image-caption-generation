

import numpy as np
from keras.applications.vgg16 import VGG16
from keras.models import Model
from keras.layers import Input, Dense, Dropout, LSTM, Embedding, concatenate
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tqdm import tqdm
from nltk.translate.bleu_score import corpus_bleu


"""

    Defining the model

"""

# Define the captioning model
def define_model(vocab_size, max_len, drop_out=0.5, emb_size=256):
     
    # Features extractor model
    image_input = Input(shape=(4096,))
    image_drop  = Dropout(drop_out)(image_input)
    image_model = Dense(emb_size, activation= 'relu')(image_drop)

    # Sequence model
    caption_input = Input(shape=(max_len,))
    caption_emb   = Embedding(vocab_size, emb_size, mask_zero=True)(caption_input)
    caption_drop  = Dropout(drop_out)(caption_emb)
    caption_model = LSTM(256)(caption_drop)

    # Merging the models
    decoder1 = concatenate([image_model, caption_model])
    decoder2 = Dense(256, activation = 'relu')(decoder1)
    outputs  = Dense(vocab_size, activation= 'softmax')(decoder2)

    model = Model(inputs = [image_input, caption_input], outputs= outputs)

    model.compile(loss= 'categorical_crossentropy', optimizer= 'adam')

    return model



"""
	Maps an integer to a its word
"""

def int_to_word(integer, tokenizer):
	for word, index in tokenizer.word_index.items():
		if index == integer:
			return word
	return None



"""
	
    Generating a caption for an image, given a pre-trained model and a tokenizer to map integer back to word
	
"""

def generate_caption(model, tokenizer, image, max_length):

    # Initialize the input sequence
	in_text = 'startseq'
	
	# Iterate over the whole length of the sequence
	for _ in range(max_length):
		# Integer encode input sequence
		sequence = tokenizer.texts_to_sequences([in_text])[0]
		sequence = pad_sequences([sequence], maxlen=max_length)
		
		# Predict next word
		# The model will output a prediction, which will be a probability distribution over all words in the vocabulary.
		yhat = model.predict([image,sequence], verbose=0)
		""" The output vector represents a probability distribution where max probability is the predicted word position
		    Take output class with maximum probability and convert to integer"""
		yhat = np.argmax(yhat)
		
		# Map integer back to word
		word = int_to_word(yhat, tokenizer)
		
		# Stop if we cannot map the word
		if word is None:
			break
		# Append as input for generating the next word
		in_text += ' ' + word
		# Stop if we predict the end of the sequence
		if word == 'endseq':
			break
	return in_text



"""
	Evaluate the model on BLEU Score using argmax predictions
"""

def evaluate_model(model, images, captions, tokenizer, max_length):
	actual, predicted = list(), list()
	for image_id, caption_list in tqdm(captions.items()):
		yhat = generate_caption(model, tokenizer, images[image_id], max_length)
		ground_truth = [caption.split() for caption in caption_list]
		actual.append(ground_truth)
		predicted.append(yhat.split())
	print('BLEU Scores :')
	print('A perfect match results in a score of 1.0, whereas a perfect mismatch results in a score of 0.0.')
	print('BLEU-1: %f' % corpus_bleu(actual, predicted, weights=(1.0, 0, 0, 0)))
	print('BLEU-2: %f' % corpus_bleu(actual, predicted, weights=(0.5, 0.5, 0, 0)))
	print('BLEU-3: %f' % corpus_bleu(actual, predicted, weights=(0.3, 0.3, 0.3, 0)))
	print('BLEU-4: %f' % corpus_bleu(actual, predicted, weights=(0.25, 0.25, 0.25, 0.25)))
