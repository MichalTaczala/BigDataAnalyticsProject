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
  # metadata_startup_script = <<-EOT
  #   #! /bin/bash
  #   # Log start of the script
  #   mkdir logss
  #   echo "Starting script" > /logss/startup_script.log

  #   # Update and install Java (NiFi dependency)
  #   sudo apt-get update >> /logss/startup_script.log 2>&1
  #   sudo apt-get install -y openjdk-11-jdk unzip >> /logss/startup_script.log 2>&1

  #   # Create a test file to confirm script ran
  #   touch /logss/test1.txt >> /logss/startup_script.log 2>&1

  #   # Download and extract MiNiFi
  #   curl -O https://archive.apache.org/dist/nifi/1.27.0/nifi-1.27.0-bin.zip >> /logss/startup_script.log 2>&1
  #   unzip nifi-1.27.0-bin.zip >> /logss/startup_script.log 2>&1

  #   # Set JAVA_HOME
  #   export JAVA_HOME=$(readlink -f $(which java) | sed "s:bin/java::")
  #   echo "export JAVA_HOME=$(readlink -f $(which java) | sed 's:bin/java::')" >> ~/.bashrc
  #   source ~/.bashrc >> /logss/startup_script.log 2>&1

  #   # Permissions for MiNiFi directories
  #   sudo chmod -R u+w ~/nifi-1.27.0/logs ~/nifi-1.27.0/run >> /logss/startup_script.log 2>&1
  #   sudo chown -R $USER:$USER ~/nifi-1.27.0 >> /logss/startup_script.log 2>&1

  #   # Start MiNiFi
  #   cd /nifi-1.27.0
  #   sudo JAVA_HOME=$(readlink -f $(which java) | sed "s:bin/java::") ./bin/nifi.sh start >> /logss/startup_script.log 2>&1
  # EOT

  metadata_startup_script = <<-EOT
    sudo su
    apt upadate
    apt install -y openjdk-11-jdk unzip
    wget https://archive.apache.org/dist/nifi/1.27.0/nifi-1.27.0-bin.zip
    unzip nifi-1.27.0-bin.zip

    

    echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> /etc/profile.d/jdk.sh
    echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /etc/profile.d/jdk.sh
    source /etc/profile.d/jdk.sh

    cd nifi-1.27.0
    bin/nifi.sh start
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
  name    = "nifi-allow-all"
  network = "default"

  allow {
    protocol = "all"
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
