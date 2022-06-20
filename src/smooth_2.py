import imp
import math
import pickle
import re
import argparse

oneWordDist = {}
twoWordDist = {}
threeWordDist = {}
firstWordDist = {}
chi2num = {}
num2chi = {}
pyList = {}
pyCount = {}
wordcount = 6764
alpha = 0.999999
dataset = "pretrained_data_with_wikipedia"
testcase = "../data/input.txt"
outputfile = "../data/output.txt"

# 汉字转编号
def c2n(chr):
    tmp = 0
    if chr in chi2num:
        tmp = chi2num[chr]
    return tmp

# 编号转数字
def n2c(id):
    tmp = ""
    if id in num2chi:
        tmp = num2chi[id]
    return tmp

# 首字机率
def prob_fst(id):
    tmp = 1e-3
    if id in firstWordDist:
        tmp = firstWordDist[id]
    return tmp

# 单字机率
def prob_one(id):
    tmp = 1e-3
    if id in oneWordDist:
        tmp = oneWordDist[id]
    return tmp

# 双字机率
def prob_two(id1, id2):
    tmp = 1e-8
    id = id1 * wordcount + id2 
    if id in twoWordDist:
        tmp = twoWordDist[id]
    return tmp

# 拼音表
def get_py(target):
    if target in pyList:
        return pyList[target]
    return []

# 计算所有拼音的汉字出现总数
def count_py():
    for py in pyList:
        wordList = get_py(py)
        total = 0
        for letter in wordList:
            id = c2n(letter)
            total += prob_one(id) 
        pyCount[py] = total

# 对应拼音的汉字出现总数
def get_total(target):
    if target in pyCount:
        return pyCount[target]
    return 1000

def setup():
    global oneWordDist
    global twoWordDist
    global threeWordDist
    global firstWordDist
    global chi2num
    global num2chi
    global pyList

    # 汉字编码表
    inputFile = open("./" + dataset + "/hanzimap.txt", "rb")
    chi2num = pickle.load(inputFile)
    inputFile.close()

    # 汉字解码表
    inputFile = open("./" + dataset + "/hanzidecode.txt", "rb")
    num2chi = pickle.load(inputFile)
    inputFile.close()

    # 读入拼音表
    inputFile = open("./" + dataset + "/pinyinlist.txt", "rb")
    pyList = pickle.load(inputFile)
    inputFile.close()

    # 字符在句首出现的概率
    inputFile = open("./" + dataset + "/frequencyF.txt", "rb")
    firstWordDist = pickle.load(inputFile)
    inputFile.close()

    # 单个出现的概率
    inputFile = open("./" + dataset + "/frequency1.txt", "rb")
    oneWordDist = pickle.load(inputFile)
    inputFile.close()

    # 连续两个出现的概率
    inputFile = open("./" + dataset + "/frequency2.txt", "rb")
    twoWordDist = pickle.load(inputFile)
    inputFile.close()

    count_py()

def get_args():
    global dataset, testcase, outputfile
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", default="pretrained_data", help="选定语料库。可选值为：pretrained_data, pretrained_data_with_wikipedia")
    parser.add_argument("-if", "--inputfile", default="../data/input.txt", help="指定输入文件的位置")
    parser.add_argument("-of", "--outputfile", default="../data/output.txt", help="指定输出文件的位置")
    args = parser.parse_args()
    dataset = args.data
    testcase = args.inputfile
    outputfile = args.outputfile
    print("  Use corpus: " + dataset)
    print("  Input file: \"" + testcase + "\"")
    print("  Output file: \"" + outputfile + "\"")

def main():
    # 读入命令行参数
    get_args()

    # 初始化
    setup()
    
    # 读入测试数据
    inputFile = open(testcase, "r")
    outputFile = open(outputfile, "w")
    query = inputFile.readlines()

    # 按行为单位操作
    for line in query:

        # 按空格和换行符分开
        wordList = re.split(" |\n", line)

        dp = []
        item = {}

        # 根据第一个拼音寻找可能的汉字
        targetWord = get_py(wordList[0])
        total = get_total(wordList[0])

        # 遍历可行值，将该字出现在首位的概率记入 dp 数组中
        for letter in targetWord:
            id = c2n(letter)
            prob = (prob_fst(id) + prob_one(id) * prob_fst(0) / prob_one(0)) / total
            item[id] = {
                "value": prob,
                "word": -1,
            }

        dp.append(item)

        flag = False

        for i in range(len(wordList)):
            word = wordList[i]
            print(word, end=" ")

            # 首字符分开考虑
            if not flag:
                flag = True
                continue

            item = {}
            targetWord = get_py(word)
            total = get_total(wordList[i - 1])
            # 若拼音无对应单词，句子有误，不做操作
            if (len(targetWord) == 0):
                continue
            
            # 遍历可行值
            for letter in targetWord:
                id2 = c2n(letter)
                tmp = -1
                tarID = -1
                # 遍历上一层的所有汉字
                for id1 in dp[-1]:
                    value1 = dp[-1][id1]
                    # 计算两者同时出现的机率
                    prob1 = prob_two(id1, id2)
                    prob2 = prob_one(id1)
                    prob = alpha * prob1 / prob2 + (1 - alpha) * prob2 / total
                    # 若机率比现有值大，更新
                    if (value1["value"] * prob > tmp):
                        tmp = value1["value"] * prob # + prob
                        tarID = id1

                # 记录最大值和可以取到此值的上一位汉字
                item[id2] = {
                    "value": tmp,
                    "word": tarID
                }

            dp.append(item)

        nxtID = -1
        tarID = -1     
        tarProb = float('-inf')
        cnt = -1

        # 寻找末位机率最大者
        for id1 in dp[cnt]:
            value1 = dp[cnt][id1]
            if (value1["value"] > tarProb):
                tarID = id1
                tarProb = value1["value"]
                nxtID = value1["word"]

        # 得到最后一位
        ans = n2c(tarID)

        # 从后往前查找，直至找不到上一位汉字
        while nxtID != -1:
            ans = n2c(nxtID) + ans
            tarID = nxtID
            cnt -= 1         
            nxtID = dp[cnt][tarID]["word"]

        # 则结束
        print(ans)
        outputFile.write(ans + "\n")

    inputFile.close()
    outputFile.close()

if __name__ == "__main__":
    print("Running smooth_2.py ...")
    main()
    print("Finished running smooth_2.py")
    print()