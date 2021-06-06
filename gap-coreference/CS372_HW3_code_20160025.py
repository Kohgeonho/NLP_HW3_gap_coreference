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

    def symbols(index, symbol, word, i):
        syms = [ind for ind, c in enumerate(word) if c==symbol]
        for ind in syms:
            word_index[index+ind+1]=i

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
            symbols(index+spaces, '/', word, i)
        elif "." in word:                           ## words like Ms.Abigail
            dots = [i for i in range(len(word)) if word[i] == '.'][-1]
            word_index[index+spaces+dots+1] = i
        elif "-" in word:                           ## words like Ask-Elizabeth
            symbols(index+spaces, '-', word, i)

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

train_data = pd.read_csv('gap-development.tsv', sep='\t')
test_data  = pd.read_csv('gap-test.tsv', sep='\t')

def word_subject(row):
    token_dict = tokenized_index(row)

    tagged_words = token_dict['tagged_words']
    word_index = token_dict['word_index']

    def next_word(word):

        tokens = len(row[word].split())
        id = row[word+'-offset']
        index = word_index[id] + tokens

        if tagged_words[index] == ('(', '('):
            close = tagged_words[index:].index((')', ')'))
            if index + close + 1 >= len(tagged_words):
                return tagged_words[index]
            index += close + 1

        return tagged_words[index]

    def word_verb(tagged_word):
        word, tag = tagged_word
        return tag.startswith('V') or tag.startswith('MD') or tag.startswith('RB')

    return (word_verb(next_word('A')), word_verb(next_word('B')))

def only_subject(row):
    return sum(word_subject(row)) == 1

def both_subject(row):
    return word_subject(row) == (True, True)

def none_subject(row):
    return word_subject(row) == (False, False)

def former_word(row):
    if row['A-offset'] < row['B-offset']:
        return (True, False)
    return (False, True)

def latter_word(row):
    if row['A-offset'] < row['B-offset']:
        return (False, True)
    return (True, False)

def closer_word(row):
    if abs(row['A-offset']-row['Pronoun-offset']) < abs(row['B-offset'] - row['Pronoun-offset']):
        return (True, False)
    else:
        return (False, True)

def farther_word(row):
    if abs(row['A-offset']-row['Pronoun-offset']) < abs(row['B-offset'] - row['Pronoun-offset']):
        return (False, True)
    else:
        return (True, False)

def both_latter(row):
    if row['A-offset'] > row['Pronoun-offset'] and row['B-offset'] > row['Pronoun-offset']:
        return True

    return False

def isparenthesis(row):
    sent = row['Text']
    A = row['A']
    A_id = row['A-offset']
    B = row['B']
    B_id = row['B-offset']

    return (not (sent[A_id-1] == "(" and sent[A_id+len(A)] == ")"),
            not (sent[B_id-1] == "(" and sent[B_id+len(B)] == ")"))

def only_parenthesis(row):
    return sum(isparenthesis(row)) == 1

def another_subject(row):
    token_dict = tokenized_index(row)

    tagged_sents = token_dict['tagged_sents']
    sents = token_dict['sents']
    word_index = token_dict['word_index']
    sent_index = token_dict['sent_index']

    pro_sent_id = sent_index[word_index[row['Pronoun-offset']]]

    def first_noun(sent):
        for word, tag in sent:
            if tag.startswith('NN') or tag.startswith('PR'):
                return (word, tag)

    word, tag = first_noun(tagged_sents[pro_sent_id])
    if tag.startswith('NNP') and not word in [row['A'].split()[0], row['B'].split()[0]]:
        return True

    return False

def CC_pronoun(row):
    token_dict = tokenized_index(row)

    tagged_words = token_dict['tagged_words']
    word_index = token_dict['word_index']

    pro_index = word_index[row['Pronoun-offset']]
    A_index = word_index[row['A-offset']]
    B_index = word_index[row['B-offset']]

    def coref(index):
        if index+5 >= len(tagged_words):
            return False
        return (tagged_words[index+1][1] == 'CC' and pro_index == index + 2) or \
               (tagged_words[index+2][1] == 'CC' and pro_index == index + 3)

    return coref(A_index), coref(B_index)

def exist_CC_pronoun(row):
    return sum(CC_pronoun(row)) == 1

