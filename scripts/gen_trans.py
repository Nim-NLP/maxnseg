import math
import sys
from os import path,unlink
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
        if pre_word != "<BEG>" and re.search(punc,pre_word):
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
    result = "import tables\n{.push checks: off, optimization: speed.}\n"
   

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

    freq_prob_str = "import tables\n{.push checks: off, optimization: speed.}\n"
    freq_prob_str += "const allFreq* = %s\n" % all_freq
    freq_prob_str += "const maxWordLen* = %s\n" % max_wordlen
    freq_prob_str += "let %s = %s\n" %  ("wordFreqProb*:TableRef[string,array[2,BiggestFloat]]", 
                            json.dumps(freq_prob, ensure_ascii=False).replace("}", "}.newTable")
                          )
    
    # result += "let %s = %s\n" % ("transFreq*:TableRef[string,TableRef[string,int]]",
    #                       json.dumps(trans_dict_count, ensure_ascii=False).replace("}", "}.newTable")
    #                       )
    freq_prob_str += "\n{.pop.}"
    result += "\n{.pop.}"
    # re.sub('("[^\"]+")',r"\1.hash ",
    # cleaned = ""
    # punc = "[\"|\s][０１２３４５６７８９！？。＂＃$＄％&＆'＇（）＊＋，－／：；<＜＝>＞@［＿｀`｛|｜｝~～《》｟｠｢｣、〃「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏]"
     
    # for line in result.splitlines(keepends=True):
    #     if re.search(punc,line) :
    #         continue
    #     else:
    #         cleaned+=line
    bg = path.join(cur_dir, "..", "src", "maxnseg", "backward_gram.dict")
    sb = path.join(cur_dir, "..", "src", "maxnseg", "sb.nim")
    if path.exists(bg):
        unlink(bg)
    with open(bg, "a") as f,\
        open(path.join(cur_dir, "..", "src", "maxnseg", "freq_prob.nim"), "w") as f2,\
        open(sb,"w") as f3:
        for k,v in trans_dict_count.items():
            if k == "<BEG>":
                f3.write("import tables\nlet %s = %s\n" %  ("wordFreq*:TableRef[string,int]", 
                            json.dumps(trans_dict_count[k], ensure_ascii=False,indent=4).replace("}", "}.newTable")
                          ))
            else:
                f.write(k+","+json.dumps(v, ensure_ascii=False)+"\n")
        f2.write(freq_prob_str)
