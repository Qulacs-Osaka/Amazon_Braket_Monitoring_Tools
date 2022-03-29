import boto3
from collections import defaultdict
from datetime import datetime, date, timedelta

class AmazonBraketlib:
    def __init__(self,region,clientToken):
        self.region = region
        self.clientToken = clientToken
        self.braket = boto3.client('braket',region_name=self.region)

    def massage_maker(self,date,time,device,count):
        message = "At "+str(date)+str(time)+" "+"I detected increaing by "+str(count)+"at "+device+". Please keep care."
        return message

    def make_markdown_from_list(self,str_time,target_list):
        res_str = ""
        res_str += str_time + "<br/>"
        res_str += " ".join(target_list) + "<br/>"
        return res_str

    def res_print(self,dict):
        for k in dict.keys():print(k,dict[k])

    def get_info(self,year,month,day,device_a,device_m,device_e,i):

        def cal(self):
            for k in response['quantumTasks']:
                # print(k)
                if (date(year,month,day) - k['createdAt'].date() > delta1) == True:
                    return 1
                    break
                if k['status'] == target_name[i] and k['createdAt'].date() == date(year,month,day):
                    total_shots_array[target_name[i]] +=  + k['shots']
                    time_me = k['createdAt'].time()

                    tmp_s3_dic_name_array = list(k['outputS3Directory'].split('/'))
                    if k['outputS3Bucket'] not in s3bucket_name_array:
                        s3bucket_name_array.append(k['outputS3Bucket'])
                        count_dic[k['outputS3Bucket']] = 0
                        count_id[k['outputS3Bucket']] = []
                    count_dic[k['outputS3Bucket']] += k['shots']
                    count_id[k['outputS3Bucket']].append(k['quantumTaskArn'])

                    if tmp_s3_dic_name_array[0] not in s3bucket_dic_name_dic[k['outputS3Bucket']]:
                        s3bucket_dic_name_dic[k['outputS3Bucket']].append(tmp_s3_dic_name_array[0])
                        count_dic[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] = 0
                        count_id[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] = []
                    count_dic[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] += k['shots']
                    count_id[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]].append(k['quantumTaskArn'])

        s3bucket_name_array = []
        s3bucket_dic_name_dic = defaultdict(list)
        s3bucket_dic_id_dic = defaultdict(list)
        count_dic = {}
        count_id = {}
        delta1 = timedelta(seconds=60)

        total_shots = 0
        target_name = ['QUEUED','COMPLETED','CANCELLED','RUNNING']
        total_shots_array = {}
        for I in target_name:total_shots_array[I] = 0

        target_status = target_name[i]
        device_n = 'device'
        device_name = device_n+'/'+device_a+'/'+device_m+'/'+device_e

        #Search Quantum Tasks recursively
        next_token = ''

        own_filters = [
            {
                'name': 'deviceArn',
                'operator': 'EQUAL',
                'values': [
                'arn:aws:braket:::'+device_name
                ]
            },
        ]

        response = self.braket.search_quantum_tasks(
            filters=own_filters,
            maxResults=100
        )
        time_me =0;flag = 0

        flag = cal(self)
        if 'nextToken' in response:next_token = response['nextToken']
        elif flag==1:
            next_token = False
            return {"id":count_id,
                    "count":count_dic,"total_shots":total_shots_array[target_name[i]],
                "hardware": device_m,
                    "qpu": device_e,"status":target_status,
                    'date':str(year)+'-'+str(month)+'-'+str(day),
                'time':str(time_me)}

        else:next_token = False
        while next_token and flag==0:
            response = self.braket.search_quantum_tasks(
                filters=own_filters,
                maxResults=100,
                nextToken = next_token
            )

            flag = cal(self)
            if 'nextToken' in response:next_token = response['nextToken']
            elif flag==1:break
            else:break

        return {"id":count_id,
                "count":count_dic,"total_shots":total_shots_array[target_name[i]],
            "hardware": device_m,
                "qpu": device_e,"status":target_status,
                'date':str(year)+'-'+str(month)+'-'+str(day),
            'time':str(time_me)}

    def delete_quantumTask(self,quantumTaskArn_name):
        response = self.braket.cancel_quantum_task(clientToken= self.clientToken, quantumTaskArn= quantumTaskArn_name)
        return response