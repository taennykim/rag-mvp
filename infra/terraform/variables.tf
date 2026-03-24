variable "aws_region" {
  description = "AWS region for the implementation server"
  type        = string
  default     = "ap-northeast-2"
}

variable "instance_name" {
  description = "Name tag for the implementation EC2 instance"
  type        = string
  default     = "c1an2testadmin001_RAC"
}

variable "ami_id" {
  description = "AMI id copied from the reference instance"
  type        = string
  default     = "ami-09e1f7f5fee1f6d4a"
}

variable "instance_type" {
  description = "EC2 instance type copied from the reference instance"
  type        = string
  default     = "t2.micro"
}

variable "availability_zone" {
  description = "Availability zone copied from the reference instance"
  type        = string
  default     = "ap-northeast-2a"
}

variable "subnet_id" {
  description = "Subnet id copied from the reference instance"
  type        = string
  default     = "subnet-0e1132f0332a1c9d7"
}

variable "security_group_ids" {
  description = "Security groups copied from the reference instance"
  type        = list(string)
  default = [
    "sg-0e3f1efd64bb15288",
    "sg-071794595b7007c6e",
  ]
}

variable "key_name" {
  description = "EC2 key pair copied from the reference instance"
  type        = string
  default     = "p2an2test001"
}

variable "iam_instance_profile" {
  description = "IAM instance profile copied from the reference instance"
  type        = string
  default     = "terraform-poc-iac-role"
}

variable "root_volume_size" {
  description = "Root EBS volume size in GiB"
  type        = number
  default     = 50
}

variable "root_volume_type" {
  description = "Root EBS volume type copied from the reference instance"
  type        = string
  default     = "gp2"
}

variable "owner_tag" {
  description = "Owner tag required by AGENTS.md"
  type        = string
  default     = "taenny"
}

variable "legacy_owner_tag" {
  description = "Legacy OWNER tag copied from the reference instance"
  type        = string
  default     = "taenny.kim"
}

variable "class0_tag" {
  description = "Legacy CLASS0 tag copied from the reference instance"
  type        = string
  default     = "POC"
}

variable "class1_tag" {
  description = "Legacy CLASS1 tag copied from the reference instance"
  type        = string
  default     = "CL"
}
