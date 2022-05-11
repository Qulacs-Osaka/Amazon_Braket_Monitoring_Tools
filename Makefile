STACKNAME := "amazonBraketMonitoringTool"
REGION := "us-west-1"
SLACKPOSTURL := "slack post url starting from https:"
notificationEmail := "notification email"

build: FORCE
	sam build

deploy: build FORCE
	sam deploy --resolve-s3 --stack-name $(STACKNAME) --region $(REGION) \
		--parameter-overrides SLACKPOSTURL=$(SLACKPOSTURL) NOTIFICATIONEMAIL=$(notificationEmail)

clean: FORCE
	sam delete --stack-name $(STACKNAME) --region $(REGION)

FORCE: 
