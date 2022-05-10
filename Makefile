build: FORCE
	sam build

deploy: build FORCE
	sam deploy --resolve-s3 --stack-name amazonBraketMonitoringTool --region us-east-1 \
		--parameter-overrides  SLACKPOSTURL="hoge"

FORCE: 
