
output "role" {
  value = "${aws_iam_role.beer_loader_role.name}"
}

output "user" {
  value = "${aws_iam_user.beer_user.name}"
}

output "bucket" {
  value = "${aws_s3_bucket.loader_bucket.arn}"
}
