variable "branch_name" {
}

provider "google" {
  project     = "__GCP_PROJECT"
  region      = "europe-west2"
}

resource "google_container_cluster" "primary" {
  name                      = var.branch_name
  location                     = "europe-west2-a"

  remove_default_node_pool = false


  node_pool {
    name = "default-pool"
    initial_node_count       = 2
  }
}