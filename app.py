import requests
from flask import Flask, request,render_template
app = Flask(__name__)
import json
import time
from flask import  jsonify,request
@app.route('/', methods=['GET'])
def home():
    return render_template('home2.html')
@app.route('/getMessage',methods=['POST'])
def getMessage():
    dataInfo = request.get_json()
    tools = dataInfo["tools"]
    # for tool in tools:
    #     for i in range(0,len(tool["time_per_chips"])):
    #         tool["time_per_chips"][i]=decimal.Decimal(tool["time_per_chips"][i])
    flows=dataInfo["flows"]
    chipCount=dataInfo["chipCount"]
    chipList = []
    chipIndex = 0
    resultList = []
    allChipCount=0
    for productIndex, count in enumerate(chipCount):
        allChipCount=allChipCount+count
        chipProduct = []
        groupIndex = 0
        for i in range(1, count + 1):
            if i % 25 == 1:
                chipProduct.append([])
                groupIndex = groupIndex + 1
            chip = {}
            chipIndex = chipIndex + 1
            chip["productId"] = productIndex + 1
            chip["groupId"] = groupIndex
            chip["id"] = chipIndex
            chip["flowInfo"] = []  # {"flowIndex","wait_time","start_time","end_time","load_time"}
            chipProduct[-1].append(chip)
        chipList.append(chipProduct)
    for productList in chipList:
        for groupList in productList:
            for chip in groupList:
                chip["flowInfo"].append(
                    {
                        "flowIndex": 0,
                        "start_time": 0,
                        "end_time": 0,
                        "execute_consume_time": 0,
                    }
                )
                nowFlow = flows[chip["productId"] - 1][0]
                tools[nowFlow - 1]["waiting_area"].append(chip)
    addTime = 0.01
    nowTime = 0.00
    loadingTime = 5
    while len(resultList) < allChipCount:  # 当输出的长度小于chipList的长度,保持循环
        for tool in tools:  # 对每个工具循环
            if nowTime.is_integer():
                #work_time_log
                if len(tool["work_time_log"]) == 0:
                    tool["work_time_log"].append(0)
                else:
                    if len(tool["executing_area"]) > 0:
                        tool["work_time_log"].append(tool["work_time_log"][-1]+1)
                    else:
                        tool["work_time_log"].append(tool["work_time_log"][-1])
                #utlization
                if len(tool["utlization"])==0:
                    tool["utlization"].append(0)
                else:
                    tool["utlization"].append( tool["work_time_log"][-1]/nowTime)
                #waitareaCountChange
                tool["waitareaCountChange"].append(len(tool["waiting_area"]))
                #throughput
                if len(tool["throughput"])==0 or tool["work_time_log"][-1]==0:
                    tool["throughput"].append(0)
                else:
                    tool["throughput"].append(len(resultList)/tool["work_time_log"][-1])
            # 处理出队
            if len(tool["executing_area"]) > 0:  # 如果工作区长度大于0
                productIndex = tool["executing_area"][0]["productId"] - 1  # 获取产品
                # 增加对应流程的工作时间
                tool["executing_area"][0]["flowInfo"][-1]["execute_consume_time"] =round(tool["executing_area"][0]["flowInfo"][-1]["execute_consume_time"] + addTime,2)
                if tool["executing_area"][0]["flowInfo"][-1]["execute_consume_time"] >= tool["time_per_chips"][
                    productIndex]:  # 如果增加后的工作时间大于等于对应的时间,则出队
                    tool["executing_area"][0]["flowInfo"][-1]["end_time"] = nowTime
                    if nowTime>tool["endTime"]:
                        tool["endTime"]=nowTime
                    nowChip = tool["executing_area"].pop(0)
                    nextFlowIndex = nowChip["flowInfo"][-1]["flowIndex"] + 1
                    if len(flows[productIndex]) == nextFlowIndex:
                        resultList.append(nowChip)
                    else:
                        nowChip["flowInfo"].append(
                            {
                                "flowIndex": nextFlowIndex,
                                "start_time": 0,
                                "end_time": 0,
                                "execute_consume_time": 0,
                            }
                        )
                        if nowChip["productId"] not in tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"].keys():
                            tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"][nowChip["productId"]]={}
                        if nowChip["groupId"] not in tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"][nowChip["productId"]].keys():
                            tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"][nowChip["productId"]][nowChip["groupId"]]=[]
                        tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"][nowChip["productId"]][nowChip["groupId"]].append(nowChip)
                        if len(tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"][nowChip["productId"]][nowChip["groupId"]])==len(chipList[nowChip["productId"]-1][nowChip["groupId"]-1]):
                            while len(tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"][nowChip["productId"]][nowChip["groupId"]])>0:
                                loadingChip=tools[flows[productIndex][nextFlowIndex] - 1]["loading_area"][nowChip["productId"]][nowChip["groupId"]].pop(0)
                                tools[flows[productIndex][nextFlowIndex] - 1]["waiting_area"].append(loadingChip)
                        # tools[flows[productIndex][nextFlowIndex] - 1]["waiting_area"].append(nowChip)
            # 处理入队
            if len(tool["waiting_area"]) > 0:  # 如果等待区长度大于0
                if len(tool["executing_area"]) == 0:
                    tool["waiting_area"].sort(key=lambda x: x['id'])
                    nowChip = tool["waiting_area"].pop(0)
                    nowChip["flowInfo"][-1]["start_time"] = round(nowTime,2)
                    tool["executing_area"].append(nowChip)
                    if tool["startTime"]==0:
                        tool["startTime"]=nowTime
            tool["wait_count_log"].append(len(tool["waiting_area"]))
        nowTime = round(nowTime + addTime,2)  # 当前时间增加
    resultList.sort(key=lambda x: x['id'])
    toolResult={}
    toolResult["utlization"] = []
    toolResult["waitareaCountChange"]=[]
    toolResult["throughput"] = []
    utlizationAdd=0
    waitareaCountChangeMaxAdd=0
    throughputAdd = 0
    for tool in tools:
        #utlization
        valueList=[]
        for i in range(0,len(tool["utlization"])):
            if i<tool["startTime"] or i>tool["endTime"]:
                valueList.append(0)
            else:
                valueList.append(tool["utlization"][i])
        toolResult["utlization"].append({
            "name":tool["name"],
            "value":valueList
        })
        #waitareaCountChange
        utlizationAdd=utlizationAdd+1
        toolResult["waitareaCountChange"].append({
            "name":tool["name"],
            "value":[item+waitareaCountChangeMaxAdd for item in tool["waitareaCountChange"]]
        })
        waitareaCountChangeMaxAdd=waitareaCountChangeMaxAdd+max(tool["waitareaCountChange"])+10
        #throughput
        toolResult["throughput"].append({
            "name":tool["name"],
            "value":[item+throughputAdd for item in tool["throughput"]]
        })
        throughputAdd=throughputAdd+1
    return {"chipResultList":resultList,"toolResult":toolResult}
if __name__ == '__main__':
    app.run(debug=True)