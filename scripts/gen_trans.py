import math
import sys
from os import path
import json
import re

cur_dir = path.abspath(path.dirname(__file__))
model_dir = path.normpath(path.join(cur_dir, "..", "model"))
word_count_path = path.normpath(path.join(model_dir, "word_dict.model"))
word_trans_path = path.normpath(path.join(model_dir, "trans_dict.model"))

word_dict = {}  # 记录概率,1-gram '无能为力': -12.61044837259944
word_dict_count = {}  # 记录词频,1-gram  '无能为力': 11

trans_dict_count = {}  # 记录词频,2-gram
max_wordlen = 0  # 词的最长长度
all_freq = 0  # 所有词的词频总和,1-gram


def load_model(model_path):
    f = open(model_path, 'r')
    a = f.read()
    word_dict = eval(a)
    f.close()
    return word_dict


def init():
    global word_dict_count, word_dict, max_wordlen, all_freq
    trans_dict = {}  # 记录概率,2-gram
    word_dict_count = load_model(word_count_path)
    all_freq = sum(word_dict_count.values())  # 所有词的词频
    max_wordlen = max(len(key) for key in word_dict_count.keys())
    for key in word_dict_count:
        word_dict[key] = math.log(word_dict_count[key] / all_freq)
    # 计算转移概率
    Trans_dict = load_model(word_trans_path)
    for pre_word, post_info in Trans_dict.items():
        for post_word, count in post_info.items():
            word_pair = pre_word + ' ' + post_word
            trans_dict_count[word_pair] = float(count)
            if pre_word in word_dict_count.keys():
                trans_dict[key] = math.log(
                    count / word_dict_count[pre_word])  # 取自然对数，归一化
            else:
                trans_dict[key] = word_dict[post_word]


if __name__ == "__main__":
    init()
    TEMPLATE = "let %s* = %s\n"
    result = "import tables\n"
    result += "const allFreq* = %s\n" % all_freq
    result += "const maxWordLen* = %s\n" % max_wordlen

    result += TEMPLATE % ("wordProb",
                          json.dumps(word_dict, ensure_ascii=False,
                                     indent=2).replace("}", "}.newTable")

                          )
    result += TEMPLATE % ("wordFreq", json.dumps(word_dict_count, ensure_ascii=False, indent=2).replace("}", "}.newTable")

                          )
    result += TEMPLATE % ("transFreq",
                          json.dumps(trans_dict_count, ensure_ascii=False,
                                     indent=2).replace("}", "}.newTable")
                          )
    cleaned = ""
    punc = "[\"|\s][\uFF00-\uFFFF！？。＂＃$＄％&＆'＇（）＊＋，－／：；<＜＝>＞@［＿｀`｛|｜｝~～《》｟｠｢｣、〃「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…﹏]"
    # punc = "[\"|\s][\uFF00-\uFFFF]" 全角数字？
    
    for line in result.splitlines(keepends=True):
        if re.search(punc,line) :
            continue
        else:
            cleaned+=line

    with open(path.join(cur_dir, "..", "src", "maxnseg", "model.nim"), "w") as f:
        f.write(cleaned)
