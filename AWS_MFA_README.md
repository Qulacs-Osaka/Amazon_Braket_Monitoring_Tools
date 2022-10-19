# aws-mfa使用時の注意

aws-mfa --profile sample
など, profileを指定して認証した場合, awsコマンド実行時にも--profile sampleとしないといけない.
もしくは, export AWS_PROFILE=sample
と環境変数で設定しておく
