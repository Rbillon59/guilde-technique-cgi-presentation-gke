provider "google" {
  credentials = "${file("account.json")}"
  project     = "__GCP_PROJECT"
  region      = "europe-west2"
}

resource "google_container_cluster" "primary" {
  name                     = "gke-cgi-terraform"
  location                     = "europe-west2-a"
  remove_default_node_pool = true

}

resource "google_container_node_pool" "primary_pool" {
  name       = "primary-pool"
  cluster    = "${google_container_cluster.primary.name}"
  location       = "europe-west2-a"
  node_count = "1"

  node_config {
    machine_type = "n1-standard-1"
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 2
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}