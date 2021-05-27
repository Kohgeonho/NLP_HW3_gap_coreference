import pandas as pd

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