create_from_terraform:
	terraform init
	terraform apply -auto-approve -var-file=terraform.tfvars
destroy_from_terraform:
	terraform destroy -auto-approve

.PHONY: create_from_terraform destroy_from_terraform