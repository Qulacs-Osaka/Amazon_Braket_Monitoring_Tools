import numpy as np
# import matplotlib.pyplot as plt
# magic word for producing visualizations in notebook
# %matplotlib inline

import argparse
# AWS imports: Import Braket SDK modules
from braket.circuits import Circuit, Gate, Instruction, circuit, Observable
from braket.devices import LocalSimulator
from braket.aws import AwsDevice, AwsQuantumTask

# Please enter the S3 bucket you created during onboarding in the code below

my_bucket = "amazon-braket-masumoto" # the name of the bucket
my_prefix = "Sandbox" # the name of the folder in the bucket

s3_folder = (my_bucket, my_prefix)

parser = argparse.ArgumentParser()
parser.add_argument('--shots', default=10)
args = parser.parse_args()


dev1 = 'rigetti'
dev2 = 'Aspen-M-1'

# set up device
rigetti = AwsDevice("arn:aws:braket:us-west-1::device/qpu/"+dev1+'/'+dev2)

# create a clean circuit with no result type attached.(This is because some result types are only supported when shots=0)
bell = Circuit().h(0).cnot(0, 1)  

# add the Z \otimes Z expectation value
bell.expectation(Observable.Z() @ Observable.Z(), target=[0,1])

# run circuit 
rigetti_task = rigetti.run(bell, s3_folder, shots=args.shots)

# get id and status of submitted task
rigetti_task_id = rigetti_task.id
rigetti_status = rigetti_task.state()
print('ID of task:', rigetti_task_id)
print('Status of task:', rigetti_status)
