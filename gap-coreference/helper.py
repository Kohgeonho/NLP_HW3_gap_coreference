import pandas as pd
import nltk
import re

def tokenized_index(row):
    raw = row['Text']
    words = nltk.word_tokenize(row['Text'])
    sents = [nltk.word_tokenize(sent) for sent in nltk.tokenize.sent_tokenize(raw)]
    tagged_words = nltk.pos_tag(words)
    tagged_sents = [nltk.pos_tag(sent) for sent in sents]
    word_index = {}
    sent_index = {}
    index = 0

    for i, word in enumerate(words):

        if word in ["''", "``"]:
            to_find = re.compile("''|``")
            spaces = to_find.search(raw[index:]).start()
        else:
            spaces = raw[index:].index(word)

        word_index[index+spaces] = i

        if "'" in word:                             ## words like 'Abigail'
            word_index[index+spaces+1] = i
        elif "/" in word:                           ## words like Abigail/Bill
            slash = raw[index:].index('/')
            word_index[index+slash+1] = i
        elif "." in word:                           ## words like Ms.Abigail
            dots = [i for i in range(len(word)) if word[i] == '.'][-1]
            word_index[index+spaces+dots+1] = i

        index += spaces + len(word)

    index = 0
    for i, sent in enumerate(sents):
        for word in sent:
            sent_index[index] = i
            index += 1

    return {'words': words, 
            'sents': sents,
            'tagged_words': tagged_words,
            'tagged_sents': tagged_sents,
            'word_index': word_index,
            'sent_index': sent_index}

def print_sents(num_lines=10, datatype='train', random=True, datas={'manual':False, 'data':None}):
    
    if datas['manual'] == False:
        if datatype == 'train':
            data = "gap-development.tsv"
        elif datatype == 'validate':
            data = "gap-validation.tsv"
        elif datatype == 'test':
            data = "gap-test.tsv"
        else:
            data = "gap-development.tsv"

        lines = pd.read_csv('gap-development.tsv', sep='\t')
    else:
        lines = datas['data']

    if random:
        lines = lines.sample(frac=1)

    count = 1
    for row in lines.iloc:

        sent = row['Text']
        pn, pn_id = row[['Pronoun', 'Pronoun-offset']]
        A, A_id = row[['A', 'A-offset']]
        B, B_id = row[['B', 'B-offset']]

        pn_len, A_len, B_len = len(pn), len(A), len(B)

        pn = "\033[94m" + pn + "\033[0m"
        A  = "\033[92m" + A  + "\033[0m" if row['A-coref'] else \
             "\033[91m" + A  + "\033[0m"
        B  = "\033[92m" + B  + "\033[0m" if row['B-coref'] else \
             "\033[91m" + B  + "\033[0m"

        indices = [(pn_id, pn, pn_len), (A_id, A, A_len), (B_id, B, B_len)]

        for index, content, length in sorted(indices, reverse=True):
            sent = sent[:index] + content + sent[index+length:]

        print(sent, end='\n\n')

        count += 1
        if count > num_lines:
            break



def accuracy(data):
    right_count = 0
    
    for row in data.iloc:
        if row['A-pred'] == row['A-coref'] and row['B-pred'] == row['B-coref']:
            right_count += 1
    
    return right_count/len(data)

def apply_model(data, func_list, pred):

    filtered_data = data.copy()
    for func in func_list:
        mask = filtered_data.apply(func, axis=1)
        filtered_data = filtered_data[mask]

    pred_data = filtered_data.copy()
    pred_data['A-pred'] = pred_data.apply(lambda row: pred(row)[0], axis=1)
    pred_data['B-pred'] = pred_data.apply(lambda row: pred(row)[1], axis=1)

    print(len(pred_data), accuracy(pred_data))

    return pred_data