STACKNAME := "amazonBraketMonitoringTool"
REGION := "us-west-1"
LambdaRoleArn := "arn:aws:iam::227122787190:role/amazon-braket-monitor"
SLACKPOSTURL := "https://hooks.slack.com/services/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"
notificationEmail := "kotamanegi84@gmail.com"

build: FORCE
	sam build

deploy: build FORCE
	sam deploy --resolve-s3 --stack-name $(STACKNAME) --region $(REGION) \
		--parameter-overrides SLACKPOSTURL=$(SLACKPOSTURL) NOTIFICATIONEMAIL=$(notificationEmail) LAMBDAROLEARN=$(LambdaRoleArn)

clean: FORCE
	sam delete --stack-name $(STACKNAME) --region $(REGION)

FORCE: 
