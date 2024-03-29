import json
import logging
import os
import urllib.request
from datetime import date, datetime

import boto3  # type:ignore

import settings
from AmazonBraketlib import AmazonBraketlib

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
    # 定数設定
    SLACK_POST_URL = os.environ["SLACK_POST_URL"]
    TOPIC_ARN = os.environ["TOPIC_ARN"]
    MAX_SHOT_NUM = int(os.environ["MAX_SHOT_NUM"])
    MAX_SHOT_COST = int(os.environ["MAX_SHOT_COST"])  # dollar

    logger.info(event)

    # set boto user
    ama_us_west_1 = AmazonBraketlib("us-west-1")
    ama_us_west_2 = AmazonBraketlib("us-west-2")
    ama_us_east_1 = AmazonBraketlib("us-east-1")
    clients: list = [ama_us_west_1, ama_us_west_2, ama_us_east_1]

    # device definition
    device_table: dict[str, list[str]] = settings.DEVICE_TABLE
    device_region_index_dict: dict[str, int] = settings.DEVICE_REGION_INDEX_DICT

    # setting device of Tasks that have now changed the status
    device_provider: str
    device_name: str
    is_known_device: bool
    (device_provider, device_name, is_known_device) = set_device_info(
        device_table, event
    )
    if is_known_device is False:
        post_slack("error: unknown_device", SLACK_POST_URL, event)
        return {"error": "unknown device"}

    # store task results for each status to result dictionary
    shots_count_each_status: list[int] = [0, 0, 0]
    task_count_each_status: list[int] = [0, 0, 0]
    task_info_each_status: list = []
    result: dict = {}
    deviceArn: str = event["detail"]["deviceArn"]
    (
        shots_count_each_status,
        task_count_each_status,
        task_info_each_status,
        result,
    ) = set_task_results(
        shots_count_each_status,
        task_count_each_status,
        task_info_each_status,
        clients,
        device_region_index_dict,
        device_provider,
        deviceArn,
    )

    # set output json string values
    lambda_output: dict = {}
    lambda_output = set_lambda_output(
        lambda_output, result, shots_count_each_status, task_count_each_status
    )

    deleted_result: list = delete_task_over_max_shot(
        MAX_SHOT_NUM,
        clients,
        device_region_index_dict,
        device_provider,
        shots_count_each_status,
        task_info_each_status,
    )

    deleted_result2: list = delete_task_over_max_cost(
        MAX_SHOT_COST,
        clients,
        device_region_index_dict,
        device_provider,
        shots_count_each_status,
        task_info_each_status,
        task_count_each_status,
    )

    send_email(lambda_output, TOPIC_ARN)
    post_slack(lambda_output, SLACK_POST_URL, event)

    return lambda_output


def set_task_results(
    shots_count_each_status: list[int],
    task_count_each_status: list[int],
    task_info_each_status: list,
    clients: list,
    device_region_index_dict: dict,
    device_provider: str,
    deviceArn: str,
) -> tuple[list[int], list[int], list, dict]:
    # store task results for each status to result dictionary

    result: dict = {}
    today_date = [date.today().year, date.today().month, date.today().day]

    for task_status_index in range(3):
        result = clients[device_region_index_dict[device_provider]].get_info(
            *today_date, deviceArn, task_status_index
        )
        task_info_each_status.append(result)

        shots_count_each_status[task_status_index] += result["total_shots"]

        if result["total_shots"]:
            for id_name in result["id"].keys():
                if "/" not in id_name:
                    task_count_each_status[task_status_index] += len(
                        result["id"][id_name]
                    )
    return (
        shots_count_each_status,
        task_count_each_status,
        task_info_each_status,
        result,
    )