def begin_sentence(row):

    token_dict = tokenized_index(row)
    tagged_sents = token_dict['tagged_sents']

    Subjects = []

    def first_NP(sent):

        first_np = ""
        index=0
        while sent[index][1].startswith('NN') or sent[index][1].startswith('W') or sent[index][1] in ["'s", 'DT', 'IN', 'CD']:
            while sent[index][1].startswith('NNP'):
                first_np += sent[index][0] + " "
                if index < len(sent) - 1:
                    index += 1
                else:
                    break

            if len(first_np) > 0:
                Subjects.append(first_np)

            if index < len(sent) - 1:
                index += 1
            else:
                break

    def tagged_split(tagged_sent):
        splitted = []
        index = 0
        
        while(index < len(tagged_sent)):
            try:
                new_index = tagged_sent[index:].index((',',','))
                splitted.append(tagged_sent[index:index+new_index])
                index += new_index+1
            except:
                splitted.append(tagged_sent[index:])
                return splitted

    for sent in tagged_sents:
        for sub_sent in tagged_split(sent):
        
            first_np = first_NP(sub_sent)

    def exist(word):
        for first_word in Subjects:
            if word in first_word:
                return True
            elif first_word in word:
                return True
        return False

    return (exist(row['A']), exist(row['B']))

def begin_sentence_word(row):
    return sum(begin_sentence(row)) == 1

def most_occurance(row):

    token_dict = tokenized_index(row)
    tagged_words = token_dict['tagged_words']

    index=0
    NPs = []
    NP_dict = {}

    while index < len(tagged_words):
        np = ""
        while index < len(tagged_words) and tagged_words[index][1].startswith('NNP'):
            np += tagged_words[index][0] + " "
            index += 1
        
        if len(np) > 0:
            NPs.append(np[:-1])

        index += 1

    def occurance(word):
        occ = 0
        for w in NPs:
            if w in word:
                occ += 1

        return occ

    for word in set(NPs):
        NP_dict[word] = occurance(word)

    max_occ = sorted(NP_dict.items(), key = (lambda x: x[1]), reverse=True)[0]

    if max_occ[1] > 1:
        return [NP for NP in NP_dict if NP_dict[NP] == max_occ[1]]
    else:
        return None

def more_occurance(row):

    most_occs = most_occurance(row)

    if most_occs == None:
        return (True, True)

    def exist(word, words):
        for w in words:
            if word in w or w in word:
                return True
        return False

    return (exist(row['A'], most_occs), exist(row['B'], most_occs))

def only_most_occurance(row):
    return sum(more_occurance(row)) == 1

def none_most_occurance(row):
    return sum(more_occurance(row)) == 0

def both_most_occurance(row):
    return more_occurance(row) == (True, True)

def subject(row):

    ## 3.1. When words are inside parenthesis
    if only_parenthesis(row):
        return isparenthesis(row)

    ## 5.1. When only one word is subject
    elif only_subject(row):
        if row['Pronoun'] == 'him':
            return latter_word(row)

        return word_subject(row)

    ## 5.2. When both words are subject
    elif both_subject(row):
        if row['Pronoun'] == 'him':
            return former_word(row)

        return latter_word(row)

    ## 6. When both words are not subject
    elif none_subject(row):
        ## 4.2. When both words appear latter than pronoun, and there is another subject rather than the words.
        if both_latter(row) and another_subject(row):
            return (False, False)

        ## 3.3. When pattern like <(word) and (his|her)> appears, coreference of the word is always true.
        elif exist_CC_pronoun(row):
            return CC_pronoun(row)

        ## 6. Check the frequency of words in the text.
        else:
            ## 6.1 If a word appears multiple times in the text.
            if only_most_occurance(row):
                return more_occurance(row)

            ## 6.2 If the frequency of both words are same(but more than once).
            elif both_most_occurance(row):
                if row['Pronoun'] in ['He', 'She', 'His', 'Her', 'he', 'she']:
                    return former_word(row)

                elif row['Pronoun'] in ['him', 'his', 'her', 'hers']:
                    return latter_word(row)

                else:
                    print('unexpected pronoun : ', row['Pronoun'])

            ## 7. If the frequency of every proper nouns in the text is 1.
            elif none_most_occurance(row):
                return begin_sentence(row)

    else:
        print("error cases : no subject")



def apply_model(data, func_list, pred):

    filtered_data = data.copy()
    for func in func_list:
        mask = filtered_data.apply(func, axis=1)
        filtered_data = filtered_data[mask]

    pred_data = filtered_data.copy()
    pred_data['A-pred'] = pred_data.apply(lambda row: pred(row)[0], axis=1)
    pred_data['B-pred'] = pred_data.apply(lambda row: pred(row)[1], axis=1)

    return pred_data

subject_data = apply_model(test_data, [], subject)

result = open("CS372_HW3_snippet_output_20160025.tsv", 'w')
result2= open("CS372_HW3_page_output_20160025.tsv", "w")

for row in subject_data.iloc:

    result.write("\t".join([row['ID'], str(row['A-pred']), str(row['B-pred'])]) + "\n")
    result2.write("\t".join([row['ID'], str(row['A-pred']), str(row['B-pred'])]) + "\n")

result.close()