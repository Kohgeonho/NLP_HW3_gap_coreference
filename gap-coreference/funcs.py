def word_subject(row):
    raw = row['Text']
    words, tagged_words, word_index = tokenized_word_sets(row)

    A_id = row['A-offset']
    B_id = row['B-offset']

    def next_word(word):

        tokens = len(row[word].split())
        id = row[word+'-offset']
        index = word_index[id] + tokens

        if tagged_words[index] == ('(', '('):
            close = tagged_words[index:].index((')', ')'))
            if index + close + 1 >= len(tagged_words):
                return tagged_words[index]
            return tagged_words[index + close + 1]
        
        return tagged_words[index]

    if next_word('A')[1].startswith('V'):
        if next_word('B')[1].startswith('V'):
            return (True, True)
        else:
            return (True, False)
    else:
        if next_word('B')[1].startswith('V'):
            return (False, True)
        else:
            return (False, False)

def only_subject(row):
    return sum(word_subject(row))%2 == 1

def both_subject(row):
    return word_subject(row) == (True, True)

def none_subject(row):
    return word_subject(row) == (False, False)

def different_sents(row):
    raw = row['Text']
    words, tagged_words, word_index = tokenized_word_sets(row)

    dots = [i for i, w in enumerate(words) if w == '.']

    pro_id = word_index[row['Pronoun-offset']]
    A_id = word_index[row['A-offset']]
    B_id = word_index[row['B-offset']]

    def between(id1, id2):
        if id1 > id2:
            id1, id2 = id2, id1
        dots = [i for i, w in enumerate(words[id1:id2]) if w == '.']
        if len(dots) > 0:
            return True
        else:
            return False

    return (between(pro_id, A_id), between(pro_id, B_id))

def both_different_sents(row):
    return different_sents(row) == (True, True)

def only_different_sents(row):
    return sum(different_sents(row)) == 1

def none_different_sents(row):
    return different_sents(row) == (False, False)

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

