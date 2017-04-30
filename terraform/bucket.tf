resource "aws_s3_bucket" "loader_bucket" {
  bucket = "${var.loader_s3_bucket_name}"
  acl = "private"

  tags {
    Name = "Beer Loader Bucket"
  }
}
