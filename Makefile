deploy: FORCE
	sam deploy --resolve-s3 --stack-name amazonBraketMonitoringTool --region us-east-1

FORCE: 
