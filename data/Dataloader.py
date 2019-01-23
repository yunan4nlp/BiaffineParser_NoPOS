from data.Vocab import *
import numpy as np
import torch
from torch.autograd import Variable
import argparse

def read_corpus(file_path, vocab=None):
    data = []
    with open(file_path, 'r', encoding='utf8') as infile:
        for sentence in readDepTree(infile, vocab):
            data.append(sentence)
    return data

def sentences_numberize(sentences, vocab):
    for sentence in sentences:
        yield sentence2id(sentence, vocab)

def sentence2id(sentence, vocab):
    result = []
    for dep in sentence:
        wordid = vocab.word2id(dep.form)
        extwordid = vocab.extword2id(dep.form)
        head = dep.head
        relid = vocab.rel2id(dep.rel)
        result.append([wordid, extwordid, head, relid])

    return result



def batch_slice(data, batch_size):
    batch_num = int(np.ceil(len(data) / float(batch_size)))
    for i in range(batch_num):
        cur_batch_size = batch_size if i < batch_num - 1 else len(data) - batch_size * i
        sentences = [data[i * batch_size + b] for b in range(cur_batch_size)]

        yield sentences


def data_iter(data, batch_size, shuffle=True):
    """
    randomly permute data, then sort by source length, and partition into batches
    ensure that the length of  sentences in each batch
    """

    batched_data = []
    if shuffle: np.random.shuffle(data)
    batched_data.extend(list(batch_slice(data, batch_size)))

    if shuffle: np.random.shuffle(batched_data)
    for batch in batched_data:
        yield batch


def batch_data_variable(batch, vocab):
    length = len(batch[0])
    batch_size = len(batch)
    for b in range(1, batch_size):
        if len(batch[b]) > length: length = len(batch[b])

    words = Variable(torch.LongTensor(batch_size, length).zero_(), requires_grad=False)
    extwords = Variable(torch.LongTensor(batch_size, length).zero_(), requires_grad=False)
    masks = Variable(torch.Tensor(batch_size, length).zero_(), requires_grad=False)
    heads = []
    rels = []
    lengths = []

    b = 0
    for sentence in sentences_numberize(batch, vocab):
        index = 0
        length = len(sentence)
        lengths.append(length)
        head = np.zeros((length), dtype=np.int32)
        rel = np.zeros((length), dtype=np.int32)
        for dep in sentence:
            words[b, index] = dep[0]
            extwords[b, index] = dep[1]
            head[index] = dep[2]
            rel[index] = dep[3]
            masks[b, index] = 1
            index += 1
        b += 1
        heads.append(head)
        rels.append(rel)

    return words, extwords, heads, rels, lengths, masks

def batch_variable_depTree(trees, heads, rels, lengths, vocab):
    for tree, head, rel, length in zip(trees, heads, rels, lengths):
        sentence = []
        for idx in range(length):
            sentence.append(Dependency(idx, tree[idx].org_form, tree[idx].tag, head[idx], vocab.id2rel(rel[idx])))
        yield sentence


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--train', default='examples/ptb/dev1.ptb.conll06.out')
    argparser.add_argument('--dev', default='examples/ptb/dev1.ptb.conll06')
    argparser.add_argument('--emb', default='examples/glove.6B.100d.txt')
    argparser.add_argument('--use-cuda', action='store_true', default=True)

    args, extra_args = argparser.parse_known_args()

    vocab = creatVocab(args.train, 2)
    vocab.load_pretrained_embs(args.emb)

    train_data = read_corpus(args.train, vocab)
    dev_data = read_corpus(args.dev, vocab)



    for onebatch in data_iter(train_data, 100, False):
        words, extwords, heads, rels, lengths, masks = batch_data_variable(onebatch, vocab)

