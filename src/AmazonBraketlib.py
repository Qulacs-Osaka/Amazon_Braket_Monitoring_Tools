from email.policy import default
import boto3
from collections import defaultdict
from datetime import datetime, date, timedelta


class AmazonBraketlib:

    def __init__(self, region="us-east-1", clientToken=''):
        """Initialize configuration of braket client and some data
        Args:
            region: The AWS Region
            clientToken: client Token
        """
        # store bucket name
        self.s3_bucket_name_list = []
        # store folder name
        self.s3_bucket_folder_name_list = defaultdict(list)
        self.total_shots_dic = {}
        self.s3_shot_count_dic = {}
        self.s3_count_id = {}
        self.target_name = ['QUEUED', 'COMPLETED', 'CANCELLED', 'RUNNING']
        self.region = region
        self.clientToken = clientToken
        self.braket = boto3.client('braket', region_name=self.region)

    def message_maker(self, date, time, device, count):
        """Make a warning message

        Args:
            data:
            time:
            device:
            count:
        """
        message = "At "+str(date)+str(time)+" "+"I detected increaning by "+str(count)+"at "+device+". Please keep care."
        return message

    def make_markdown_from_list(self, str_time, target_list):
        """Make markdown-format string from target list

        Args:
            str_time (str): time
            target_list (str):

        Returns:
            _type_: _description_
        """
        res_str = ""
        res_str += str_time + "<br/>"
        res_str += " ".join(target_list) + "<br/>"
        return res_str

    def calculate_shots_num(self, year, month, day, device_type, device_provider, device_name, index_of_status_type, response, delta):
        """calculate the number of shots for each bucket

        Args:


        Returns:
            bool:
        """

        for task in response['quantumTasks']:
            # Returns False if the data is not the given date
            if task['status'] == self.target_name[index_of_status_type] and task['createdAt'].date() == date(year, month, day):
                self.total_shots_dic[self.target_name[index_of_status_type]] += task['shots']

                # output s3 information is like this
                # 'count': {'amazon-braket-issa': 8100,
                # 'amazon-braket-issa/boto-examples': 100,
                #  'amazon-braket-issa/task-check-example': 8000},

                # 新たなs3 bucketなら, appendしてやる
                if task['outputS3Bucket'] not in self.s3_bucket_name_list:
                    self.s3_bucket_name_list.append(task['outputS3Bucket'])
                    self.s3_shot_count_dic[task['outputS3Bucket']] = 0
                    self.s3_count_id[task['outputS3Bucket']] = []
                # bucket内のshot数を加算
                self.s3_shot_count_dic[task['outputS3Bucket']] += task['shots']
                # bucketに新たなtaskを加える
                self.s3_count_id[task['outputS3Bucket']].append(task['quantumTaskArn'])
                # task result fileの格納フォルダ名
                self.s3_folder_name = list(task['outputS3Directory'].split('/'))[0]
                bucket_name = task['outputS3Bucket']+'/'+self.s3_folder_name
                if self.s3_folder_name not in self.s3_bucket_folder_name_list[task['outputS3Bucket']]:
                    self.s3_bucket_folder_name_list[task['outputS3Bucket']].append(self.s3_folder_name)
                    self.s3_shot_count_dic[bucket_name] = 0
                    self.s3_count_id[bucket_name] = []
                self.s3_shot_count_dic[bucket_name] += task['shots']
                self.s3_count_id[bucket_name].append(task['quantumTaskArn'])
            elif (date(year, month, day) - task['createdAt'].date() > delta) == True:
                return False

    def get_info(self, year, month, day, device_type, device_provider, device_name, index_of_status_type):
        """Get task information for a specific device on a specific date

        Args:
            year (int): year
            month (int): month
            day (int): day
            device_type (str): device type (ex. 'qpu', 'qpu-simulator')
            device_provider (str): provider name (ex. amazon, d-wave, rigetti)
            device_name (str): device name (ex. Aspen-10, tn1)
            index_of_status_type (int):  index of status type(0:QUEUED,1:COMPLETED, 2:CANCELLED, 3:RUNNING)

        Returns:
        Task information in json-format string.

        """
        self.s3_bucket_name_list = []
        self.s3_bucket_folder_name_list = defaultdict(list)
        self.s3_shot_count_dic = {}
        self.s3_count_id = {}
        self.total_shots_dic = {}
        # 調べるstatusを指定
        target_status = self.target_name[index_of_status_type]
        # total_hosts_dicの初期化
        for I in self.target_name:
            self.total_shots_dic[I] = 0
        # 指定した日付とタスクの日付の差の上限
        delta = timedelta(seconds=60)
        # 調べるdeviceの名前を指定
        device_name = 'device'+'/'+device_type+'/'+device_provider+'/'+device_name
        # Array of SearchQuantumTasksFilter objects.
        own_filters = [
            {
                'name': 'deviceArn',
                'operator': 'EQUAL',
                'values': [
                    'arn:aws:braket:::'+device_name
                ]
            },
        ]
        # search_quantum_tasksは, json形式のstrを返し, "nextToken":次のタスクのトークン と "quantumTasks":filterにマッチしたタスクのarrayオブジェクトが返される.
        response = self.braket.search_quantum_tasks(
            filters=own_filters,
            maxResults=100
        )
        # 1回目のnext_tokenはnullにしておく. すると先頭からsearchしてくれる.
        next_token = ''
        # taskが存在するかのフラグ
        has_next_token = True

        # 再帰的にtaskを検索. 毎回maxResults分のタスクを取ってくる.
        while has_next_token:
            response = self.braket.search_quantum_tasks(
                filters=own_filters,
                maxResults=100,
                nextToken=next_token
            )
            has_next_token = self.calculate_shots_num(year, month, day, device_type, device_provider,
                                      device_name, index_of_status_type, response, delta)

            # 次のtokenがないなら, 終了
            if has_next_token == True:
                # nextTokenは, 次のトークンがない場合nullであるため, もしnullだとresponse['nextToken']でエラーになる
                if 'nextToken' in response:
                    next_token = response['nextToken']

        return {"id": self.s3_count_id,
                "count": self.s3_shot_count_dic, "total_shots": self.total_shots_dic[self.target_name[index_of_status_type]],
                "hardware": device_provider,
                "qpu": device_name, "status": target_status,
                'date': str(year)+'-'+str(month)+'-'+str(day)
                }

    def delete_quantumTask(self, quantumTaskArn_name):
        """delete specific quantumTask
        Args:
            quantumTaskArn_name (_type_): _description_

        Returns:
            _type_: _description_
        """
        response = self.braket.cancel_quantum_task(clientToken=self.clientToken, quantumTaskArn=quantumTaskArn_name)
        return response
