import json
import os
from time import sleep

import boto3
from boto3.session import Session
from collections import defaultdict
from datetime import datetime, date, timedelta
from AmazonBraketlib import AmazonBraketlib
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(event)

    now_time = datetime.now()

    now_month = str(now_time.date().month)
    now_date = str(now_time.date())

    prev_time = datetime.now().date()
    today = datetime.now().date()
    today_date = str(prev_time).split('-')
    today_date_int = []
    now_date = str(datetime.now().date())s
    for i in today_date:
        today_date_int.append(int(i))

    ama_us_west_1 = AmazonBraketlib('us-west-1', 'SECRET_KEY')  # riggeti
    ama_us_west_2 = AmazonBraketlib('us-west-2', 'SECRET_KEY')  # D-wave
    ama_us_east_1 = AmazonBraketlib('us-east-1', 'SECRET_KEY')  # IonQ

    ama = [ama_us_west_1, ama_us_west_2, ama_us_east_1]

    delta_day = timedelta(days=1)
    prev_time = datetime.now() - delta_day
    now_date = str(datetime.now().date())
    now_time = datetime.now()
    que = []

    time_index = datetime.now().time()

    # price

    price_per_task = 0.3
    price_table = {'d-wave': 0.00019, 'ionq': 0.01, 'rigetti': 0.00035}

    cols = ['hardware', 'qpu', 'status', 'id', 'count', 'total_shots']
    d_m = ['d-wave', 'd-wave', 'ionq', 'rigetti']
    d_e = ['DW_2000Q_6', 'Advantage_system4', 'ionQdevice', 'Aspen-11']
    device_dict = {}

    ama_dict = {'d-wave': 1, 'rigetti': 0, 'ionq': 2, 'DW_2000Q_6': 1,
                'Advantage_system4': 2, 'ionQdevice': 1, 'Aspen-11': 0}

    for i, j in zip(d_m, d_e):
        device_dict[j] = i

    def get_sigle_device(device, state_number):
        tmp_res = ama[ama_dict[device]].get_info(*today_date_int, 'qpu', device_dict[device], device, state_number)
        return tmp_res

    d_m = ['d-wave', 'd-wave', 'ionq', 'rigetti']
    d_e = ['DW_2000Q_6', 'Advantage_system4', 'ionQdevice', 'Aspen-11']

    target_name = ['QUEUED', 'COMPLETED', 'CANCELLED']

    c = 0
    cols = ['hardware', 'qpu', 'status', 'id', 'count', 'total_shots']

    total_shots_dict = {}
    total_shots_dict_v = {}

    price_dict = {}

    for momo, eoeo in zip(d_m, d_e):
        # print(momo,eoeo)
        if momo in event['detail']['deviceArn']:
            m = momo
            e = eoeo
            break

    tmp_dict = {}
    price_tmp_dict = {}
    c += 1

    all_state_dict = {}
    all_shots_list = [0, 0, 0]
    all_task_count_list = [0, 0, 0]
    all_shots = 0
    for i in range(3):
        tmp_res = ama[ama_dict[m]].get_info(*today_date_int, 'qpu', m, e, i)

        all_state_dict[time_index] = tmp_res
        all_shots += tmp_res['total_shots']
        all_shots_list[i] += tmp_res['total_shots']
        if tmp_res['total_shots']:
            for id_name in tmp_res['id'].keys():
                if not '/' in id_name:
                    all_task_count_list[i] += len(tmp_res['id'][id_name])

        tmp_res['device'] = e
    total_shots_dict[tmp_res['device']] = all_shots_list[0]+all_shots_list[1]
    total_shots_dict_v[tmp_res['device']] = all_shots_list[0]

    new_dict = {}
    new_dict['date'] = tmp_res['date']
    new_dict['qpu'] = tmp_res['qpu']
    new_dict['QUEUED_counts'] = all_shots_list[0]
    new_dict['QUEUED_task_counts'] = all_task_count_list[0]

    price_tmp_dict['QUEUED'] = all_shots_list[0]*price_table[m]+all_task_count_list[0]*price_per_task

    new_dict['COMPLETED_counts'] = all_shots_list[1]
    new_dict['COMPLETED_task_counts'] = all_task_count_list[1]

    price_tmp_dict['COMPLETED'] = all_shots_list[1]*price_table[m]+all_task_count_list[1]*price_per_task

    new_dict['CANCELLED_counts'] = all_shots_list[2]
    new_dict['CANCELLED_task_counts'] = all_task_count_list[2]

    price_tmp_dict['CANCELLED'] = all_shots_list[2]*price_table[m]+all_task_count_list[2]*price_per_task

    print(new_dict)

    device = e
    tmp_array = []
    total_shots_que_comp = [0, 0]
    can_sum = 0
    for i in range(3):
        tmp_list = [get_sigle_device(device, i)]
        if i != 2:
            total_shots_que_comp[i] += tmp_list[0]['total_shots']
        else:
            can_sum += tmp_list[0]['total_shots']
        tmp_array.append(tmp_list)

    print(price_tmp_dict)
    client = boto3.client('sns')

    msg = str(new_dict)
    subject = 'Braket Monitor'
    TOPIC_ARN = 'TOPIC_EXAPMLE'

    response = client.publish(
        TopicArn=TOPIC_ARN,
        Message=msg,
        Subject=subject
    )

    return new_dict
