# Set up the provider
provider "google" {
  project = var.project
  region  = var.region
  zone    = var.zone
}

# Define a Google Compute Engine instance for NiFi
resource "google_compute_instance" "nifi_instance" {
  name         = "nifi-vm"
  machine_type = "n1-standard-1"
  zone         = var.zone
  depends_on = [google_project_iam_member.nifi_service_account_iam]

  # Define the VM boot disk image
  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
    }
  }

  # Define the network interface and assign a public IP
  network_interface {
    network = "default"
    access_config {}
  }

  # Define instance metadata for startup script to install NiFi
  metadata_startup_script = <<-EOT
    #! /bin/bash
    # Update and install Java (NiFi dependency)
    sudo apt-get update
    sudo apt-get install -y openjdk-11-jdk
    # Download and extract NiFi
    curl -O https://downloads.apache.org/nifi/1.21.0/nifi-1.21.0-bin.tar.gz
    tar -xzvf nifi-1.21.0-bin.tar.gz
    # Start NiFi
    sudo nifi-1.21.0/bin/nifi.sh start
  EOT

  tags = ["nifi-server"]

  # Define service account with necessary permissions
  service_account {
    email  = google_service_account.nifi_service_account.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# Create a firewall rule to allow HTTP access to NiFi
resource "google_compute_firewall" "nifi_firewall" {
  name    = "nifi-allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags = ["nifi-server"]
}

# Create a service account for the NiFi VM
resource "google_service_account" "nifi_service_account" {
  account_id   = "nifi-sa"
  display_name = "NiFi Service Account"
}

resource "google_project_iam_member" "nifi_service_account_iam" {
  for_each = toset(var.roles)
  project = var.project
  role = each.value
  member = "serviceAccount:${google_service_account.nifi_service_account.email}"
}
resource "google_service_account_key" "gcp_tests" {
    service_account_id = google_service_account.nifi_service_account.name
}
