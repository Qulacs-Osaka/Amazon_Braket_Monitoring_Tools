import boto3  # type:ignore
from datetime import datetime, date
from AmazonBraketlib import AmazonBraketlib
import json
import urllib.request
from datetime import datetime

import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

#  task status ['QUEUED','COMPLETED','CANCELLED']


def lambda_handler(event: dict, context: dict) -> dict:
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
    clients: list = [ama_us_west_1, ama_us_west_2, ama_us_east_1]

    # device definition
    device_providers: list[str] = ["d-wave", "d-wave", "ionq", "rigetti"]
    device_names: list[str] = [
        "DW_2000Q_6",
        "Advantage_system4",
        "ionQdevice",
        "Aspen-11",
        "Aspen-M-1",
    ]
    device_region_index_dict: dict[str, int] = {
        "d-wave": 1,
        "rigetti": 0,
        "ionq": 2,
        "DW_2000Q_6": 1,
        "Advantage_system4": 1,
        "ionQdevice": 2,
        "Aspen-11": 0,
        "Aspen-M-1": 0,
    }

    # setting device of Tasks that have now changed the status
    device_provider: str
    device_name: str
    is_known_device: bool
    (device_provider, device_name, is_known_device) = set_device_info(
        device_providers, device_names, event
    )
    if is_known_device == False:
        post_slack("error: unknown_device", " ", SLACK_POST_URL)
        return {"error": "unkown device"}

    # store task results for each status to result dictionary
    shots_count_each_status: list[int] = [0, 0, 0]
    task_count_each_status: list[int] = [0, 0, 0]
    task_info_each_status: list = []
    result: dict = {}
    (
        shots_count_each_status,
        task_count_each_status,
        task_info_each_status,
        result,
    ) = set_task_results(
        clients,
        device_region_index_dict,
        device_provider,
        device_name,
    )

    # set output json string values
    lambda_output: dict = {}
    lambda_output = set_lambda_output(
        lambda_output, result, shots_count_each_status, task_count_each_status
    )

    device_type = "qpu"
    deleted_result: dict = delete_task_over_max_shot(
        MAX_SHOT_NUM,
        clients,
        device_region_index_dict,
        device_type,
        device_provider,
        device_name,
        shots_count_each_status,
        task_info_each_status,
    )

    # send_email(lambda_output, TOPIC_ARN)
    post_slack(lambda_output, deleted_result, SLACK_POST_URL)

    return lambda_output


def set_task_results(
    clients: list, device_region_index_dict: dict, device_provider, device_name
) -> tuple[list[int], list[int], list, dict]:
    # store task results for each status to result dictionary
    shots_count_each_status: list[int] = [0, 0, 0]
    task_count_each_status: list[int] = [0, 0, 0]
    task_info_each_status: list = []
    result: dict = {}
    today_date = [date.today().year, date.today().month, date.today().day]

    for task_status_index in range(3):
        result = clients[device_region_index_dict[device_provider]].get_info(
            *today_date, "qpu", device_provider, device_name, task_status_index
        )
        task_info_each_status.append(result)

        shots_count_each_status[task_status_index] += result["total_shots"]

        if result["total_shots"]:
            for id_name in result["id"].keys():
                if not "/" in id_name:
                    task_count_each_status[task_status_index] += len(result["id"][id_name])
    return (
        shots_count_each_status,
        task_count_each_status,
        task_info_each_status,
        result,
    )


def set_device_info(device_providers, device_names, event) -> tuple[str, str, bool]:
    # setting device of Tasks that have now changed the status
    device_dict: dict[str, str] = {}
    for provider, device in zip(device_providers, device_names):
        device_dict[provider] = device
    device_provider: str = ""
    device_name: str = ""
    is_known_device = False
    for provider, device in zip(device_providers, device_names):
        if provider in event["detail"]["deviceArn"]:
            device_provider = provider
            if device in event["detail"]["deviceArn"]:
                device_name = device
                is_known_device = True
                return (device_provider, device_name, is_known_device)

    return ("", "", False)


def set_lambda_output(
    lambda_output: dict,
    result: dict,
    shots_count_each_status: list[int],
    task_count_each_status: list[int],
) -> dict:
    # set lambda_output in json string type
    lambda_output["date"] = result["date"]
    lambda_output["qpu"] = result["qpu"]
    lambda_output["QUEUED_shot_count"] = shots_count_each_status[0]
    lambda_output["QUEUED_task_conut"] = task_count_each_status[0]
    lambda_output["COMPLETED_shot_count"] = shots_count_each_status[1]
    lambda_output["COMPLETED_task_count"] = task_count_each_status[1]
    lambda_output["CANCELLED_shot_count"] = shots_count_each_status[2]
    lambda_output["CANCELLED_task_count"] = task_count_each_status[2]

    return lambda_output


