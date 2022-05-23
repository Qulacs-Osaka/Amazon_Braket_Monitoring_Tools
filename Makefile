STACKNAME := "amazonBraketMonitoringTool"
REGION := "us-west-1"
SLACKPOSTURL := "https://hooks.slack.com/services/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"
notificationEmail := "pyroxene68473@gmail.com"
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
