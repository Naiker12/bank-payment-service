data "archive_file" "payment_service_zip" {
  type        = "zip"
  source_dir  = "../lambdas"
  output_path = "../lambdas/function.zip"
}