def delete_task_over_max_shot(
    max_shot_num: int,
    clients: list,
    device_region_index_dict: dict,
    device_type: str,
    device_provider: str,
    device_name: str,
    shots_count_each_status: list[int],
    task_info_each_status: list[dict],
):
    """delete QUEUED task according to the number of shots
    Args:
        max_shot_num :
        clients :
        device_region_index_dict :
        device_type :
        device_provider :
        device_name :

    Returns:
        result : TODO 削除したtask_id全て列挙
    """

    # for debug
    print(
        "\r"
        + str(datetime.now().time())
        + " QUEUED "
        + str(shots_count_each_status[0])
        + " COMPLETED "
        + str(shots_count_each_status[1])
        + " CANCELLED "
        + str(shots_count_each_status[2]),
        end="",
    )

    # 現在QUEUEDのshots合計が50以上なら, 全部のQUEUD taskを削除
    deleted_result = []
    if shots_count_each_status[0] >= max_shot_num:
        for bucket_name in task_info_each_status[0]["id"]:
            # bucket_nameにはbucketとそのfolderの両方がtask_idsに代入されるため,
            # '/'があったら飛ばす(folderの中のtaskはとばす)
            if "/" not in bucket_name:
                for task_id in task_info_each_status[0]["id"][bucket_name]:
                    deleted_result.append(
                        clients[device_region_index_dict[device_name]].delete_quantumTask(task_id)
                    )
        return deleted_result


def delete_task_over_max_cost(
    max_cost: int,
    clients: list,
    device_region_index_dict: dict,
    device_type: str,
    device_provider: str,
    device_name: str,
    shots_count_each_status: list[int],
    task_info_each_status: list[dict],
    task_count_each_status: list[int],
):
    """Delete QUEUD task accordingly when the maximum cost is exceeded
    Args:
        max_cost :
        clients :
        device_region_index_dict :
        device_type :
        device_provider :
        device_name :
    Returns:
        result : 削除したtask_id 全列挙
    """

    # TODO
    # price definition
    price_per_task: float = 0.3
    price_table: dict = {"d-wave": 0.00019, "ionq": 0.01, "rigetti": 0.00035}
    price_each_status_index: dict = {"QUEUED": 0, "COMPLETED": 1, "CANCELLED": 2}
    price_each_status: list = [0] * len(price_each_status_index)

    # Calculate the total cost of each state
    for price_status in price_each_status_index:
        price_each_status[price_each_status_index[price_status]] = (
            shots_count_each_status[price_each_status_index[price_status]]
            * price_table[device_provider]
            + task_count_each_status[price_each_status_index[price_status]] * price_per_task
        )

    print(
        "\r"
        + str(datetime.now().time())
        + " QUEUED "
        + str(price_each_status[0])
        + " COMPLETED "
        + str(price_each_status[1])
        + " CANCELLED "
        + str(price_each_status[2]),
        end="",
    )

    # 現在QUEUEDのshots合計が50以上なら, 全部のQUEUD taskを削除
    deleted_result = []
    if price_each_status[0] >= max_cost:
        for bucket_name in task_info_each_status[0]["id"]:
            # bucket_nameにはbucketとそのfolderの両方がtask_idsに代入されるため,
            # '/'があったら飛ばす(folderの中のtaskはとばす)
            if "/" not in bucket_name:
                for task_id in task_info_each_status[0]["id"][bucket_name]:
                    deleted_result.append(
                        clients[device_region_index_dict[device_name]].delete_quantumTask(task_id)
                    )
    return deleted_result


def send_email(lambda_output, TOPIC_ARN):
    client = boto3.client("sns")
    msg = str(lambda_output)
    subject: str = "Braket Monitor"
    response = client.publish(TopicArn=TOPIC_ARN, Message=msg, Subject=subject)


def post_slack(lambda_output, deleted_result, slack_post_url):

    # 設定

    username = "speed"
    icom = ":sunglasses:"
    channnel = "#general"
    method = "POST"

    # メッセージの内容
    now = datetime.now()
    current_time = now.strftime("%Y/%m/%d %H:%M:%S")
    operation_message = "Task Information" + " " + current_time + "\n"
    detail_info = str(lambda_output)
    delete_message = "delete task result\n" + str(deleted_result)
    message = operation_message + detail_info + "\n" + delete_message
    send_data = {
        "username": username,
        "icon_emoji": icom,
        "text": message,
        "channel": channnel,
    }

    send_text = ("payload=" + json.dumps(send_data)).encode("utf-8")

    request = urllib.request.Request(slack_post_url, data=send_text, method=method)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")

    return response_body
