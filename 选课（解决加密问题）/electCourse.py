import json
import time
import requests
import base64
import hashlib
import urllib.parse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
# 学号，需要修改
student_id=''
# 浏览器内查看的sessionid，需要修改（填充）14c
cookies={"sessionid":""}
# 需要捡漏的课程，需要修改（填充），下面是一个例子
target_teachClassCode={'32000428','32000473','32000411','32000432'}


# 需要修改round_id和calendarId，请自行查看
round_id='5343'
electUrl = 'https://1.tongji.edu.cn/api/electionservice/student/elect'
electResUrl = 'https://1.tongji.edu.cn/api/electionservice/student/5343/electRes'

# 体育课选择接口，需要修改，从浏览器开发者模式获取接口,需要修改round_id和calendarId，请自行查看
getTeachClass4Limit='https://1.tongji.edu.cn/api/electionservice/student/getTeachClass4Limit?roundId=5343&courseCode=320004&studentId='+student_id+'&calendarId=116'


def get_course_elect_secret():
  url = "https://www.gardilily.com/oneDotTongji/courseElectSecret.php"

  try:
    response = requests.get(url)
    if response.status_code != 200:
      return None

    json_data = response.json()
    return {
      'key': json_data['key'],
      'iv': json_data['iv']
    }

  except Exception as e:
    print(f"发生错误: {e}")
    return None
# AES Encryption
def encrypt_aes_cbc(input_data, key, iv):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()

    padded_data = padder.update(input_data.encode()) + padder.finalize()
    return encryptor.update(padded_data) + encryptor.finalize()

def encrypt_data(student_id, course_code, teach_class_id, calendar_id, timestamp, payload_json):
  secret = get_course_elect_secret()
  if secret:
    secret_key = secret['key'].encode()
    iv = secret['iv'].encode()
  # Concatenating elements
  elements_plus = f"{student_id}+{course_code}+{teach_class_id}+{calendar_id}+{timestamp}+{payload_json}"
  elements_and = f"{student_id}&{course_code}&{teach_class_id}&{calendar_id}&{timestamp}&{payload_json}"
  # MD5 Hash
  md5_hash = hashlib.md5(elements_plus.encode()).hexdigest()
  # Encrypt and encode
  encrypted_data = encrypt_aes_cbc(urllib.parse.quote(elements_and), secret_key, iv)
  encoded_data = base64.b64encode(encrypted_data).decode()
  # URL encode the base64 encoded encrypted data
  cipher_url_encoded = urllib.parse.quote(encoded_data)
  # Final JSON Object
  encrypted_json_str = {
    "checkCode": md5_hash,
    "ciphertext": cipher_url_encoded
  }
  return encrypted_json_str  # 这是加密后的 JSON 字符串


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
    # 在这里加入加密逻辑
    encrypted_data = encrypt_data(
      self.student_id,
      data['elecClassList'][0]['courseCode'],
      data['elecClassList'][0]['teachClassId'],
      '116',  # 假设 calendar_id 是 116，自行修改
      str(int(time.time() * 1000)),  # 当前时间戳
      json.dumps(data)  # 转换为 JSON 字符串
    )
    # 发送加密的数据
    res = requests.post(electUrl, cookies=self.cookies, data=encrypted_data)
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
        payload={'roundId':5343,'elecClassList':[{"teachClassId":one['teachClassId'],"teachClassCode":one
        ['teachClassCode'],"courseCode":one['courseCode'],"courseName":one['courseName'],"teacherName":one
        ['teacherName']}],"withdrawClassList":[]}# 需要修改round_id，请自行查看
        self.chooseAClass(payload,{'value':one['times'][0]['value']})
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

