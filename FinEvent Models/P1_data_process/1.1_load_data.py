# -*- coding: utf-8 -*-
# @Time : 2022/11/29 16:14
# @Author : yysgz
# @File : 1.1_load_data.py
# @Project : P3_FinEvent_Model Models
# @Description :
# generate the initial features for the messages
'''
This file generates the initial message features (please see Figure 1(b) and Section 3.2 of the paper for more details).
To leverage the semantics in the data, we generate document feature for each message,
which is calculated as an average of the pre-trained word embeddings of all the words in the message
We use the word embeddings pre-trained by en_core_web_lg, while other options,
such as word embeddings pre-trained by BERT, are also applicable.
To leverage the temporal information in the data, we generate temporal feature for each message,
which is calculated by encoding the times-tamps: we convert each timestamp to OLE date,
whose fractional and integral components form a 2-d vector.
The initial feature of a message is the concatenation of its document feature and temporal feature.
'''
import numpy as np
import pandas as pd
import datetime

import networkx as nx
from scipy import sparse

import torch

import os
project_path = os.path.abspath(os.path.join(os.getcwd(), "../.."))  # # 获取上上级路径
import en_core_web_lg  # spacy提供的预训练语言模型，将文本标记化已生成doc对象

load_path = project_path + '/data/FinEvent_datasets/raw dataset/'
save_path = project_path + '/result/FinEvent result/'

# load dataset
p_part1 = load_path + '68841_tweets_multiclasses_filtered_0722_part1.npy'
p_part2 = load_path + '68841_tweets_multiclasses_filtered_0722_part2.npy'
# Python 中的 pickle 用于在保存到磁盘文件或从磁盘文件读取之前，对对象进行序列化和反序列化
df_np_part1 = np.load(p_part1, allow_pickle=True)  # allow_pickle, Allow loading pickled object arrays stored in npy files
df_np_part2 = np.load(p_part2, allow_pickle=True)
df = np.concatenate((df_np_part1, df_np_part2),axis=0) # 按行拼接
print('loaded data.')
df = pd.DataFrame(data=df, columns=['event_id','tweet_id','text','user_id','created_at','user_loc','place_type',
                                      'place_full_name','place_country_code','hashtags','user_mentions','image_urls',
                                      'entities','words','filtered_words','sampled_words'])
print('Data converted to dataframe.')
# sort date by time
df = df.sort_values(by='created_at').reset_index(drop=True)

df['date'] = [d.date() for d in df['created_at']]
# 因为graph太大，爆了内存，所以取4天的twitter data做demo，后面用nci server
init_day = df.loc[0, 'date']
df_4days = df[(df['date']>= init_day) & (df['date']<= init_day + datetime.timedelta(days=3))].reset_index()

print(df_4days.shape)
print(df_4days.event_id.nunique())
print(df_4days.user_id.nunique())

# calculate the embeddings of all the documents in the dataframe
# the embeddings of each document is an average of the pre-trained embeddings of all the words in it
def documents_to_features(df):
    nlp = en_core_web_lg.load()
    features = df.filtered_words.apply(lambda x: nlp(' '.join(x)).vector).values  # nlp生成300维向量；join函数将列表连接成字符串
    return np.stack(features, axis=0)  # stack函数沿axis邻接数组序列

# encode one times-tamp
# t_str: a string of format '2012-10-11 07:19:34'
def extract_time_feature(t_str):
    t = datetime.datetime.fromisoformat(str(t_str)) # 分别返回年月日时分秒列表
    OLE_TIME_ZERO = datetime.datetime(1899, 12, 30)
    delta = t - OLE_TIME_ZERO  # datetime.timedelta(days=41193, seconds=26374)
    return [(float(delta.days)/10000.), (float(delta.seconds)/86400)] # 86400 seconds in day

# encode the times-tamps of all the messages in the dateframe
def df_to_t_features(df):
    t_features = np.asarray([extract_time_feature(t_str) for t_str in df['created_at']])
    return t_features

# 生成文档embedding
d_features = documents_to_features(df_4days)
print('Document features generated')

# 生成时间特征days和seconds
t_features = df_to_t_features(df_4days)
print('Time features generated.')

combined_features = np.concatenate((d_features, t_features), axis=1)
print('Concatenated document features and time features.')

np.save(save_path + 'combined_features.npy', combined_features)
print('Initial features saved.')

combined_features = np.load(save_path + 'combined_features.npy')
print('Initial features loaded.')
print(combined_features.shape)