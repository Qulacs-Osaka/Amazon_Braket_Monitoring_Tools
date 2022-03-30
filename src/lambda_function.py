import boto3
from datetime import datetime, date, timedelta
from AmazonBraketlib import AmazonBraketlib
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#  task status ['QUEUED','COMPLETED','CANCELLED']

def lambda_handler(event, context):
    """Cancel all QUEUED tasks if total shots or cost is over the max value and send result message to the email.

    Args:
        event (_type_): event
        context (_type_): context

    Returns:
        (str): json-format string
    """
    
    TOPIC_ARN = ""
    MAX_SHOT_NUM=50
    MAX_SHOT_COST=5 # dollar

    logger.info(event)
    # set boto user
    ama_us_west_1 = AmazonBraketlib('us-west-1')  # riggeti
    ama_us_west_2 = AmazonBraketlib('us-west-2')  # D-wave
    ama_us_east_1 = AmazonBraketlib('us-east-1')  # IonQ
    ama = [ama_us_west_1, ama_us_west_2, ama_us_east_1]

    # price definition
    price_per_task = 0.3
    price_table = {'d-wave': 0.00019, 'ionq': 0.01, 'rigetti': 0.00035}

    # device definition
    device_provider = ['d-wave', 'd-wave', 'ionq', 'rigetti']
    device_name = ['DW_2000Q_6', 'Advantage_system4', 'ionQdevice', 'Aspen-11']
    device_dict = {}
    device_region_index_dict = {'d-wave': 1, 'rigetti': 0, 'ionq': 2, 'DW_2000Q_6': 1,
                'Advantage_system4': 2, 'ionQdevice': 1, 'Aspen-11': 0}

    for provider,device in zip(device_provider, device_name):
        device_dict[provider] = device

    specific_device_provider=''
    specific_device_name=''
    for provider, device in zip(device_provider, device_name):
        if provider in event['detail']['deviceArn']:
            specific_device_provider = provider
            specific_device_name = device
            break

    price_each_status = {}
    shots_count_each_status = [0, 0, 0]
    task_count_each_status = [0, 0, 0]

    result=''
    for task_status_index in range(3):
        result = ama[device_region_index_dict[specific_device_provider]].get_info(*today_date_int, 'qpu', specific_device_provider, specific_device_name, task_status_index)

        shots_count_each_status[task_status_index] += result['total_shots']
        if result['total_shots']:
            for id_name in result['id'].keys():
                if not '/' in id_name:
                    task_count_each_status[task_status_index] += len(result['id'][id_name])

    # Calculate the total cost of each state
    price_each_status['QUEUED'] = shots_count_each_status[0] * \
        price_table[specific_device_provider]+task_count_each_status[0]*price_per_task
    price_each_status['COMPLETED'] = shots_count_each_status[1]*price_table[specific_device_provider]+task_count_each_status[1]*price_per_task
    price_each_status['CANCELLED'] = shots_count_each_status[2] * \
        price_table[specific_device_provider]+task_count_each_status[2]*price_per_task

    # set output json string values
    lambda_output = {}
    lambda_output['date'] = result['date']
    lambda_output['qpu'] = result['qpu']
    lambda_output['QUEUED_shot_count'] = shots_count_each_status[0]
    lambda_output['QUEUED_task_conut'] = task_count_each_status[0]
    lambda_output['COMPLETED_shot_count'] = shots_count_each_status[1]
    lambda_output['COMPLETED_task_count'] = task_count_each_status[1]
    lambda_output['CANCELLED_shot_count'] = shots_count_each_status[2]
    lambda_output['CANCELLED_task_count'] = task_count_each_status[2]

    #print(lambda_output)
    #print(price_each_status)

    client = boto3.client('sns')
    msg = str(lambda_output)
    subject = 'Braket Monitor'
    response = client.publish(
        TopicArn=TOPIC_ARN,
        Message=msg,
        Subject=subject
    )

    return lambda_output


def delete_task_over_max_shot(
        max_shot_num, ama, device_region_index_dict,today_data_intyear, device_type, device_provider, device_name, index_of_status_type):
    """delete QUEUED task according to the number of shots
    Args:
        max_shot_num :
        ama :
        device_region_index_dict :
        today_data_intyear :
        device_type :
        device_provider :
        device_name :
        index_of_status_type :

    Returns:
        result : TODO　削除したtask_id全て列挙
    """
    task_info_list_each_status = []
    num_of_shots_each_status= [0, 0, 0]
    num_of_completed_shots = 0

    for task_status_index in range(3):
        task_info = ama[device_region_index_dict[device_provider]].get_info(
            *today_date_int, 'qpu', device_provider,device_name, index_of_status_type)

        task_info_list_each_status.append(task_info)
        num_of_shots_each_status[i] += task_info['total_shots']

    # for debug
    print(
        "\r" + str(datetime.now().time()) + ' QUEUED ' + str(num_of_shots_each_status[0]) + ' COMPLETED ' +
        str(num_of_shots_each_status[1]) + " CANCELLED " + str(num_of_shots_each_status[2]),
        end="")


    # 現在QUEUEDのshots合計が50以上なら, 全部のQUEUD taskを削除
    if sum(num_of_shots_each_status[0]) >= max_shot_num:
        for bucket_name in task_info_list_each_status[0]['id']:
            # bucket_nameにはbucketとそのfolderの両方がtask_idsに代入されるため,
            # '/'があったら飛ばす(folderの中のtaskはとばす)
            if '/' not in bucket_name:
                for task_id in task_info_list_each_status[0]['id'][bucket_name]:
                    ama[device_region_index_dict[specific_device_name]].delete_quantumTask(task_id)


def delete_task_over_max_cost(
        max_cost,ama, device_region_index_dict, today_data_intyear, device_type, device_provider, device_name,
        index_of_status_type):
    """Delete QUEUD task accordingly when the maximum cost is exceeded
    Args:
        max_cost :
        ama :
        device_region_index_dict :
        today_data_intyear :
        device_type :
        device_provider :
        device_name :
        index_of_status_type :
    Returns:
        result : 削除したtask_id 全列挙
    """

    # TODO

