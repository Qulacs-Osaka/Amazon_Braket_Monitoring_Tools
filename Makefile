STACKNAME := "amazonBraketMonitoringTool"
REGION := "us-west-1"
SLACKPOSTURL := "slack post url starting from https:"
notificationEmail := "notification email"
MAXNUM := 100
MAXCOST := 1

build: FORCE
	sam build

deploy: build FORCE
	sam deploy --resolve-s3 --stack-name $(STACKNAME) --region $(REGION) \
		--parameter-overrides SLACKPOSTURL=$(SLACKPOSTURL) NOTIFICATIONEMAIL=$(notificationEmail) MAXNUM=$(MAXNUM) MAXCOST=$(MAXCOST)

clean: FORCE
	sam delete --stack-name $(STACKNAME) --region $(REGION)

FORCE: 
