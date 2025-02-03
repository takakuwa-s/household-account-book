variable "table_name" {
  type        = string
  description = "テーブル名"
}

variable "hash_key" {
  type        = string
  description = "ハッシュキー"
}

variable "range_key" {
  type        = string
  description = "レンジキー"
}

variable "items" {
  type        = map(any)
  description = "レコードのリスト"
}
