output "instance_id" {
  description = "Created EC2 instance id"
  value       = aws_instance.rag_mvp_impl.id
}

output "private_ip" {
  description = "Private IP address of the implementation instance"
  value       = aws_instance.rag_mvp_impl.private_ip
}

output "availability_zone" {
  description = "Availability zone of the implementation instance"
  value       = aws_instance.rag_mvp_impl.availability_zone
}

