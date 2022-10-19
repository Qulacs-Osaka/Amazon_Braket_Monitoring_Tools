from collections import defaultdict
from datetime import date, timedelta

import boto3  # type:ignore


class AmazonBraketlib:
    def __init__(self, region: str = "us-east-1"):
        """Initialize configuration of braket client and some data
        Args:
            region: The AWS Region
        """
        # store bucket name
        self.s3_bucket_name: list[str] = []
        # store folder name
        self.s3_bucket_folder_name: defaultdict = defaultdict(list)
        self.total_shots: dict[str, int] = {}
        self.s3_shot_count: dict[str, int] = {}
        self.s3_count_id: dict[str, list[str]] = {}
        self.target_name: list[str] = ["QUEUED", "COMPLETED", "CANCELLED", "RUNNING"]
        self.region: str = region
        self.braket = boto3.client("braket", region_name=self.region)

    def __calculate_shots_num(
        self,
        year: int,
        month: int,
        day: int,
        index_of_status_type: int,
        response: dict[str, dict],
        delta: timedelta,
    ) -> bool:
        """calculate the number of shots for each bucket

        Args:

        Returns:
            bool:
        """

        for task in response["quantumTasks"]:
            # Returns False if the data is not the given date
            if task["status"] == self.target_name[index_of_status_type] and task[
                "createdAt"
            ].date() == date(year, month, day):
                self.total_shots[self.target_name[index_of_status_type]] += task[
                    "shots"
                ]

                # output s3 information is like this
                # 'count': {'amazon-braket-issa': 8100,
                # 'amazon-braket-issa/boto-examples': 100,
                #  'amazon-braket-issa/task-check-example': 8000},

                # 新たなs3 bucketなら, appendしてやる
                if task["outputS3Bucket"] not in self.s3_bucket_name:
                    self.s3_bucket_name.append(task["outputS3Bucket"])
                    self.s3_shot_count[task["outputS3Bucket"]] = 0
                    self.s3_count_id[task["outputS3Bucket"]] = []
                # bucket内のshot数を加算
                self.s3_shot_count[task["outputS3Bucket"]] += task["shots"]
                # bucketに新たなtaskを加える
                self.s3_count_id[task["outputS3Bucket"]].append(task["quantumTaskArn"])
                # task result fileの格納フォルダ名
                self.s3_folder_name = list(task["outputS3Directory"].split("/"))[0]
                bucket_name = task["outputS3Bucket"] + "/" + self.s3_folder_name
                if (
                    self.s3_folder_name
                    not in self.s3_bucket_folder_name[task["outputS3Bucket"]]
                ):
                    self.s3_bucket_folder_name[task["outputS3Bucket"]].append(
                        self.s3_folder_name
                    )
                    self.s3_shot_count[bucket_name] = 0
                    self.s3_count_id[bucket_name] = []
                self.s3_shot_count[bucket_name] += task["shots"]
                self.s3_count_id[bucket_name].append(task["quantumTaskArn"])

            elif (date(year, month, day) - task["createdAt"].date() > delta) is True:
                return False
        return True

    def get_info(
        self,
        year: int,
        month: int,
        day: int,
        deviceArn: str,
        index_of_status_type: int,
    ) -> dict:
        """Get task information for a specific device on a specific date

        Args:
            year (int): year
            month (int): month
            day (int): day
            deviceArn (str):
            index_of_status_type (int):  index of status type(0:QUEUED,1:COMPLETED, 2:CANCELLED, 3:RUNNING)

        Returns:
        Task information in json-format string.

        """
        self.s3_bucket_name = []
        self.s3_bucket_folder_name = defaultdict(list)
        self.s3_shot_count = {}
        self.s3_count_id = {}
        self.total_shots = {}
        # 調べるstatusを指定
        target_status = self.target_name[index_of_status_type]
        # total_hosts_dicの初期化
        for I in self.target_name:
            self.total_shots[I] = 0
        # 指定した日付とタスクの日付の差の上限
        delta: timedelta = timedelta(seconds=24 * 60 * 60)
        # Array of SearchQuantumTasksFilter objects.
        own_filters = [
            {
                "name": "deviceArn",
                "operator": "EQUAL",
                "values": [deviceArn],
            },
        ]
        # search_quantum_tasksは, json形式のstrを返し, "nextToken":次のタスクのトークン と "quantumTasks":filterにマッチしたタスクのarrayオブジェクトが返される.
        # 1回目のnext_tokenはnullにしておく. すると先頭からsearchしてくれる.
        next_token: str = ""
        # taskが存在するかのフラグ
        has_next_token: bool = True

        # 再帰的にtaskを検索. 毎回maxResults分のタスクを取ってくる.
        while has_next_token:
            response = self.braket.search_quantum_tasks(
                filters=own_filters, maxResults=10, nextToken=next_token
            )
            print(response)
            if response["quantumTasks"] == []:
                has_next_token = False
                break
            has_next_token = self.__calculate_shots_num(
                year,
                month,
                day,
                index_of_status_type,
                response,
                delta,
            )

            # 次のtokenがないなら, 終了
            if has_next_token is True:
                # nextTokenは, 次のトークンがない場合nullであるため, もしnullだとresponse['nextToken']でエラーになる
                if "nextToken" in response:
                    next_token = response["nextToken"]
                else:
                    break
            else:
                break

        return {
            "id": self.s3_count_id,
            "count": self.s3_shot_count,
            "total_shots": self.total_shots[self.target_name[index_of_status_type]],
            "qpu": deviceArn,
            "status": target_status,
            "date": str(year) + "-" + str(month) + "-" + str(day),
        }

    def delete_quantumTask(self, quantumTaskArn_name: str) -> dict[str, dict]:
        """delete specific quantumTask
        Args:
            quantumTaskArn_name (_type_): _description_

        Returns:
            _type_: _description_
        """
        response = self.braket.cancel_quantum_task(quantumTaskArn=quantumTaskArn_name)
        return response
