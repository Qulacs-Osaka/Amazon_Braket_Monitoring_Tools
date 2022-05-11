STACKNAME := "amazonBraketMonitoringTool"
REGION := "us-west-1"
SLACKPOSTURL := "https://hooks.slack.com/services/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"
notificationEmail := "kotamanegi84@gmail.com"

build: FORCE
	sam build

deploy: build FORCE
	sam deploy --resolve-s3 --stack-name $(STACKNAME) --region $(REGION) \
		--parameter-overrides SLACKPOSTURL=$(SLACKPOSTURL) NOTIFICATIONEMAIL=$(notificationEmail)

clean: FORCE
	sam delete --stack-name $(STACKNAME) --region $(REGION)

FORCE: 
