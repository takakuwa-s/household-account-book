# Agent Guide

このファイルは、このリポジトリで作業するAIエージェント向けの案内です。全体構成とデプロイ手順は [README.md](README.md) を参照してください。

## プロジェクト構成

- アプリケーション本体は `src/app/` にあります。Lambdaエントリーポイントはルートの `main.py` です。
- 外部サービスとの接続は `src/app/adaptor/`、イベント処理は `src/app/handler/`、業務処理は `src/app/usecase/`、データアクセスは `src/app/repository/` に置きます。
- テストは `src/test/` にあります。既存の構成と命名に合わせ、変更範囲に近いテストを更新してください。
- Terraformの本番環境は `terraform/environments/prod/`、再利用モジュールは `terraform/modules/` にあります。

## 開発と検証

- Python依存関係は `requirements.txt` で管理します。テストにはpytestを使います。
- リポジトリルートで `python -m pytest src/test` を実行します。pytestが未導入の場合は別途インストールしてください。
- Terraformはバージョン1.10.4を使います。Terraform変更時は `terraform/` で `terraform fmt -check -recursive` を実行し、`terraform/environments/prod/` で `terraform validate` と `terraform plan` を実行します。
- 既存の公開関数名やTerraform module interfaceは、依頼に必要な場合を除いて変更しないでください。

## クラウド変更と秘密情報

- `terraform apply`、`terraform destroy`、LINE Webhook・リッチメニュー変更など、外部サービスやクラウドの状態を変更する操作は、ユーザーから明示的に依頼された場合に限ります。実行前にplanと変更内容を確認してください。
- `terraform.tfvars`、Terraform state、`resource/gcp-credentials.json`、トークン、キーは秘密情報として扱います。内容を出力・貼り付け・コミットせず、Git管理対象へ追加しないでください。
- Lambdaのコードアーカイブには `resource/gcp-credentials.json` が含まれます。関連する変更ではデプロイ先への認証情報の配布と最小権限を考慮してください。
- `terraform/.terraform/` と `terraform/output/` は依存物・生成物です。調査や検証で必要な場合を除き、直接編集しないでください。

## 変更方針

- 既存の責務分担と近隣コードのスタイルに合わせ、必要な範囲だけを変更します。
- 外部サービスを使うテストでは、既存テストの前提を確認し、認証情報や実サービスへの意図しないアクセスを避けてください。
- 検証できなかった項目や外部認証が必要な操作は、作業結果で明確に伝えてください。