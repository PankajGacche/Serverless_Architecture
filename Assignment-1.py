import boto3
import base64
import time
import uuid

def Launch_EC2_Instance(ec2_client,ec2_tag_Name,ec2_instance_name, image_id, instance_type, key_name,subnet_id, security_group, user_data):
    try:
        instance = ec2_client.run_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=security_group,
            SubnetId=subnet_id,
            UserData=user_data,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Action',
                            'Value': ec2_tag_Name,
                            'Key': 'Name',
                            'Value': ec2_instance_name
                        },
                    ]
                 },
            ]
        )
        instance_id = instance['Instances'][0]['InstanceId']
        print(f"Instance {instance_id} launched successfully.")
        return instance_id
    except Exception as e:
        print(f"Error launching EC2 instance: {e}")

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')

    auto_stop_instances = get_instances_by_tag(ec2_client, 'Action','Auto-Stop')

    for instance_id in auto_stop_instances:
        stop_instance(ec2_client, instance_id)
        print(f"Stopped instance: {instance_id}")

    auto_start_instances = get_instances_by_tag(ec2_client, 'Action','Auto-Start')

    for instance_id in auto_start_instances:
        start_instance(ec2_client, instance_id)
        print(f"Started instance: {instance_id}")
    
    return {
        'statusCode': 200,
        'body': 'Auto-Stop and Auto-Start process completed successfully'
    }

def get_instances_by_tag(ec2_client, tag_key,tag_value):
    instances = []
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]}
        ]
    )
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])
    return instances

def stop_instance(ec2_client, instance_id):
    ec2_client.stop_instances(InstanceIds=[instance_id])
    print(f'{instance_id} instance stopped successfully')

def start_instance(ec2_client, instance_id):
    ec2_client.start_instances(InstanceIds=[instance_id])

if __name__ == "__main__":
    instance_type = 't3.micro'
    region_name='eu-north-1'
    vpc_id='vpc-05154ead3bc4c56b7'
    instance_type = 't3.micro'
    key_name = 'My_Key_Pair'
    subnet_id = 'subnet-07f4de62d10359420'
    security_group = ['sg-0bf10eab4bb24c016']
    image_id = 'ami-07c8c1b18ca66bb07'
    ec2_1_tag_Name='Auto-Stop'
    ec2_2_tag_Name='Auto-Start'
    ec2_start_instance_name='Auto-Start-'+str(uuid.uuid4())[:5]
    ec2_stop_instance_name='Auto-Stop-'+str(uuid.uuid4())[:5]
    ec2_client = boto3.client('ec2', region_name=region_name)
    userdata_script='''#!/bin/bash
                 sudo apt-get update -y
                 sudo apt-get install -y nginx
                 sudo mkdir -p /var/www/html/myproject
                 sudo chown -R ubuntu:ubuntu /var/www/html/myproject
                 sudo apt install python3
                 sudo apt install -y python3-pip
                 sudo apt install -y python3-flask
                 sudo apt install git
                 sudo git clone https://github.com/PankajGacche/Simple_Flask_Application.git /var/www/html/myproject
                 sudo service nginx restart
                 cd /var/www/html/myproject
                 sudo python3 simple_app.py
                 ''' 
    
userdata_script_encoded = base64.b64encode(userdata_script.encode()).decode('utf-8')
instance_id1=Launch_EC2_Instance(ec2_client,ec2_1_tag_Name,ec2_start_instance_name, image_id, instance_type, key_name, subnet_id,security_group, userdata_script_encoded)
time.sleep(60)
stop_instance(ec2_client,instance_id1)
instance_id2=Launch_EC2_Instance(ec2_client,ec2_2_tag_Name,ec2_stop_instance_name, image_id, instance_type, key_name, subnet_id,security_group, userdata_script_encoded)
time.sleep(60)
