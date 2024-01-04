from selenium.webdriver import Edge
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import requests
import json
import base64
import hashlib
import urllib.parse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# 获取 sessionid 的函数
def get_sessionid():
    driver = Edge()

    # 打开登录页面
    login_url = "https://1.tongji.edu.cn"  # 登录 URL
    driver.get(login_url)

    # 等待页面加载
    time.sleep(5)

    # 定位用户名和密码输入框，并输入登录信息
    username = driver.find_element(By.ID, "j_username")
    password = driver.find_element(By.ID, "j_password")
    # 一系统自己的账密
    username.send_keys("")
    password.send_keys("")

    # 定位登录按钮并点击
    login_button = driver.find_element(By.ID, "loginButton")
    login_button.click()

    # 等待登录过程
    time.sleep(3)

    # 提取 sessionid
    cookies = driver.get_cookies()
    sessionid = next((cookie['value'] for cookie in cookies if cookie['name'] == 'sessionid'), None)

    # 关闭浏览器
    driver.quit()

    return sessionid

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
    self.student_id = ''# 填自己的学号
    self.cookies = {"sessionid": get_sessionid()}
    self.target_teachClassCode = {'32000428', '32000473', '32000411', '32000432'}# 一个例子，根据需要更改
    self.all_PEclass = {}
    self.round_id = '5343'# 需要按自己的更改
    self.electUrl = 'https://1.tongji.edu.cn/api/electionservice/student/elect'
    self.electResUrl = f'https://1.tongji.edu.cn/api/electionservice/student/{self.round_id}/electRes'
    # 需要按自己的更改
    self.getTeachClass4Limit = f'https://1.tongji.edu.cn/api/electionservice/student/getTeachClass4Limit?roundId={self.round_id}&courseCode=320004&studentId={self.student_id}&calendarId=116'

  def getAllPE(self):
    # 请求所有的体育课
    res=requests.post(self.getTeachClass4Limit,cookies=self.cookies)
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
      '116',  # 假设 calendar_id 是 116
      str(int(time.time() * 1000)),  # 当前时间戳
      json.dumps(data)  # 转换为 JSON 字符串
    )
    # 发送加密的数据
    res = requests.post(self.electUrl, cookies=self.cookies, data=encrypted_data)
    if res.status_code==200:
      print('[INFO]send success')
    else:
      print(res.text)

    # 循环等待直到状态变为 Ready
    while True:
      time.sleep(2)  # 等待一段时间再次检查状态
      res = requests.post(self.electResUrl, cookies=self.cookies)
      if res.status_code != 200:
        print('[ERROR]请求失败: 状态码:', res.status_code)
        print('[ERROR]响应内容:', res.text)
        return

      try:
        resJson = json.loads(res.text)
      except json.JSONDecodeError as e:
        print('[ERROR]解析 JSON 失败:', e)
        print('[ERROR]响应内容:', res.text)
        return

      # 检查状态
      if resJson['data']['status'] == 'Ready':
        # 检查选课结果
        if resJson['data']['failedReasons'] == {}:
          print('成功 Congratulation! 你选上了')
          exit('选课结束，退出')
        else:
          print('[INFO]失败', resJson['data']['failedReasons'])
        break
      elif resJson['data']['status'] == 'Processing':
        print('[INFO]选课正在处理中')
      else:
        print('[INFO]未知状态:', resJson['data']['status'])
        break

  # 开始请求
  def requestPE(self):
    # 根据课程序号生成对应的请求体
    for one in self.all_PEclass:
      if one['teachClassCode'] in self.target_teachClassCode:
        payload={'roundId':5343,'elecClassList':[{"teachClassId":one['teachClassId'],"teachClassCode":one
        ['teachClassCode'],"courseCode":one['courseCode'],"courseName":one['courseName'],"teacherName":one
        ['teacherName']}],"withdrawClassList":[]}
        self.chooseAClass(payload,{'value':one['times'][0]['value']})
        print()

  def refresh_session(self):
    # 每25轮刷新一次 sessionid
    self.cookies = {"sessionid": get_sessionid()}

if __name__=='__main__':
  a=SelectClass()
  a.getAllPE()
  i=1
  while True:
    if i % 25 == 0:
      a.refresh_session()
    time.sleep(1)
    print(f'第{i}轮申请课程')
    a.requestPE()
    i += 1

