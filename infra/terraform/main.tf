resource "aws_instance" "rag_mvp_impl" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  availability_zone      = var.availability_zone
  subnet_id              = var.subnet_id
  vpc_security_group_ids = var.security_group_ids
  key_name               = var.key_name
  iam_instance_profile   = var.iam_instance_profile

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = var.root_volume_type
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name   = var.instance_name
    NAME   = var.instance_name
    OWNER  = var.legacy_owner_tag
    CLASS0 = var.class0_tag
    CLASS1 = var.class1_tag
    owner  = var.owner_tag
  }
}
