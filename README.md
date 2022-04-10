# Amazon_Braket_Monitoring_Tools
Tools to monitor Amazon Braket

このリポジトリはAmazon Braketを利用する上でのタスク監視、削除の支援ツールのコード置き場です。

## AmazonBraketlib class
Braket taskを監視・削除する基本メソッドが含まれたクラス.

AmazonBraketlibの主なメソッド

- get_info(year, month, day, device_type, device_provider, device_name, index_of_status_type)
指定した日付の指定したデバイスのタスクに関する情報をjson形式で出力する.
出力されるjson文字列の例は以下の通り
```
{"id": self.s3_count_id,
    "count": self.s3_shot_count_dic, "total_shots": self.total_shots_dic[self.target_name[index_of_status_type]],
    "hardware": device_provider,
    "qpu": device_name, "status": target_status,
    'date': str(year)+'-'+str(month)+'-'+str(day)
    }
```

- delete_quantumTask(quantumTaskArn_name)

QUEUED状態の指定したタスクをキャンセルできる.
## lambda_fucntion.py
このlambda関数は, braketに投げられたQUEUED状態のTaskをイベントソースとし, 同日に投げられたQUEUED状態のtaskの総shot数またはshot数によって発生する総金額が, あらかじめ指定した上限を超えたら, QUEUED状態のTaskを全てCANCELLEDにする関数です.
結果はslackに通知します.
slackの設定方法は[こちら](https://www.takapy.work/entry/2019/02/20/140751)
を参照してください.

また, SLACK_POST_URLをAWS Lambdaの環境変数に設定してください.

- delete_task_over_max_shot()
shot数に応じてtaskを消去するlambda関数
- delete_task_over_max_cost()
金額に応じてtaskを消去するlambda関数



## Example
### shot.py

実行すると簡易なタスクを投げることができる。確認用。

### tutorial.ipynb
手元でAmazonBraketLib を実行するチュートリアルコード

## コンテナ環境

本リポジトリのDockerfile, docker-compose.ymlで作成されるコンテナは, AWSのconfig, credentialsファイルが含まれる ~/.aws/ と Amazon_Braket_Monitoring_Tools/src/ をvolumeで共有しています.
詳しくは[aws-notebook-docker-env](https://github.com/speed1313/aws-notebook-docker-env)を参照してください.

- コンテナ立ち上げ and login 方法
```
~/Amazon_Braket_Monitoring_Tools$ docker-compose up --build
$ docker exec -it  [コンテナ名] /bin/bash
```

詳細な設定方法は以下のドキュメントを参照してください。
https://braketmonitor-document.s3.ap-northeast-1.amazonaws.com/index.html



### AWS Braket jupyter notebook Docker環境はこちら

