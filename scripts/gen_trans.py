import math
import sys
from os import path
import json
import re
from collections import defaultdict

cur_dir = path.abspath(path.dirname(__file__))
model_dir = path.normpath(path.join(cur_dir, "..", "model"))
word_count_path = path.normpath(path.join(model_dir, "word_dict.model"))
word_trans_path = path.normpath(path.join(model_dir, "trans_dict.model"))

word_dict = {}  # 记录概率,1-gram '无能为力': -12.61044837259944
word_dict_count = {}  # 记录词频,1-gram  '无能为力': 11

trans_dict_count = defaultdict(dict)  # 记录词频,2-gram
max_wordlen = 0  # 词的最长长度
all_freq = 0  # 所有词的词频总和,1-gram
punc = "[０１２３４５６７８９！？。＂＃$＄％&＆'＇（）＊＋，－／：；<＜＝>＞@［＿｀`｛|｜｝~～《》｟｠｢｣、〃「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏]"
     

def load_model(model_path):
    f = open(model_path, 'r')
    a = f.read()
    word_dict = eval(a)
    f.close()
    return word_dict


def init():
    global word_dict_count, word_dict, max_wordlen, all_freq,trans_dict_count,punc
    # trans_dict = {}  # 记录概率,2-gram
    word_dict_count = load_model(word_count_path)
    all_freq = sum(word_dict_count.values())  # 所有词的词频
    max_wordlen = max(len(key) for key in word_dict_count.keys())
    for key in word_dict_count:
        word_dict[key] = math.log(word_dict_count[key] / all_freq)
    # 计算转移概率
    Trans_dict = load_model(word_trans_path)
    for pre_word, post_info in Trans_dict.items():
        if re.search(punc,pre_word):
            continue
        for post_word, count in post_info.items():
            if re.search(punc,post_word):
                continue
            # word_pair = pre_word + ' ' + post_word
            trans_dict_count[pre_word][post_word] = count
            # if pre_word in word_dict_count.keys():
            #     trans_dict[key] = math.log(
            #         count / word_dict_count[pre_word])  # 取自然对数，归一化
            # else:
            #     trans_dict[key] = word_dict[post_word]

if __name__ == "__main__":
    init()
    TEMPLATE = "let %s = %s\n"
    result = "import tables\nimport hashes\n"
   

    # result += TEMPLATE % ("wordProb",
    #                       json.dumps(word_dict, ensure_ascii=False,
    #                                  indent=2).replace("}", "}.newTable")

    #                       )
    # result += TEMPLATE % ("wordFreq", json.dumps(word_dict_count, ensure_ascii=False, indent=2).replace("}", "}.newTable")

    #                       )
    freq_prob = defaultdict(list)
    for k,v in word_dict_count.items():
        freq_prob[k].append(float(v))
        freq_prob[k].append(word_dict[k])

    freq_prob_str = "import tables\nimport hashes\n"
    freq_prob_str += "const allFreq* = %s\n" % all_freq
    freq_prob_str += "const maxWordLen* = %s\n" % max_wordlen
    freq_prob_str += "const %s = %s\n" %  ("wordFreqProb*:Table[Hash,array[2,BiggestFloat]]", 
                            re.sub('("[^\"]+")',r"\1.hash ",json.dumps(freq_prob, ensure_ascii=False).replace("}", "}.toTable"))
                          )
    
    result += "const %s = %s\n" % ("transFreq*:Table[Hash,Table[Hash,int]]",
                          re.sub('("[^\"]+")',r"\1.hash ",json.dumps(trans_dict_count, ensure_ascii=False,).replace("}", "}.toTable"))
                          )
    # cleaned = ""
    # punc = "[\"|\s][０１２３４５６７８９！？。＂＃$＄％&＆'＇（）＊＋，－／：；<＜＝>＞@［＿｀`｛|｜｝~～《》｟｠｢｣、〃「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏]"
     
    # for line in result.splitlines(keepends=True):
    #     if re.search(punc,line) :
    #         continue
    #     else:
    #         cleaned+=line

    with open(path.join(cur_dir, "..", "src", "maxnseg", "backward_gram.nim"), "w") as f,\
        open(path.join(cur_dir, "..", "src", "maxnseg", "freq_prob.nim"), "w") as f2:
        f.write(result)
        f2.write(freq_prob_str)
