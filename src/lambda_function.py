import boto3  # type:ignore
from datetime import datetime, date, timedelta
from AmazonBraketlib import AmazonBraketlib
import json
import urllib.request
from datetime import datetime

import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
today_date_int: list = [
    date.today().year, date.today().month, date.today().day]

#  task status ['QUEUED','COMPLETED','CANCELLED']


def lambda_handler(event, context: str):
    """Cancel all QUEUED tasks if total shots or cost is over the max value and send result message to the email.

    Args:
        event (_type_): event
        context (_type_): context

    Returns:
        (str): json-format string
    """
    SLACK_POST_URL = ""
    MAX_SHOT_NUM = 50
    MAX_SHOT_COST = 5  # dollar

    logger.info(event)
    # set boto user
    ama_us_west_1 = AmazonBraketlib("us-west-1")  # riggeti
    ama_us_west_2 = AmazonBraketlib("us-west-2")  # D-wave
    ama_us_east_1 = AmazonBraketlib("us-east-1")  # IonQ
    ama: list = [ama_us_west_1, ama_us_west_2, ama_us_east_1]

    today_date_int = [date.today().year, date.today().month, date.today().day]


    # device definition
    device_provider: list = ['d-wave', 'd-wave', 'ionq', 'rigetti']
    device_name: list = ['DW_2000Q_6',
                         'Advantage_system4', 'ionQdevice', 'Aspen-11']
    device_dict: dict = {}
    device_region_index_dict: dict = {'d-wave': 1, 'rigetti': 0, 'ionq': 2, 'DW_2000Q_6': 1,
                                      'Advantage_system4': 1, 'ionQdevice': 2, 'Aspen-11': 0}

    for provider, device in zip(device_provider, device_name):
        device_dict[provider] = device

    specific_device_provider: str = ''
    specific_device_name: str = ''
    for provider, device in zip(device_provider, device_name):
        if provider in event['detail']['deviceArn']:
            specific_device_provider = provider
            specific_device_name = device
            break


    shots_count_each_status: list = [0, 0, 0]
    task_count_each_status: list = [0, 0, 0]

    # store task results for each status to result dictionary
    task_info_each_status: list=[]
    result: dict = {}
    for task_status_index in range(3):
        result = ama[device_region_index_dict[specific_device_provider]].get_info(
            *today_date_int, 'qpu', specific_device_provider, specific_device_name, task_status_index)
        task_info_each_status.append(result)

        shots_count_each_status[task_status_index] += result['total_shots']

        if result['total_shots']:
            for id_name in result['id'].keys():
                if not '/' in id_name:
                    task_count_each_status[task_status_index] += len(
                        result['id'][id_name])


    # set output json string values
    lambda_output: dict = {}
    lambda_output['date'] = result['date']
    lambda_output['qpu'] = result['qpu']
    lambda_output['QUEUED_shot_count'] = shots_count_each_status[0]
    lambda_output['QUEUED_task_conut'] = task_count_each_status[0]
    lambda_output['COMPLETED_shot_count'] = shots_count_each_status[1]
    lambda_output['COMPLETED_task_count'] = task_count_each_status[1]
    lambda_output['CANCELLED_shot_count'] = shots_count_each_status[2]
    lambda_output['CANCELLED_task_count'] = task_count_each_status[2]

    # print(lambda_output)
    # print(price_each_status)



    device_type="qpu"
    deleted_result=delete_task_over_max_shot(
        MAX_SHOT_NUM, ama, device_region_index_dict, today_date_int, device_type, specific_device_provider,
        specific_device_name, shots_count_each_status, task_info_each_status)

    #send_email(lambda_output, TOPIC_ARN)
    post_slack(lambda_output,deleted_result, SLACK_POST_URL)

    return lambda_output


