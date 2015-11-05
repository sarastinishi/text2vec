import numpy
import collections
import re
import glob
import math
import os
import shutil

import kit
import log
import parameters
import connectors


def iterateSentences(text):
    sentences = re.split('\.', text)
    for sentence in sentences:
        if sentence != '':
            yield sentence


def iterateWords(text):
    for sentence in iterateSentences(text):
        words = re.split('\s+', sentence)

        for word in words:
            if word != '':
                yield word


def subsampleAndPrune(text, wordFrequencyMap, sample, minCount):
    sentences = []

    for sentence in iterateSentences(text):
        words = []

        for word in iterateWords(sentence):
            if word not in wordFrequencyMap:
                continue

            wordFrequency = wordFrequencyMap[word]
            wordSample = numpy.random.random()

            if word in wordFrequencyMap and wordSample > (1 - math.sqrt(sample/wordFrequency)) and wordFrequency >= minCount:
                words.append(word)

        if len(words) > 0:
            sentence = ' '.join(words)
            sentences.append(sentence)

    text = ''
    if len(sentences) > 0:
        text = '. '.join(sentences) + '.'

    return text


def buildWordFrequencyMap(connector):
    wordFrequencyMap = collections.OrderedDict()

    textFilesCount = connector.count()
    for textFileIndex, name, text in connector.iterate():
        for word in iterateWords(text):
            if word not in wordFrequencyMap:
                wordFrequencyMap[word] = 1
            else:
                wordFrequencyMap[word] += 1

        log.progress('Building frequency map: {0:.3f}.', textFileIndex + 1, textFilesCount)

    log.lineBreak()

    return wordFrequencyMap



def weed(inputDirectoryPath, outputDirectoryPath, sample, minCount, connector):
    if os.path.exists(outputDirectoryPath):
        shutil.rmtree(outputDirectoryPath, ignore_errors=True)

    os.mkdir(outputDirectoryPath)
    os.chown(outputDirectoryPath, 1000, 1000)

    textFilesCount = connector.count()

    wordFrequencyMap = buildWordFrequencyMap(connector)

    for textFileIndex, name, text in connector.iterate():
        text = subsampleAndPrune(text, wordFrequencyMap, sample, minCount)
        weededFilePath = os.path.join(outputDirectoryPath, name + '.txt')

        with open(weededFilePath, 'w+') as weededFile:
            weededFile.write(text)

        log.progress('Pruning and subsampling: {0:.3f}.', textFileIndex + 1, textFilesCount)

    log.lineBreak()


def launch(pathTo, hyper):
    weed(
        inputDirectoryPath = pathTo.extractedDir,
        outputDirectoryPath = pathTo.weededDir,
        sample = hyper.sample,
        minCount = hyper.minCount,
        connector = hyper.connector
    )

if __name__ == '__main__':
    pathTo = kit.PathTo('Cockatoo', experiment='default', w2vEmbeddings='wiki_full_s800_w10_mc20_hs1.bin')
    hyper = parameters.HyperParameters(
        sample=1e1,
        minCount=2,
        connector=connectors.TextFilesConnector(pathTo.dataSetDir))

    launch(pathTo, hyper)

