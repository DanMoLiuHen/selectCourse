import json
import time
import requests
# 学号，需要修改
student_id='2051912'
# 浏览器内查看的sessionid，需要修改（填充）14c
cookies={"sessionid":"ccb65c86b61946f2991c2e618be0cfd8"}
# 需要捡漏的课程，需要修改（填充）
target_teachClassCode={'42036102'}


# 一般不用修改
round_id='5276'
electUrl = 'https://1.tongji.edu.cn/api/electionservice/student/elect'
electResUrl = 'https://1.tongji.edu.cn/api/electionservice/student/5276/electRes'

# 体育课选择接口，需要修改，从浏览器开发者模式获取接口
# getTeachClass4Limit='https://1.tongji.edu.cn/api/electionservice/student/getTeachClass4Limit?roundId=5276&courseCode=420361&studentId='+student_id+'&calendarId=115'
getTeachClass4Limit='https://1.tongji.edu.cn/api/electionservice/student/getTeachClass4Limit?roundId=5276&courseCode=320004&studentId='+student_id+'&calendarId=115'

class SelectClass():
  def __init__(self):
    self.student_id=student_id
    self.cookies=cookies
    self.target_teachClassCode=target_teachClassCode
    self.all_PEclass={}

  def getAllPE(self):  
    # 请求所有的体育课
    res=requests.post(getTeachClass4Limit,cookies=cookies)
    if res.status_code==200:
      self.all_PEclass= json.loads(res.text)['data']
    else:
      print('请求失败，请检查sessionid等信息，程序已退出')
      exit()

  # 请求一个课程
  def chooseAClass(self,data,class_information):
    print('[INFO]开始请求 '+class_information['value']+' 课程')
    # 发送请求
    res=requests.post(electUrl,cookies=cookies,json=data)
    if res.status_code==200:
      print('[INFO]send success')
    else:
      print(res.text)
    time.sleep(3)
    # 接收响应
    res = requests.post(electResUrl, cookies=cookies)
    resJson = json.loads(res.text)
    if res.status_code==200:
      # 如果接收响应成功查看结果，是否选上
      if resJson['data']['failedReasons']=={}:
        print('成功 Congratulation! 你选上了')
        exit('选课结束，退出')
      else:
        try:
          print('[INFO]失败',resJson['data']['failedReasons'])
        except:
          print(resJson)

  # 开始请求
  def requestPE(self):
    # 根据课程序号生成对应的请求体
    for one in self.all_PEclass:
      if one['teachClassCode'] in target_teachClassCode:
        paylaod={'roundId':5276,'elecClassList':[{"teachClassId":one['teachClassId'],"teachClassCode":one['teachClassCode'],"courseCode":one['courseCode'],"courseName":one['courseName'],"teacherName":one['teacherName']}],"withdrawClassList":[]}
        self.chooseAClass(paylaod,{'value':one['times'][0]['value']})
        print()

if __name__=='__main__':
  a=SelectClass()
  a.getAllPE()
  i=1
  while(1):
    time.sleep(1)
    print('第'+str(i)+'轮申请课程')
    a.requestPE()
    i+=1