def delete_task_over_max_shot(
        max_shot_num, ama, device_region_index_dict, today_data_intyear, device_type, device_provider, device_name,shots_count_each_status,task_info_each_status):
    """delete QUEUED task according to the number of shots
    Args:
        max_shot_num :
        ama :
        device_region_index_dict :
        today_data_intyear :
        device_type :
        device_provider :
        device_name :

    Returns:
        result : TODO 削除したtask_id全て列挙
    """


    # for debug
    print(
        "\r" + str(datetime.now().time()) + ' QUEUED ' + str(shots_count_each_status[0]) + ' COMPLETED ' +
        str(shots_count_each_status[1]) +
        " CANCELLED " + str(shots_count_each_status[2]),
        end="")

    # 現在QUEUEDのshots合計が50以上なら, 全部のQUEUD taskを削除
    deleted_result = []
    if shots_count_each_status[0] >= max_shot_num:
        for bucket_name in task_info_each_status[0]['id']:
            # bucket_nameにはbucketとそのfolderの両方がtask_idsに代入されるため,
            # '/'があったら飛ばす(folderの中のtaskはとばす)
            if '/' not in bucket_name:
                for task_id in task_info_each_status[0]['id'][bucket_name]:
                    deleted_result.append(ama[device_region_index_dict[device_name]].delete_quantumTask(task_id))
        return deleted_result


def delete_task_over_max_cost(
        max_cost, ama, device_region_index_dict, today_data_intyear, device_type, device_provider, device_name, shots_count_each_status, task_info_each_status):
    """Delete QUEUD task accordingly when the maximum cost is exceeded
    Args:
        max_cost :
        ama :
        device_region_index_dict :
        today_data_intyear :
        device_type :
        device_provider :
        device_name :
    Returns:
        result : 削除したtask_id 全列挙
    """

    # TODO
    # price definition
    price_per_task: float = 0.3
    price_table: dict = {'d-wave': 0.00019, 'ionq': 0.01, 'rigetti': 0.00035}
    price_each_status_index: dict = {
        'QUEUED': 0, 'COMPLETED': 1, 'CANCELLED': 2}
    price_each_status: list = [0]*len(price_each_status_index)

    # Calculate the total cost of each state
    for price_status in price_each_status_index:
        price_each_status[price_each_status_index[price_status]] = \
            shots_count_each_status[price_each_status_index[price_status]] * \
            price_table[device_provider] + \
            task_count_each_status[price_each_status_index[price_status]]*price_per_task

    print(
        "\r" + str(datetime.now().time()) + ' QUEUED ' + str(price_each_status[0]) + ' COMPLETED ' +
        str(price_each_status[1]) +
        " CANCELLED " + str(price_each_status[2]),
        end="")

    # 現在QUEUEDのshots合計が50以上なら, 全部のQUEUD taskを削除
    deleted_result = []
    if price_each_status[0] >= max_cost:
        for bucket_name in task_info_each_status[0]['id']:
            # bucket_nameにはbucketとそのfolderの両方がtask_idsに代入されるため,
            # '/'があったら飛ばす(folderの中のtaskはとばす)
            if '/' not in bucket_name:
                for task_id in task_info_each_status[0]['id'][bucket_name]:
                    deleted_result.append(ama[device_region_index_dict[device_name]].delete_quantumTask(task_id))
    return deleted_result


def send_email(lambda_output,TOPIC_ARN):
    client = boto3.client('sns')
    msg = str(lambda_output)
    subject: str = 'Braket Monitor'
    response = client.publish(
        TopicArn=TOPIC_ARN,
        Message=msg,
        Subject=subject
    )

def post_slack(lambda_output,deleted_result,slack_post_url):

    # 設定

    username = "speed"
    icom = ":sunglasses:"
    channnel = '#general'
    method = "POST"

    # メッセージの内容
    now = datetime.now()
    current_time = now.strftime("%Y/%m/%d %H:%M:%S")
    operation_message = "Task Information" + " " + current_time + "\n"
    detail_info = str(lambda_output)
    delete_message="delete task result\n"+str(deleted_result)
    message =operation_message + detail_info+"\n"+delete_message
    send_data = {
        "username": username,
        "icon_emoji": icom,
        "text": message,
        "channel": channnel
    }

    send_text = ("payload=" + json.dumps(send_data)).encode('utf-8')

    request = urllib.request.Request(
        slack_post_url,
        data=send_text,
        method=method
    )
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode('utf-8')

    return response_body

