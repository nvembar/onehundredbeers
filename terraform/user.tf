data "aws_caller_identity" "current" {}

resource "aws_iam_user" "beer_user" {
  name = "${var.loader_user_name}"
}

data "aws_iam_policy_document" "loader_assume_role_policy" {
  statement {
    actions = [ "sts:AssumeRole" ]
    principals {
      # This should limit the users that can assume the role to
      # those associated with the current identity
      type = "AWS"
      identifiers = [
        "${data.aws_caller_identity.current.arn}",
        "${aws_iam_user.beer_user.arn}"
      ]
    }
  }
}

resource "aws_iam_role" "beer_loader_role" {
  name = "${var.loader_role_name}"
  path = "${var.loader_role_path}"
  assume_role_policy = "${data.aws_iam_policy_document.loader_assume_role_policy.json}"
}

data "aws_iam_policy_document" "loader_s3_role_policy" {
  statement {
    actions = [ "s3:*" ]
    resources = [ "arn:aws:s3:::${var.loader_s3_bucket_name}", "arn:aws:s3:::${var.loader_s3_bucket_name}/*" ]
  }
}

resource "aws_iam_role_policy" "beer_loader_role_policy" {
  name = "beers_s3_policy"
  role = "${aws_iam_role.beer_loader_role.id}"
  policy = "${data.aws_iam_policy_document.loader_s3_role_policy.json}"

}
