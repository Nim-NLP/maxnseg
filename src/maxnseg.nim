# maxnseg
# Copyright zhoupeng
# A new awesome nimble package
import maxnseg/freq_prob
# import maxnseg/backward_gram
import math
import tables
import algorithm
import unicode
import memfiles
import regex
import strutils
import unicode
import unicodedb/scripts
import sequtils

const
    MIN_FLOAT = BiggestFloat.low

type PreNode = tuple[pre_node:int,prob_sum:BiggestFloat]

proc `<`(a,b:PreNode):bool =
    return a.prob_sum < b.prob_sum
var
    mm:MemFile

mm = memfiles.open("src/maxnseg/backward_gram.dict", mode = fmRead)
mm.close()
# 估算未出现的词的概率,根据beautiful data里面的方法估算，平滑算法
# proc get_unknow_word_prob( word:string):BiggestFloat = 
#     try:
#         result = ln(1 / allFreq ^ runeLen(word))
#     except OverflowError:
#         result = MIN_FLOAT
#     if classify(result) == fcNan:
#         result = MIN_FLOAT
    # elif result == NegInf:
    #     result = MIN_FLOAT
#     echo result

# 获取候选词的概率
proc get_word_prob( word:string ):BiggestFloat = 
    result = wordFreqProb.getOrDefault(word,[0.0,MIN_FLOAT])[1]

proc existInDict(q:string):tuple[a:bool,b:string]=
    for x in mm.lines:
        if x.startsWith(q):
            result[0] = true
            result[1] = x.substr(q.len - 1)
#获取转移概率
proc get_word_trans_prob( pre_word:string, post_word: string):BiggestFloat =
    result = get_word_prob(post_word)
    let q = existInDict(pre_word)
    if q[0]:
        var m: RegexMatch
        let i = q[1].find(post_word)
        if i != -1 :
            let a = q[1].substr(i)
            if a.find(re"(\d+)",m):
                result = ln(parseInt(a[m.group(0)[0]]).toBiggestFloat / wordFreqProb[pre_word][1])


# 寻找node的最佳前驱节点，方法为寻找所有可能的前驱片段
proc get_best_pre_node(sentence:string, runes:seq[Rune], node:int, node_state_list:var seq[PreNode]):PreNode=
    # 如果node比最大词长小，取的片段长度以node的长度为限
    result.prob_sum = MIN_FLOAT
    var max_seg_length = min(node, maxWordLen)
    var pre_node_list:seq[PreNode] = @[]  # 前驱节点列表
    var 
        segment_start_node:int
        # segment:seq[Rune]
        pre_node:int
        segment_prob:BiggestFloat
        pre_pre_node:int
        pre_node_prob_sum:BiggestFloat
        candidate_prob_sum:BiggestFloat
        pre_pre_word:string
        segmentStr:string
        right,left:int
    # 获得所有的前驱片段，并记录累加概率
    for segment_length in 1..max_seg_length:
        segment_start_node = node - segment_length
        right = sentence.runeOffset(node)
        left = sentence.runeOffset(segment_start_node)
        if right < 0:
            right = sentence.len
        segmentStr = sentence[left..<right]  # 获取片段
        pre_node = segment_start_node  # 取该片段，则记录对应的前驱节点
        if pre_node == 0:
            # 如果前驱片段开始节点是序列的开始节点，
            # 则概率为<S>转移到当前词的概率
            segment_prob =  get_word_trans_prob("<BEG>", segmentStr)
        else:  # 如果不是序列开始节点，按照二元概率计算
            # 获得前驱片段的前一个词
            right = sentence.runeOffset(pre_node)
            pre_pre_node = node_state_list[pre_node].pre_node
            left = sentence.runeOffset(pre_pre_node)
            if right < 0:
                right = sentence.len
            pre_pre_word = sentence[left..<right]
            segment_prob = get_word_trans_prob(pre_pre_word, segmentStr)
        pre_node_prob_sum = node_state_list[pre_node].prob_sum  # 前驱节点的概率的累加值
        candidate_prob_sum = pre_node_prob_sum + segment_prob
        pre_node_list.add((pre_node:pre_node, prob_sum:candidate_prob_sum))

    # 找到最大的候选概率值
    result = max(pre_node_list)

    # return best_pre_node, best_prob_sum

#切词主函数
proc internal_cut*( sentence:string ):seq[string]=
    # sentence = sentence.strip()
    # 初始化
    let a = (pre_node: -1,prob_sum: 0.0)
    var node_state_list:seq[PreNode] = @[a]  
    # 记录节点的最佳前驱，index就是位置信息
    # 初始节点，也就是0节点信息
   
    # 字符串概率为2元概率， P(a b c) = P(a|<S>)P(b|a)P(c|b)
    # 逐个节点寻找最佳前驱节点
    var 
        runes = sentence.toRunes()
        runesLen = runes.len
        best_pre_node:int
        best_prob_sum:BiggestFloat
    for node in 1..runesLen:
        # 寻找最佳前驱，并记录当前最大的概率累加值
        (best_pre_node, best_prob_sum) = get_best_pre_node(sentence,runes, node, node_state_list)
        # 添加到队列
        node_state_list.add( (pre_node: best_pre_node,prob_sum: best_prob_sum) )
        # print "cur node list",node_state_list
    # step 2, 获得最优路径,从后到前
    var 
        best_path:seq[int] = @[]
        pre_node:int
        node = runesLen  # 最后一个点
    best_path.add(node)
    while true:
        pre_node = node_state_list[node].pre_node
        if pre_node == -1:
            break
        node = pre_node
        best_path.add(node)
    best_path.reverse()
    # step 3, 构建切分
    var 
        left,right:int
        word:string
    for i in 0..<len(best_path)-1:
        left = best_path[i]
        right = best_path[i + 1]
        right = sentence.runeOffset(right)
        if right < 0:
            right = sentence.len
        word = sentence[sentence.runeOffset(left)..<right]
        result.add(word)

proc isHan(r: Rune): bool =
    # fast ascii check followed by unicode check
    result = r.int > 127 and r.unicodeScript() == sptHan
    
proc containsHan(s: string): bool =
  for r in s.runes:
    if r.isHan:
        result = true
        break

iterator splitHan(s: string): string =
  var
    i = 0
    j = 0
    k = 0
    r: Rune
    isHan = false
    isHanCurr = false
  fastRuneAt(s, i, r, false)
  isHanCurr = r.isHan()
  isHan = isHanCurr
  while i < s.len:
    while isHan == isHanCurr:
      k = i
      if i == s.len:
        break
      fastRuneAt(s, i, r, true)
      isHanCurr = r.isHan()
    yield s[j ..< k]
    j = k
    isHan = isHanCurr

const
    re_skip = re(r"([a-zA-Z0-9]+(?:\.\d+)?%?)")

iterator cut*(sentence: string):string  = 
    # if sentence.len > 0 and sentence.runeLen > 0:
    # var 
    #     wordStr:string
        # cuted:seq[string]
    for blk in splitHan(sentence):
        if blk.len == 0:
            continue
        if likely(containsHan(blk) == true):
            # internal_cut2(blk,cuted)
            for wordStr in internal_cut(blk):
                # wordStr = $word
                yield wordStr
               
        else:
            yield blk

proc lcut*(sentence:string):seq[string] {.noInit.} =
    if len(sentence) == 0 or sentence.runeLen == 0:
        result = @[]
    else:
        result = toSeq(cut(sentence))