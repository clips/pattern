import numpy as np
from fastai.text import *
from fastai.lm_rnn import get_rnn_classifer
import html
from nltk import word_tokenize


class Tokenizer():
    def __init__(self, lang='en'):
        pass

    def spacy_tok(self,x):
        return word_tokenize(x)

    def proc_text(self, s):
        return self.spacy_tok(s)

    @staticmethod
    def proc_all(ss, lang):
        tok = Tokenizer(lang)
        return [tok.proc_text(s) for s in ss]

    @staticmethod
    def proc_all_mp(ss, lang='en'):
        ncpus = num_cpus()//2
        with ProcessPoolExecutor(ncpus) as e:
            return sum(e.map(Tokenizer.proc_all, ss, [lang]*len(ss)), [])


class ULMFiT:

    def __init__(self,model: str):
        model_path = Path(model)
        itos_filename = model_path/"news_lm"/"tmp"/'itos.pkl'
        trained_classifier_filename = model_path/'models'/'clas_2.h5'
        label2index = model_path/"news_clas"/"l2i.npy"
        self.l2i = {v:k for k,v in np.load(label2index).item().items()}
        self.stoi, self.model = self.load_model(itos_filename, trained_classifier_filename)
        self.re1 = re.compile(r'  +')

    def load_model(self,itos_filename, classifier_filename):
        """Load the classifier and int to string mapping

        Args:
            itos_filename (str): The filename of the int to string mapping file (usually called itos.pkl)
            classifier_filename (str): The filename of the trained classifier

        Returns:
            string to int mapping, trained classifer model
        """

        # load the int to string mapping file
        itos = pickle.load(Path(itos_filename).open('rb'))
        # turn it into a string to int mapping (which is what we need)
        stoi = collections.defaultdict(lambda:0, {str(v):int(k) for k,v in enumerate(itos)})

        # these parameters aren't used, but this is the easiest way to get a model
        bptt,em_sz,nh,nl = 70,400,1150,3
        dps = np.array([0.4,0.5,0.05,0.3,0.4])*0.5
        num_classes = len(self.l2i) # this is the number of classes we want to predict
        vs = len(itos)

        model = get_rnn_classifer(bptt, 20*70, num_classes, vs, emb_sz=em_sz, n_hid=nh, n_layers=nl, pad_token=1,
                layers=[em_sz*3, 50, num_classes], drops=[dps[4], 0.1],
                dropouti=dps[0], wdrop=dps[1], dropoute=dps[2], dropouth=dps[3])

        # load the trained classifier
        model.load_state_dict(torch.load(classifier_filename, map_location=lambda storage, loc: storage))

        # put the classifier into evaluation mode
        model.reset()
        model.eval()

        return stoi, model


    def softmax(self,x):
        '''
        Numpy Softmax, via comments on https://gist.github.com/stober/1946926

        >>> res = softmax(np.array([0, 200, 10]))
        >>> np.sum(res)
        1.0
        >>> np.all(np.abs(res - np.array([0, 1, 0])) < 0.0001)
        True
        >>> res = softmax(np.array([[0, 200, 10], [0, 10, 200], [200, 0, 10]]))
        >>> np.sum(res, axis=1)
        array([ 1.,  1.,  1.])
        >>> res = softmax(np.array([[0, 200, 10], [0, 10, 200]]))
        >>> np.sum(res, axis=1)
        array([ 1.,  1.])
        '''
        if x.ndim == 1:
            x = x.reshape((1, -1))
        max_x = np.max(x, axis=1).reshape((-1, 1))
        exp_x = np.exp(x - max_x)
        return exp_x / np.sum(exp_x, axis=1).reshape((-1, 1))

    def fixup(self, x):
        
        x = x.replace('#39;', "'").replace('amp;', '&').replace('#146;', "'").replace(
        'nbsp;', ' ').replace('#36;', '$').replace('\\n', "\n").replace('quot;', "'").replace(
        '<br />', "\n").replace('\\"', '"').replace('<unk>','u_n').replace(' @.@ ','.').replace(
        ' @-@ ','-').replace('\\', ' \\ ').replace('\u200d','').replace('\xa0',' ').replace(
        '\u200c','').replace('“',' ').replace('”',' ').replace('"',' ').replace('\u200b','')
        x = re.sub('[\(\[].*?[\)\]]', '', x)
        x = re.sub('<[^<]+?>', '', x)
        x = re.sub('[A-Za-z]+','ENG ', x)
        x = re.sub(r'\d+.?(\d+)?','NUM ',x).replace("(","").replace(")","")
        return self.re1.sub(' ', html.unescape(x))

    def predict_text(self,stoi, model, text):
        """Do the actual prediction on the text using the
            model and mapping files passed
        """

        # prefix text with tokens:
        #   xbos: beginning of sentence
        #   xfld 1: we are using a single field here
        input_str = self.fixup(text)
#         input_str = re.sub('[A-Za-z]+','ENG ', input_str)
#         input_str = re.sub(r'\d+.?(\d+)?','NUM ',input_str).replace("(","").replace(")","")
        
        # predictions are done on arrays of input.
        # We only have a single input, so turn it into a 1x1 array
        texts = [input_str]

        # tokenize using the fastai wrapper around spacy
        tok = Tokenizer().proc_text(input_str)

        # turn into integers for each word
        encoded = [stoi[p] for p in tok]
#         print(encoded)
        # we want a [x,1] array where x is the number
        #  of words inputted (including the prefix tokens)
        ary = np.reshape(np.array(encoded),(-1,1))

        # turn this array into a tensor
        tensor = torch.from_numpy(ary)

        # wrap in a torch Variable
        variable = Variable(tensor)

        # do the predictions
        predictions = model(variable)

        # convert back to numpy
        numpy_preds = predictions[0].data.numpy()

        return self.softmax(numpy_preds[0])[0], input_str

    def predict(self,text):
        intent = {}
        output, fixed_text = self.predict_text(self.stoi, self.model, text)
        intent_ranking = []
        for i, out in enumerate(output):
            temp = {"confidence": float(format(out, 'f')), "name": self.l2i[i]}
            intent_ranking.append(temp)
        intent_ranking = sorted(intent_ranking, key=lambda e: e['confidence'], reverse=True)
        intent.update({
                    "intent": intent_ranking.pop(0),
                    "intent_ranking": intent_ranking
        })
        intent.update({"processed_text": fixed_text})
        return intent#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  1 00:54:22 2019

@author: abhijithneilabraham
"""