def set_device_info(device_table: dict[str, list[str]], event) -> tuple[str, str, bool]:
    # setting device of Tasks that have now changed the status
    # for each device_table keys
    for device_provider in device_table.keys():
        # for each device_table values
        for device_name in device_table[device_provider]:
            if device_name in event["detail"]["deviceArn"]:
                return (device_provider, device_name, True)
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
    device_provider: str,
    shots_count_each_status: list[int],
    task_info_each_status: list[dict],
):
    """delete QUEUED task according to the number of shots
    Args:
        max_shot_num :
        clients :
        device_region_index_dict :
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

    # 現在QUEUEDのshots合計がMAX_SHOT以上なら, 全部のQUEUD taskを削除
    deleted_result = []
    if shots_count_each_status[0] >= max_shot_num:
        for bucket_name in task_info_each_status[0]["id"]:
            # bucket_nameにはbucketとそのfolderの両方がtask_idsに代入されるため,
            # '/'があったら飛ばす(folderの中のtaskはとばす)
            if "/" not in bucket_name:
                for task_id in task_info_each_status[0]["id"][bucket_name]:
                    deleted_result.append(
                        clients[
                            device_region_index_dict[device_provider]
                        ].delete_quantumTask(task_id)["quantumTaskArn"]
                    )
        return deleted_result


def delete_task_over_max_cost(
    max_cost: int,
    clients: list,
    device_region_index_dict: dict,
    device_provider: str,
    shots_count_each_status: list[int],
    task_info_each_status: list[dict],
    task_count_each_status: list[int],
):
    """Delete QUEUD task accordingly when the maximum cost is exceeded
    Args:
        max_cost :
        clients :
        device_region_index_dict :
        device_provider :
        device_name :
    Returns:
        result : 削除したtask_id 全列挙
    """
    price_per_task: float = settings.PRICE_PER_TASK
    price_table: dict = settings.PRICE_TABLE
    price_each_status_index: dict = {"QUEUED": 0, "COMPLETED": 1, "CANCELLED": 2}
    price_each_status: list = [0] * len(price_each_status_index)

    # Calculate the total cost of each state
    for price_status in price_each_status_index:
        price_each_status[price_each_status_index[price_status]] = (
            shots_count_each_status[price_each_status_index[price_status]]
            * price_table[device_provider]
            + task_count_each_status[price_each_status_index[price_status]]
            * price_per_task
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

    # 現在QUEUEDのshots合計が50以上なら, 全部のQUEUED taskを削除
    deleted_result = []
    if price_each_status[0] >= max_cost:
        for bucket_name in task_info_each_status[0]["id"]:
            # bucket_nameにはbucketとそのfolderの両方がtask_idsに代入されるため,
            # '/'があったら飛ばす(folderの中のtaskはとばす)
            if "/" not in bucket_name:
                for task_id in task_info_each_status[0]["id"][bucket_name]:
                    deleted_result.append(
                        clients[
                            device_region_index_dict[device_provider]
                        ].delete_quantumTask(task_id)["quantumTaskArn"]
                    )
    return deleted_result


def send_email(lambda_output, TOPIC_ARN):
    client = boto3.client("sns")
    msg = str(lambda_output)
    subject: str = "Braket Monitor"
    client.publish(TopicArn=TOPIC_ARN, Message=msg, Subject=subject)


def post_slack(lambda_output, slack_post_url, event):

    # 設定
    method = "POST"

    # メッセージの内容
    now = datetime.now()
    current_time = now.strftime("%Y/%m/%d %H:%M:%S")
    operation_message = (
        "*# Task Information*"
        + " "
        + current_time
        + "\n"
        + "*- triggered event: *\n"
        + "status: "
        + str(event["detail"]["status"])
        + ", "
        + "deviceArn: "
        + str(event["detail"]["deviceArn"])
        + ", "
        + "shots: "
        + str(event["detail"]["shots"])
        + "\n"
    )

    detail_info = str(lambda_output)

    message = (
        operation_message
        + "\n"
        + "*- Total task information for a specific device:*\n"
        + detail_info
        + "\n"
    )
    send_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                },
            }
        ],
    }

    send_text = ("payload=" + json.dumps(send_data)).encode("utf-8")

    request = urllib.request.Request(slack_post_url, data=send_text, method=method)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")

    return response_body
