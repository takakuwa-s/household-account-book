# 家計簿アプリ

LINE Botで受け取ったレシートを解析し、支出データをGoogle Sheetsへ登録するアプリケーションです。レシート解析にはAzure AI Document Intelligenceを使用し、AWS Lambda、SQS、DynamoDBを中心に実行します。

## 処理の流れ

1. LINE Messaging APIからWebhookを `line_bot_handler` Lambdaへ送信します。
2. 画像イベントを処理し、レシート解析用データをSQSへ送ります。テキストやPostbackイベントは家計簿操作として処理されます。
3. `analyze_receipt` LambdaがSQSメッセージを受信してAzure AI Document Intelligenceで解析します。
4. 解析結果やアプリケーションデータをDynamoDBとGoogle Sheetsに保存します。

Terraformのapply時にはLINEのWebhook URLとリッチメニューも設定されます。

## ディレクトリ構成

| パス | 役割 |
| --- | --- |
| `main.py` | Lambda関数のエントリーポイント |
| `src/app/adaptor/` | LINE、Azure、Google Sheets、SQSなど外部サービスとの接続 |
| `src/app/config/` | ログなどのアプリケーション設定 |
| `src/app/functions/` | Lambdaハンドラー |
| `src/app/handler/` | LINE Messaging APIイベントの処理 |
| `src/app/model/` | アプリケーション内のデータモデル |
| `src/app/repository/` | DynamoDBなどのデータアクセス |
| `src/app/usecase/` | アプリケーションのユースケース |
| `src/test/` | pytestテストとテスト用イベント |
| `resource/` | Googleサービスアカウント認証情報などの実行時リソース |
| `terraform/environments/prod/` | prod環境のTerraformルートモジュール、変数、プロバイダー設定 |
| `terraform/modules/aws/` | AWS Lambda、Layer、DynamoDB、SQS、IAM、CloudWatchのモジュール |
| `terraform/modules/azure/` | Azure Resource GroupとDocument Intelligenceのモジュール |
| `terraform/scripts/` | LINE Webhook・リッチメニュー設定スクリプトと画像 |
| `terraform/output/` | Terraformが生成するLambdaコードと依存ライブラリのアーカイブ |

## 必要なもの

- Python 3.14（LambdaランタイムもPython 3.14）
- Terraform 1.10.4以上（最新安定版1.17.1を推奨）
- AWS認証情報と、`ap-northeast-1` でリソースを作成できる権限
- Azure CLIでログインできるAzureサブスクリプションと、リソース作成権限
- LINE Messaging APIチャネル
- Google Sheetsと、そのシートへの書き込み権限を持つサービスアカウント

## ローカル開発とテスト

リポジトリのルートで仮想環境を作成し、アプリケーション依存関係をインストールします。

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest src/test
```

Google Sheets連携のローカル実行には `resource/gcp-credentials.json` が必要です。LINEや外部サービスに接続する処理では、別途対応する認証情報と環境変数を用意してください。

## prod環境のデプロイ

### 1. 認証情報を準備する

AWS CLIが利用する認証情報を設定し、Azureへログインします。

```bash
aws configure
az login
```

LINEチャネル、Google Sheets、Googleサービスアカウントを準備します。`resource/gcp-credentials.json` を配置し、対象スプレッドシートをサービスアカウントに共有してください。

`terraform/environments/prod/terraform.tfvars` をローカルに作成し、次の変数を設定します。

```hcl
channel_access_token    = "..."
channel_secret          = "..."
azure_subscription_id   = "..."
spreadsheet_id          = "..."
expenditure_sheet_name  = "..."
```

`terraform.tfvars` はGit管理対象外です。値をコミットしたり、ログ・チャットへ貼り付けたりしないでください。

### 2. Terraformを実行する

リポジトリルートでPython仮想環境を有効にし、Terraform環境ディレクトリで初期化、検証、計画を行います。

```bash
cd terraform/environments/prod
terraform init
terraform validate
terraform plan
```

計画内容を確認してから適用します。

```bash
terraform apply
```

TerraformはLambda用のPython 3.14 / ARM64依存Layerとコードアーカイブを生成します。Python 3.15はLambdaでプレビュー中のため、本番環境ではGA済みのPython 3.14を使用します。適用時にはLINE設定スクリプトも実行され、LINEチャネルのWebhook URLとリッチメニューが更新されます。適用端末からLINE APIへ接続でき、必要なPython依存関係をインストールできることを確認してください。

### 3. リソースを削除する

削除対象を確認したうえで、同じ環境ディレクトリから実行します。DynamoDBのデータを含めて削除される可能性があります。

```bash
terraform plan -destroy
terraform destroy
```

## 認証情報とTerraform state

- `terraform.tfvars`、Terraform state、`resource/gcp-credentials.json` には秘密情報が含まれるため、Gitへ追加しないでください。
- Terraform stateはリソース情報や機密値を含みます。現状はリモートbackendの設定がないため、ローカルstateを安全に保管し、共有運用では暗号化・アクセス制御されたリモートbackendを検討してください。
- Lambdaコードのアーカイブはリポジトリルートを元に生成され、Terraform関連ファイルなどを除外します。Google Sheets連携が実行時に参照する `resource/gcp-credentials.json` はアーカイブに含まれるため、サービスアカウントに最小権限を付与し、キーの保管・ローテーションに注意してください。
- 認証情報を誤って公開した場合は、該当するLINE、Google、AWS、Azureの資格情報を失効・ローテーションしてください。Gitからファイルを削除するだけでは、履歴やTerraform state内の値は消えません。