# https://qiita.com/neruneruo/items/feca4ea15e2230c188b4
resource "terraform_data" "pip_install" {
  triggers_replace = [
    filebase64("../../../requirements.txt")
  ]

  provisioner "local-exec" {
    command = <<-EOF
      rm -rf ../../output/layer/python &&
      pip install \
        --platform manylinux2014_aarch64 \
        --target=../../output/layer/python/ \
        --implementation cp \
        --python-version 3.12 \
        -r ../../../requirements.txt \
        --only-binary=:all: --upgrade \
        --no-cache-dir
    EOF

    on_failure = fail
  }
}

data "archive_file" "pip_package_layer_zip" {
  depends_on = [
    terraform_data.pip_install,
  ]

  type        = "zip"
  source_dir  = "../../output/layer"
  output_path = "../../output/pip_package_layer.zip"
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_layer_version
resource "aws_lambda_layer_version" "pip_package_layer" {
  layer_name = "${var.env_variables.env}_pip_package_layer"

  compatible_architectures = ["arm64"]
  compatible_runtimes      = ["python3.12"]
  filename                 = data.archive_file.pip_package_layer_zip.output_path
  source_code_hash         = data.archive_file.pip_package_layer_zip.output_base64sha256
}
