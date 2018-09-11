# maxnseg
# Copyright zhoupeng
# A new awesome nimble package
import maxnseg/model
import math
import tables
import algorithm
import unicode
const
    MIN_FLOAT = BiggestFloat.low
# 估算未出现的词的概率,根据beautiful data里面的方法估算，平滑算法
# proc get_unknow_word_prob( word:string):BiggestFloat = 
#     try:
#         result = ln(1 / allFreq ^ runeLen(word))
#     except OverflowError:
#         result = MIN_FLOAT
#     if classify(result) == fcNan:
#         result = MIN_FLOAT
#     # elif result == NegInf:
#     #     result = MIN_FLOAT
#     echo result

# 获取候选词的概率
proc get_word_prob( word:string ):BiggestFloat = 
    result = wordProb.getOrDefault(word,MIN_FLOAT)

#获取转移概率
proc get_word_trans_prob( pre_word, post_word:string):BiggestFloat =
    var trans_word = pre_word & " " & post_word
    
    if transFreq.hasKey(trans_word):
        result = ln(transFreq[trans_word] / wordFreq[pre_word].toBiggestFloat)
    else:
        result = get_word_prob(post_word)

# 寻找node的最佳前驱节点，方法为寻找所有可能的前驱片段
proc get_best_pre_node( runes:seq[Rune], node:int, node_state_list:var seq[tuple[pre_node:int,prob_sum:BiggestFloat]]):tuple[pre_node:int,prob_sum:BiggestFloat]=
    # 如果node比最大词长小，取的片段长度以node的长度为限
    result.prob_sum = MIN_FLOAT
    var max_seg_length = min(node, maxWordLen)
    var pre_node_list:seq[tuple[pre_node:int,prob_sum:BiggestFloat]] = @[]  # 前驱节点列表
    var 
        segment_start_node:int
        segment:seq[Rune]
        pre_node:int
        segment_prob:BiggestFloat
        pre_pre_node:int
        pre_node_prob_sum:BiggestFloat
        candidate_prob_sum:BiggestFloat
        pre_pre_word:seq[Rune]
    # 获得所有的前驱片段，并记录累加概率
    for segment_length in 1..max_seg_length:
        segment_start_node = node - segment_length
        segment = runes[segment_start_node..<node]  # 获取片段
        pre_node = segment_start_node  # 取该片段，则记录对应的前驱节点
        if pre_node == 0:
            # 如果前驱片段开始节点是序列的开始节点，
            # 则概率为<S>转移到当前词的概率
            segment_prob = get_word_trans_prob("<BEG>", $segment)
        else:  # 如果不是序列开始节点，按照二元概率计算
            # 获得前驱片段的前一个词
            pre_pre_node = node_state_list[pre_node].pre_node
            pre_pre_word = runes[pre_pre_node..<pre_node]
            segment_prob = get_word_trans_prob($pre_pre_word, $segment)

        pre_node_prob_sum = node_state_list[pre_node].prob_sum  # 前驱节点的概率的累加值
        candidate_prob_sum = pre_node_prob_sum + segment_prob
        if candidate_prob_sum != NegInf and  candidate_prob_sum > result.prob_sum:
            result.prob_sum = candidate_prob_sum
            result.pre_node = pre_node
        # pre_node_list.add((pre_node:pre_node, prob_sum:candidate_prob_sum))

    # 找到最大的候选概率值
    # (best_pre_node, best_prob_sum) = max(pre_node_list, key=lambda d: d[1])

    # return best_pre_node, best_prob_sum

#切词主函数
proc cut*( sentence:string ):seq[string]=
    # sentence = sentence.strip()
    # 初始化
    let a = (pre_node: -1,prob_sum: 0.0)
    var node_state_list:seq[tuple[pre_node:int,prob_sum:BiggestFloat]] = @[a]  
    # 记录节点的最佳前驱，index就是位置信息
    # 初始节点，也就是0节点信息
   
    # 字符串概率为2元概率， P(a b c) = P(a|<S>)P(b|a)P(c|b)
    # 逐个节点寻找最佳前驱节点
    var 
        runes = sentence.toRunes()
        best_pre_node:int
        best_prob_sum:BiggestFloat
    for node in 1..runeLen(sentence):
        # 寻找最佳前驱，并记录当前最大的概率累加值
        (best_pre_node, best_prob_sum) = get_best_pre_node(runes, node, node_state_list)

        # 添加到队列
        node_state_list.add( (pre_node: best_pre_node,prob_sum: best_prob_sum) )
        # print "cur node list",node_state_list

    # step 2, 获得最优路径,从后到前
    var 
        best_path:seq[int] = @[]
        pre_node:int
        node = runeLen(sentence)  # 最后一个点
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
        word:seq[Rune]
    for i in 0..<len(best_path)-1:
        left = best_path[i]
        right = best_path[i + 1]
        word = runes[left..<right]
        result.add($word)
