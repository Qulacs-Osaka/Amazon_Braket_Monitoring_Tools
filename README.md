# Amazon_Braket_Monitoring_Tools
Tools to monitor Amazon Braket

このリポジトリはAmazon Braketを利用する上でのタスク監視、削除の支援ツールのコード置き場です。

## AmazonBraketlib class
Braket taskを監視・削除する基本メソッドが含まれたクラス.

### AmazonBraketlibの主なメソッド
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

shot数に応じてtaskを消去するlambda関数
## lambda_function_money.py

金額に応じてtaskを消去するlambda関数
### shot.py
実行すると簡易なタスクを投げることができる。確認用。

### tutorial.ipynb
手元でAmazonBraketLib を実行するチュートリアルコード

詳細な設定方法はいかのドキュメントを参照してください。
https://braketmonitor-document.s3.ap-northeast-1.amazonaws.com/index.html
